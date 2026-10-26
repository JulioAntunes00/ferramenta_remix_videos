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


@router.post("/upload/{session_id}")
async def upload_clip(
    session_id: str,
    category: str = Form(...),
    file: UploadFile = File(...)
):
    """
    Recebe um vídeo de uma categoria específica (hook, body ou cta).
    Valida limites de segurança (max 4 por categoria).
    """
    if category not in ["hook", "body", "cta"]:
        raise HTTPException(status_code=400, detail="Categoria inválida. Use: hook, body ou cta.")

    paths = StorageService.get_session_paths(session_id)
    cat_dir = paths["upload"] / category
    cat_dir.mkdir(parents=True, exist_ok=True)

    existing_files = list(cat_dir.glob("*.mp4")) + list(cat_dir.glob("*.mov"))
    if len(existing_files) >= MAX_VIDEOS_PER_CATEGORY:
        raise HTTPException(
            status_code=400,
            detail=f"Limite de {MAX_VIDEOS_PER_CATEGORY} vídeos por categoria atingido para esta versão."
        )

    # Salva arquivo com nome limpo
    file_ext = Path(file.filename or "video.mp4").suffix.lower() or ".mp4"
    safe_filename = f"{category}_{len(existing_files) + 1}{file_ext}"
    dest_path = cat_dir / safe_filename

    with open(dest_path, "wb") as f:
        content = await file.read()
        f.write(content)

    return {
        "filename": safe_filename,
        "category": category,
        "total_in_category": len(existing_files) + 1,
    }


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
    """Permite visualizar/reproduzir o vídeo gerado na interface."""
    paths = StorageService.get_session_paths(session_id)
    file_path = paths["output"] / filename
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="Vídeo não encontrado.")
    return FileResponse(file_path, media_type="video/mp4")


@router.get("/download-zip/{session_id}")
def download_zip(session_id: str):
    """Gera e faz o download de todos os vídeos combinados em um arquivo .zip."""
    zip_path = StorageService.create_zip_archive(session_id)
    if not zip_path.exists():
        raise HTTPException(status_code=404, detail="Arquivo zip não encontrado.")
    return FileResponse(
        zip_path,
        media_type="application/zip",
        filename=f"lote_remix_videos_{session_id}.zip"
    )
