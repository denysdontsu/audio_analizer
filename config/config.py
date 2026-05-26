from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent

TOKEN_PATH = BASE_DIR / "token.json"
CREDENTIALS_PATH = BASE_DIR / "credentials.json"

SCOPES = ["https://www.googleapis.com/auth/drive.metadata.readonly"]