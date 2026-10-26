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
    def create_zip_archive(session_id: str) -> Path:
        """Compacta todos os vídeos gerados em um arquivo .zip para download único."""
        output_dir = OUTPUT_DIR / session_id
        zip_base_name = output_dir.parent / f"remix_videos_{session_id}"
        zip_file = shutil.make_archive(str(zip_base_name), "zip", root_dir=output_dir)
        return Path(zip_file)
