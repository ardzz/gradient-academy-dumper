"""Configuration module for the scraper."""
import os
from pathlib import Path
from dotenv import load_dotenv

# Base configuration
BASE_DIR = Path(__file__).resolve().parent.parent

dotenv_path = BASE_DIR / '.env'
load_dotenv(dotenv_path=dotenv_path)

env_loaded = os.path.exists(dotenv_path)

DATA_DIR = BASE_DIR / "data"
DB_PATH = DATA_DIR / "gradient.db"

# API configuration
API_BASE_URL = os.environ.get("API_BASE_URL", "https://api.gradient.academy")
API_TOKEN = os.environ.get("GRADIENT_API_TOKEN", "")

# Download configuration
DOWNLOAD_PATH = Path(os.environ.get("DOWNLOAD_PATH", str(DATA_DIR / "downloads")))
FFMPEG_PATH = os.environ.get("FFMPEG_PATH", "ffmpeg")  # Default to system ffmpeg

# Concurrency settings
MAX_WORKERS = int(os.environ.get("MAX_WORKERS", 5))
RATE_LIMIT = int(os.environ.get("RATE_LIMIT", 2))  # requests per second

# Ensure data directory exists
DATA_DIR.mkdir(exist_ok=True)