"""
Motor de Processamento de Vídeo com FFmpeg.
Implementa padronização inteligente (com fundo desfocado/blurred background para vídeos horizontais),
normalização de áudio (loudnorm), e sanitização Anti-Ban (remoção de metadados).
"""
import json
import logging
import os
import shutil
import subprocess
from pathlib import Path
from typing import Dict, List, Optional, Tuple

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

    def get_video_info(self, video_path: Path) -> Dict[str, any]:
        """
        Obtém duração, largura, altura e orientação do vídeo via ffprobe.
        """
        try:
            cmd = [
                self.ffprobe_bin,
                "-v", "error",
                "-select_streams", "v:0",
                "-show_entries", "stream=width,height,duration:format=duration",
                "-of", "json",
                str(video_path),
            ]
            result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, check=True)
            data = json.loads(result.stdout)
            
            stream = data.get("streams", [{}])[0]
            fmt = data.get("format", {})

            width = int(stream.get("width", 1080))
            height = int(stream.get("height", 1920))
            
            # Prioriza a duração do stream ou do format
            raw_duration = stream.get("duration") or fmt.get("duration") or 5.0
            duration = float(raw_duration)

            is_horizontal = width > height

            return {
                "width": width,
                "height": height,
                "duration": duration,
                "is_horizontal": is_horizontal,
                "orientation": "horizontal" if is_horizontal else "vertical",
            }
        except Exception as e:
            logger.warning(f"Erro ao obter metadados de {video_path}: {e}")
            return {
                "width": 1080,
                "height": 1920,
                "duration": 5.0,
                "is_horizontal": False,
                "orientation": "vertical",
            }

    def get_duration(self, video_path: Path) -> float:
        """Obtém apenas a duração em segundos."""
        return self.get_video_info(video_path)["duration"]

    def normalize_clip(
        self,
        input_path: Path,
        output_path: Path,
        target_w: int = 1080,
        target_h: int = 1920,
        use_blurred_background: bool = True
    ) -> None:
        """
        Padroniza um clipe individual para resolução e framerate uniforme (1080x1920 @ 30fps).
        
        Tratamento Profissional de Vídeos Horizontais:
        - Se o vídeo for horizontal (16:9 ou similar) e use_blurred_background=True:
          O sistema duplica o vídeo, aplica um blur cinematográfico no fundo em 1080x1920,
          e sobrepõe o vídeo nítido centralizado com aspect ratio preservado.
        - Se o vídeo já for vertical (9:16), ele é escalado perfeitamente.
        - O áudio é normalizado com loudnorm (-16 LUFS) para volume homogêneo.
        """
        info = self.get_video_info(input_path)
        audio_filter = "loudnorm=I=-16:TP=-1.5:LRA=11"

        if info["is_horizontal"] and use_blurred_background:
            # Filtro profissional complexo:
            # [0:v] split em dois fluxos [bg] e [fg]
            # [bg]: escalado para cobrir 1080x1920 com crop e desfoque gaussiano
            # [fg]: escalado proporcionalmente para caber na largura sem cortar
            # overlay: sobrepõe o vídeo nítido no centro do fundo desfocado
            filter_complex = (
                f"[0:v]split=2[bg_in][fg_in];"
                f"[bg_in]scale={target_w}:{target_h}:force_original_aspect_ratio=increase,"
                f"crop={target_w}:{target_h},boxblur=25:5,setsar=1,fps=30[bg];"
                f"[fg_in]scale={target_w}:-2:force_original_aspect_ratio=decrease,setsar=1,fps=30[fg];"
                f"[bg][fg]overlay=(W-w)/2:(H-h)/2[outv]"
            )
            cmd = [
                self.ffmpeg_bin,
                "-y",
                "-i", str(input_path),
                "-filter_complex", filter_complex,
                "-map", "[outv]",
                "-map", "0:a?",
                "-af", audio_filter,
                "-c:v", "libx264",
                "-preset", "veryfast",
                "-crf", "22",
                "-c:a", "aac",
                "-b:a", "192k",
                str(output_path),
            ]
        else:
            # Vídeo vertical padrão ou letterbox limpo
            video_filter = (
                f"scale={target_w}:{target_h}:force_original_aspect_ratio=decrease,"
                f"pad={target_w}:{target_h}:(ow-iw)/2:(oh-ih)/2,setsar=1,fps=30"
            )
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
                safe_clip_path = str(clip).replace("\\", "/")
                f.write(f"file '{safe_clip_path}'\n")

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
