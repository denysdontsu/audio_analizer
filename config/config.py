from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent

TOKEN_PATH = BASE_DIR / "token.json"
CREDENTIALS_PATH = BASE_DIR / "credentials.json"

SOURCE_FOLDER_ID = '1dpKG-eaFg2glOovkI4sYgLyPo3mW9Ilg'
TARGET_PARENT_ID = '1cQC4pqI8vcWs8FXHHSc-xm1FSr-UNzsM'

SCOPES = ["https://www.googleapis.com/auth/drive.metadata.readonly"]