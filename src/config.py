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

# Rclone configuration
RCLONE_PATH = os.environ.get("RCLONE_PATH", "rclone")  # Default to system rclone
RCLONE_REMOTE = os.environ.get("RCLONE_REMOTE", "gdrive:")  # Default remote name
RCLONE_DEST_DIR = os.environ.get("RCLONE_DEST_DIR", "GradientAcademy")  # Default destination folder
RCLONE_ENABLED = os.environ.get("RCLONE_ENABLED", "False").lower() in ("true", "1", "yes")
DELETE_AFTER_UPLOAD = os.environ.get("DELETE_AFTER_UPLOAD", "False").lower() in ("true", "1", "yes")

# Concurrency settings
MAX_WORKERS = int(os.environ.get("MAX_WORKERS", 5))
RATE_LIMIT = int(os.environ.get("RATE_LIMIT", 2))  # requests per second

# Ensure data directory exists
DATA_DIR.mkdir(exist_ok=True)