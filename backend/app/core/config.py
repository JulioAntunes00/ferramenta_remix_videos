"""
Constantes globais e configurações de limites e regras de negócio.
Princípio Clean Code: Configurações centralizadas e de fácil modificação.
"""
from pathlib import Path

# Caminhos base
BASE_DIR = Path(__file__).resolve().parent.parent.parent
UPLOAD_DIR = BASE_DIR / "uploads"
OUTPUT_DIR = BASE_DIR / "outputs"
TEMP_DIR = BASE_DIR / "temp"

# Garantir existência dos diretórios
for directory in [UPLOAD_DIR, OUTPUT_DIR, TEMP_DIR]:
    directory.mkdir(parents=True, exist_ok=True)

# Categorias esperadas em ordem estrita de concatenação
VIDEO_CATEGORIES = ["hook", "body", "cta"]

# Limites de segurança inicial (Trava 4 x 4 x 4 = 64 vídeos)
MAX_VIDEOS_PER_CATEGORY = 4
MAX_TOTAL_COMBINATIONS = 64

# Proporção e especificações padrão para TikTok/Reels/Shorts
TARGET_WIDTH = 1080
TARGET_HEIGHT = 1920
TARGET_FPS = 30
