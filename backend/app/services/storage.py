"""
Serviço de gerenciamento de arquivos de upload, sessões de usuário e limpeza.
"""
import shutil
import uuid
from pathlib import Path
from typing import Dict, List
from app.core.config import UPLOAD_DIR, OUTPUT_DIR, TEMP_DIR


class StorageService:
    """Gerencia pastas temporárias e persistência de sessões de processamento."""

    @staticmethod
    def create_session() -> str:
        """Cria um ID de sessão único para isolar arquivos do usuário."""
        session_id = str(uuid.uuid4())[:8]
        (UPLOAD_DIR / session_id).mkdir(parents=True, exist_ok=True)
        (OUTPUT_DIR / session_id).mkdir(parents=True, exist_ok=True)
        (TEMP_DIR / session_id).mkdir(parents=True, exist_ok=True)
        return session_id

    @staticmethod
    def get_session_paths(session_id: str) -> Dict[str, Path]:
        return {
            "upload": UPLOAD_DIR / session_id,
            "output": OUTPUT_DIR / session_id,
            "temp": TEMP_DIR / session_id,
        }

    @staticmethod
    def cleanup_temp(session_id: str) -> None:
        """Limpa arquivos temporários intermediários para liberar espaço em disco."""
        temp_dir = TEMP_DIR / session_id
        if temp_dir.exists():
            shutil.rmtree(temp_dir, ignore_errors=True)
            temp_dir.mkdir(parents=True, exist_ok=True)

    @staticmethod
    def purge_session(session_id: str) -> None:
        """
        Exclui permanentemente todos os arquivos vinculados à sessão:
        uploads originais, vídeos renderizados, arquivos temporários e arquivo zip.
        Garante custo zero de armazenamento e privacidade total para o usuário.
        """
        if not session_id or not session_id.isalnum():
            return

        for base_folder in [UPLOAD_DIR, OUTPUT_DIR, TEMP_DIR]:
            target_path = base_folder / session_id
            if target_path.exists():
                shutil.rmtree(target_path, ignore_errors=True)

        # Remove arquivo zip da sessão se existir
        zip_file = OUTPUT_DIR / f"remix_videos_{session_id}.zip"
        if zip_file.exists():
            try:
                zip_file.unlink()
            except Exception:
                pass

    @staticmethod
    def create_zip_archive(session_id: str) -> Path:
        """Compacta todos os vídeos gerados em um arquivo .zip para download único."""
        output_dir = OUTPUT_DIR / session_id
        zip_base_name = OUTPUT_DIR / f"remix_videos_{session_id}"
        zip_file = shutil.make_archive(str(zip_base_name), "zip", root_dir=output_dir)
        return Path(zip_file)
