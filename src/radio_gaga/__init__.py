import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv(dotenv_path=Path(__file__).resolve().parents[2] / ".env")

PROJECT_ROOT = Path(__file__).resolve().parents[2]

PROMPT_FOLDER = Path(__file__).resolve().parent / "resources" / "prompts"

_SESSION_FILE = os.getenv("RADIO_GAGA_SESSION_FILE") or ".radio_gaga_session.json"

DEFAULT_SESSION_FILE = PROJECT_ROOT / _SESSION_FILE
