"""
Endpoints REST da aplicação FastAPI.
Princípio Clean Code: Handlers limpos, validação via Pydantic e orquestração de serviços.
"""
import itertools
import threading
from pathlib import Path
from typing import Dict, List, Any
from fastapi import APIRouter, File, Form, HTTPException, UploadFile, BackgroundTasks
from fastapi.responses import FileResponse

from app.core.config import MAX_VIDEOS_PER_CATEGORY, MAX_TOTAL_COMBINATIONS
from app.services.storage import StorageService
from app.services.similarity import SimilarityEvaluator
from app.services.video_engine import VideoEngine

router = APIRouter()
video_engine = VideoEngine()

# Estado em memória para rastreamento de progresso de renderização
# (Padrão para ambiente local, facilmente substituível por Redis em produção)
job_status: Dict[str, Dict[str, Any]] = {}


@router.post("/session/create")
def create_session():
    """Inicia uma nova sessão de upload e processamento."""
    session_id = StorageService.create_session()
    job_status[session_id] = {
        "status": "idle",
        "progress": 0,
        "total": 0,
        "completed": 0,
        "results": [],
    }
    return {"session_id": session_id}


@router.post("/session/purge/{session_id}")
def purge_session(session_id: str):
    """
    Exclui imediatamente todos os arquivos e vídeos do disco ao atualizar ou sair da página.
    Evita acúmulo de arquivos e garante limpeza contínua.
    """
    StorageService.purge_session(session_id)
    if session_id in job_status:
        del job_status[session_id]
    return {"message": "Sessão e arquivos apagados com sucesso."}


ALLOWED_EXTENSIONS = {".mp4", ".mov", ".m4v"}
MAX_FILE_SIZE = 100 * 1024 * 1024  # 100 MB por clipe


def _validate_video_header(chunk: bytes) -> bool:
    """
    Validação de Assinatura Binária (Magic Bytes):
    Garante que o arquivo enviado é realmente um arquivo MP4/MOV legítimo,
    evitando que scripts maliciosos (PHP, shell, executáveis) sejam mascarados.
    """
    if len(chunk) < 12:
        return False
    # Arquivos MP4 / MOV / QuickTime possuem 'ftyp', 'moov', ou 'mdat' nos primeiros bytes
    box_type = chunk[4:8]
    return box_type in [b"ftyp", b"moov", b"mdat", b"wide", b"skip"]


@router.post("/upload/{session_id}")
async def upload_clip(
    session_id: str,
    category: str = Form(...),
    file: UploadFile = File(...)
):
    """
    Recebe um vídeo com validação estrita de segurança:
    1. Sanitização do session_id contra Path Traversal
    2. Validação da categoria
    3. Validação de extensão
    4. Validação binária (Magic Bytes de vídeo)
    5. Limite de tamanho de arquivo
    """
    # 1. Proteção Path Traversal
    if not session_id.isalnum() or len(session_id) > 16:
        raise HTTPException(status_code=400, detail="ID de sessão inválido.")

    if category not in ["hook", "body", "cta"]:
        raise HTTPException(status_code=400, detail="Categoria inválida. Use: hook, body ou cta.")

    # 2. Validação de extensão
    file_ext = Path(file.filename or "video.mp4").suffix.lower()
    if file_ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"Formato não suportado: {file_ext}. Envie apenas vídeos MP4 ou MOV."
        )

    paths = StorageService.get_session_paths(session_id)
    cat_dir = paths["upload"] / category
    cat_dir.mkdir(parents=True, exist_ok=True)

    existing_files = list(cat_dir.glob("*.mp4")) + list(cat_dir.glob("*.mov"))
    if len(existing_files) >= MAX_VIDEOS_PER_CATEGORY:
        raise HTTPException(
            status_code=400,
            detail=f"Limite de {MAX_VIDEOS_PER_CATEGORY} vídeos por categoria atingido para esta versão."
        )

    # 3. Leitura e Validação Binária
    content = await file.read()
    if len(content) > MAX_FILE_SIZE:
        raise HTTPException(status_code=400, detail="Arquivo excede o limite máximo permitido de 100MB.")

    if not _validate_video_header(content[:32]):
        raise HTTPException(
            status_code=400,
            detail="Arquivo inválido ou corrompido. O arquivo não possui assinatura de vídeo válida."
        )

    # 4. Gravação com nome estritamente sanitizado e determinístico
    safe_filename = f"{category}_{len(existing_files) + 1}{file_ext}"
    dest_path = cat_dir / safe_filename

    with open(dest_path, "wb") as f:
        f.write(content)

    # Inspeciona orientação e resolução para feedback de UI
    video_info = video_engine.get_video_info(dest_path)

    return {
        "filename": safe_filename,
        "category": category,
        "total_in_category": len(existing_files) + 1,
        "orientation": video_info["orientation"],
        "is_horizontal": video_info["is_horizontal"],
        "resolution": f"{video_info['width']}x{video_info['height']}",
        "duration": round(video_info["duration"], 1),
    }


@router.delete("/upload/{session_id}/{category}/{filename}")
def delete_clip(session_id: str, category: str, filename: str):
    """
    Remove um vídeo previamente enviado antes de renderizar.
    Permite ao usuário descartar clipes que não queira mais na combinação.
    """
    if not session_id.isalnum() or category not in ["hook", "body", "cta"]:
        raise HTTPException(status_code=400, detail="Parâmetros inválidos.")

    paths = StorageService.get_session_paths(session_id)
    target_file = paths["upload"] / category / filename
    if target_file.exists():
        target_file.unlink()
        return {"message": "Arquivo removido com sucesso.", "filename": filename}
    raise HTTPException(status_code=404, detail="Arquivo não encontrado.")


@router.get("/preview/{session_id}")
def preview_combinations(session_id: str):
    """
    Calcula as combinações possíveis e o score de similaridade anti-ban
    antes de renderizar os vídeos.
    """
    paths = StorageService.get_session_paths(session_id)
    hooks = sorted([f.name for f in (paths["upload"] / "hook").glob("*.*")])
    bodies = sorted([f.name for f in (paths["upload"] / "body").glob("*.*")])
    ctas = sorted([f.name for f in (paths["upload"] / "cta").glob("*.*")])

    total_combinations = len(hooks) * len(bodies) * len(ctas)
    if total_combinations > MAX_TOTAL_COMBINATIONS:
        raise HTTPException(
            status_code=400,
            detail=f"Combinações ({total_combinations}) excedem a trava de segurança ({MAX_TOTAL_COMBINATIONS})."
        )

    durations: Dict[str, float] = {}
    for cat, files in [("hook", hooks), ("body", bodies), ("cta", ctas)]:
        for f in files:
            file_path = paths["upload"] / cat / f
            durations[f] = video_engine.get_duration(file_path)

    raw_combinations = []
    combo_id = 1
    for h, b, c in itertools.product(hooks, bodies, ctas):
        raw_combinations.append({
            "id": f"v_{combo_id:03d}",
            "hook": h,
            "body": b,
            "cta": c,
            "output_name": f"remix_{combo_id:03d}.mp4",
        })
        combo_id += 1

    scored_combinations = SimilarityEvaluator.evaluate_combinations(raw_combinations, durations)

    summary = {
        "total_hooks": len(hooks),
        "total_bodies": len(bodies),
        "total_ctas": len(ctas),
        "total_combinations": total_combinations,
        "combinations": scored_combinations,
    }
    return summary


def _process_videos_task(session_id: str, combinations: List[Dict[str, Any]]):
    """Worker de execução de renderização assíncrona com sanitização de metadados."""
    paths = StorageService.get_session_paths(session_id)
    total = len(combinations)
    job = job_status.setdefault(session_id, {})
    job["status"] = "processing"
    job["total"] = total
    job["completed"] = 0
    job["results"] = []

    # 1. Normalizar clipes de entrada para pasta temp
    normalized_cache: Dict[str, Path] = {}
    temp_dir = paths["temp"]

    try:
        for item in combinations:
            for cat, fname in [("hook", item["hook"]), ("body", item["body"]), ("cta", item["cta"])]:
                if fname not in normalized_cache:
                    raw_path = paths["upload"] / cat / fname
                    norm_path = temp_dir / f"norm_{fname}.mp4"
                    video_engine.normalize_clip(raw_path, norm_path)
                    normalized_cache[fname] = norm_path

        # 2. Concatenação e Sanitização Anti-Ban
        for idx, item in enumerate(combinations):
            out_filename = f"remix_{idx + 1:03d}_{item['score_badge']}.mp4"
            final_out_path = paths["output"] / out_filename

            clips_to_concat = [
                normalized_cache[item["hook"]],
                normalized_cache[item["body"]],
                normalized_cache[item["cta"]],
            ]

            video_engine.concatenate_and_sanitize(clips_to_concat, final_out_path, temp_dir)

            job["completed"] = idx + 1
            job["progress"] = int(((idx + 1) / total) * 100)
            job["results"].append({
                **item,
                "file_name": out_filename,
                "file_url": f"/api/video/{session_id}/{out_filename}",
            })

        job["status"] = "completed"
    except Exception as e:
        job["status"] = "error"
        job["error_message"] = str(e)
    finally:
        StorageService.cleanup_temp(session_id)


@router.post("/render/{session_id}")
def start_render(session_id: str, background_tasks: BackgroundTasks):
    """Dispara a esteira de renderização e anti-ban em segundo plano."""
    preview = preview_combinations(session_id)
    combinations = preview["combinations"]
    if not combinations:
        raise HTTPException(status_code=400, detail="Nenhuma combinação para renderizar. Envie os vídeos primeiro.")

    background_tasks.add_task(_process_videos_task, session_id, combinations)
    return {"message": "Renderização iniciada com sucesso.", "total": len(combinations)}


@router.get("/status/{session_id}")
def get_render_status(session_id: str):
    """Consulta o progresso em tempo real da renderização."""
    status = job_status.get(session_id)
    if not status:
        raise HTTPException(status_code=404, detail="Sessão não encontrada.")
    return status


@router.get("/video/{session_id}/{filename}")
def stream_video(session_id: str, filename: str):
    """Permite baixar diretamente ou visualizar o vídeo gerado na interface."""
    paths = StorageService.get_session_paths(session_id)
    file_path = paths["output"] / filename
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="Vídeo não encontrado.")
    return FileResponse(
        file_path, 
        media_type="video/mp4",
        filename=filename,
        headers={"Content-Disposition": f'attachment; filename="{filename}"'}
    )


@router.get("/download-zip/{session_id}")
def download_zip(session_id: str):
    """Gera e faz o download de todos os vídeos combinados em um arquivo .zip."""
    zip_path = StorageService.create_zip_archive(session_id)
    if not zip_path.exists():
        raise HTTPException(status_code=404, detail="Arquivo zip não encontrado.")
    return FileResponse(
        zip_path,
        media_type="application/zip",
        filename=f"lote_multiplicador_tiktok_{session_id}.zip",
        headers={"Content-Disposition": f'attachment; filename="lote_multiplicador_tiktok_{session_id}.zip"'}
    )
