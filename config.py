import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent

class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY", "dev-only-change-this-secret")
    MAX_CONTENT_LENGTH = 20 * 1024 * 1024
    UPLOAD_FOLDER = str(BASE_DIR / "uploads")
    INSTANCE_FOLDER = str(BASE_DIR / "instance")
    DATABASE = str(BASE_DIR / "instance" / "college_notes.db")
