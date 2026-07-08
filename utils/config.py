"""Project configuration values."""

from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv


load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
OUTPUT_DIR = BASE_DIR / "output"
LOG_DIR = BASE_DIR / "logs"
DATABASE_PATH = DATA_DIR / "steam.db"

STEAM_COUNTRY = os.getenv("STEAM_COUNTRY", "us")
STEAM_LANGUAGE = os.getenv("STEAM_LANGUAGE", "english")
TOP_LIMIT = int(os.getenv("TOP_LIMIT", "100"))
REQUEST_TIMEOUT = float(os.getenv("REQUEST_TIMEOUT", "20"))
