"""
Motor de Processamento de Vídeo com FFmpeg.
Implementa padronização, concatenação e sanitização Anti-Ban (remoção de metadados).
"""
import json
import logging
import os
import shutil
import subprocess
from pathlib import Path
from typing import List, Optional

logger = logging.getLogger(__name__)


class VideoEngine:
    """Serviço sênior responsável pelo encapsulamento de operações FFmpeg."""

    def __init__(self, ffmpeg_bin: Optional[str] = None, ffprobe_bin: Optional[str] = None):
        self.ffmpeg_bin = ffmpeg_bin or self._find_binary("ffmpeg")
        self.ffprobe_bin = ffprobe_bin or self._find_binary("ffprobe")

    @staticmethod
    def _find_binary(name: str) -> str:
        found = shutil.which(name)
        if found:
            return found
        # Possíveis caminhos do winget ou locais no Windows
        local_app_data = os.environ.get("LOCALAPPDATA", "")
        possible_paths = [
            Path(local_app_data) / "Microsoft" / "WinGet" / "Packages",
            Path("C:/Program Files/ffmpeg/bin"),
            Path("C:/ffmpeg/bin"),
        ]
        for p in possible_paths:
            if p.exists():
                matches = list(p.glob(f"**/{name}.exe"))
                if matches:
                    return str(matches[0])
        return name

    def get_duration(self, video_path: Path) -> float:
        """Obtém a duração exata do clipe em segundos usando ffprobe."""
        try:
            cmd = [
                self.ffprobe_bin,
                "-v", "error",
                "-show_entries", "format=duration",
                "-of", "default=noprint_wrappers=1:nokey=1",
                str(video_path),
            ]
            result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, check=True)
            return float(result.stdout.strip())
        except Exception as e:
            logger.warning(f"Não foi possível obter duração de {video_path}: {e}")
            return 5.0  # Fallback seguro

    def normalize_clip(self, input_path: Path, output_path: Path, target_w: int = 1080, target_h: int = 1920) -> None:
        """
        Padroniza um clipe individual para resolução e framerate uniforme (1080x1920 @ 30fps),
        com normalização de áudio (loudnorm) para que os clipes em volumes diferentes fiquem nivelados.
        """
        # Filtro de vídeo com aspect ratio preservado e padding preto se necessário
        video_filter = (
            f"scale={target_w}:{target_h}:force_original_aspect_ratio=decrease,"
            f"pad={target_w}:{target_h}:(ow-iw)/2:(oh-ih)/2,setsar=1,fps=30"
        )
        audio_filter = "loudnorm=I=-16:TP=-1.5:LRA=11"

        cmd = [
            self.ffmpeg_bin,
            "-y",
            "-i", str(input_path),
            "-vf", video_filter,
            "-af", audio_filter,
            "-c:v", "libx264",
            "-preset", "veryfast",
            "-crf", "22",
            "-c:a", "aac",
            "-b:a", "192k",
            str(output_path),
        ]
        subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)

    def concatenate_and_sanitize(
        self,
        clip_paths: List[Path],
        output_path: Path,
        session_temp_dir: Path
    ) -> None:
        """
        Concatena os clipes na ordem especificada e aplica sanitização Anti-Ban:
        1. Remove todos os metadados de gravação original (-map_metadata -1).
        2. Injeta novos metadados neutros e limpos.
        3. Recria timestamps de apresentação (PTS) contínuos para evitar flags de arquivo recortado.
        """
        concat_list_file = session_temp_dir / f"concat_{output_path.stem}.txt"
        with open(concat_list_file, "w", encoding="utf-8") as f:
            for clip in clip_paths:
                # FFmpeg concat demuxer requer caminhos com barra invertida ou escapados
                safe_clip_path = str(clip).replace("\\", "/")
                f.write(f"file '{safe_clip_path}'\n")

        # Concatenação e Sanitização Anti-Ban
        cmd = [
            self.ffmpeg_bin,
            "-y",
            "-f", "concat",
            "-safe", "0",
            "-i", str(concat_list_file),
            "-c:v", "libx264",
            "-preset", "veryfast",
            "-crf", "22",
            "-c:a", "aac",
            "-b:a", "192k",
            # ANTI-BAN: Remove metadados do fabricante, câmera, GPS, etc.
            "-map_metadata", "-1",
            "-metadata", "title=Creative Remix",
            "-metadata", "comment=Optimized Media",
            "-movflags", "+faststart",
            str(output_path),
        ]

        try:
            subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
        finally:
            if concat_list_file.exists():
                concat_list_file.unlink()
