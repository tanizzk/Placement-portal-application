import os
from pathlib import Path

basedir = Path(__file__).resolve().parent

class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY", "dev-placement-secret")
    SQLALCHEMY_DATABASE_URI = (
        os.environ.get("DATABASE_URL")
        or f"sqlite:///{basedir / 'instance' / 'placement_portal.db'}"
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    ADMIN_EMAIL = os.environ.get("ADMIN_EMAIL", "admin@placement.local")
    ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD", "placement123")
    UPLOAD_FOLDER = str(basedir / "instance" / "resumes")
    MAX_CONTENT_LENGTH = 2 * 1024 * 1024
    ALLOWED_RESUME_EXTENSIONS = {"pdf", "doc", "docx"}
