from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent

TOKEN_PATH = BASE_DIR / "token.json"
CREDENTIALS_PATH = BASE_DIR / "credentials.json"

SOURCE_FOLDER_ID = '1dpKG-eaFg2glOovkI4sYgLyPo3mW9Ilg'
SOURCE_SHEET_ID = '16I6nqmaD-AjkKF7sQWWQPRn0xnVdS9HBbwBFTe-_y0U'
TARGET_PARENT_ID = '1cQC4pqI8vcWs8FXHHSc-xm1FSr-UNzsM'

SCOPES = ["https://www.googleapis.com/auth/drive.metadata.readonly"]

WHISPER_MODEL = 'small'
WHISPER_PROMPT = "Розмова менеджера автосервісу з клієнтом щодо консультації, ремонту або діагностики автомобіля."