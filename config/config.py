from pathlib import Path

# Base paths
BASE_DIR = Path(__file__).resolve().parent.parent
CONFIG_DIR = BASE_DIR / 'config'
TOKEN_PATH = CONFIG_DIR / 'token.json'
CREDENTIALS_PATH = CONFIG_DIR / 'credentials.json'
LOG_PATH = BASE_DIR / 'log' / 'parser.log'
OUTPUT_DIR = BASE_DIR / 'output'

# Google API scopes
SCOPES = [
    "https://www.googleapis.com/auth/drive",
    "https://www.googleapis.com/auth/spreadsheets"
]

# Source Google Drive resources
# SOURCE_FOLDER_ID = '1dpKG-eaFg2glOovkI4sYgLyPo3mW9Ilg'
SOURCE_FOLDER_ID = '15nuQ2GHNE4bK4AfaSTNeyAs0wIgGDUn3'
SOURCE_SHEET_ID = '17rTXeHpZWbsj7ChYpXE3sxdlBUTSaGH9FJIJzs7tZdk'

# Target Google Drive resources
TARGET_PARENT_ID = '1cQC4pqI8vcWs8FXHHSc-xm1FSr-UNzsM'
TARGET_SHEET_NAME = 'Звіт прослуханих розмов'
TARGET_AUDIO_FOLDER_NAME = 'Дзвінки'

# Whisper configuration
WHISPER_MODEL = 'turbo'
WHISPER_PROMPT = "Розмова менеджера автосервісу з клієнтом щодо консультації, ремонту або діагностики автомобіля."
ALLOWED_LANGUAGES = ('uk', 'ru')

# OpenAI configuration
OPENAI_MODEL = "gpt-4o-mini"

# Google sheets column schema
SHEETS_DATA_RANGE = 'Лист1!A3:A'
SHEETS_COLUMNS_SCHEMA = [
    'audio_id',               # Google Drive file ID
    'audio_link',             # Link to the copied audio
    'date_time',              # Call date and time
    'call_type',              # Call type (inbound/outbound)
    'appeal_type',            # Type of appeal (currently empty)
    'number',                 # Client's phone number
    'branch',                 # Branch / Location (currently empty)
    'manager_name',           # Manager's name
    'transcription',          # Full transcription text
    'greeting',               # Greeting check / compliance
    'car_body',               # Car body type
    'car_year',               # Car manufacturing year
    'mileage',                # Car mileage
    'diagnostics_offer',      # Diagnostics offer check
    'previous_work',          # Previous work history / context
    'appointment_made',       # Whether an appointment was scheduled (Yes/No)
    'farewell',               # Farewell check / compliance
    'work_types',             # Types of work requested
    'followed_top_100',       # Followed all top 100 instructions check (currently empty)
    'failed_top_100_recoms',  # Top 100 recommendations missed by manager (currently empty)
    'result_type',            # Call outcome / result type
    'manager_score',          # Manager evaluation score (float)
    'spare_parts',            # Spare parts discussed
    'comments'                # Analyst or model comments
]

# Available work types and dialogue outcomes for dialogue analysis
WORKS = [
    'Інший варіант',
    'Комплексне ТО',
    'Компʼютерна діагностика',
    'Заміна оливи ДВЗ',
    'Заміна повітряного фільтра ДВЗ',
    'Заміна сайлентблоків',
    'Слюсарні роботи',
    'Комплексна діагностика',
    'Заміна фільтра салону',
    'Заміна масла в АКПП',
    'Заміна амортизатора переднього',
    'Ендоскопія двигуна',
    'Заміна свічок запалення',
    'Заміна гальмівних дисків та колодок',
    'Заміна оливи в передньому / задньому редукторі',
    'Заміна гальмівної рідини з прокачкою',
    'Заміна лампочки',
    'Заміна паливного фільтра (дизель)',
    'Зняття / встановлення важеля переднього',
    'Замір компресії',
    'Заміна та замовлення гальмівних колодок',
    'Заміна охолоджуючої рідини',
    'Заміна стійки стабілізатора переднього',
    'Заміна амортизатора заднього',
    'Заміна плаваючого сайлентблока',
    'Заміна гальмівних дисків та колодок задніх',
    'Заміна фільтра салону в моторному відділенні',
    'Зняття / встановлення паливних форсунок',
    'Заміна пильовика амортизатора',
    'Арматурні роботи',
    'Заміна свічок накалу',
    'Заміна ланцюгів ГРМ',
    'Зняття / встановлення впускного колектора',
    'Димогенератор, пошук підсосів / витоку',
    'Реєстрація заміни АКБ',
    'Заміна АКБ',
    'Заміна свічок запалення N55',
    'Заміна еластичної муфти',
    'Ремонт електропроводки',
    'Заміна ланцюга ГРМ та масляного насоса N20',
    'Заміна ремкомплекту рейки',
    'Заміна подушки ДВЗ',
    'Зняття / встановлення піввісі',
    'Заміна подушки АКПП',
    'Зняття / встановлення теплообмінника',
    'Зняття / встановлення маслостакана',
    'Заміна пружини',
    'Зняття / встановлення дверної карти',
    'Мийка / чистка деталі',
    'Зняття, встановлення турбокомпресора',
    'Заміна помпи',
    'Заміна 3-х сайлентблоків редуктора',
    'Заміна термостата',
    'Зняття / встановлення захисту двигуна',
    'Заміна прокладки маслостакана',
    'Заміна патрубка ОР',
    'Заміна приводного ременя',
    'Діагностика ДВЗ',
    'Зняття / встановлення кардана',
    'Заміна прокладки картера (піддона)',
    'Заміна КВКГ',
    'Заміна втулки стабілізатора переднього',
    'Заміна бачка охолоджуючої рідини',
    'Промивка системи охолодження',
    'Тестер витоку охолоджуючої рідини',
    'Зняття / встановлення вихлопної труби',
    'Заміна пильовика ШРУСа',
    'Діагностика течії',
    'Зняття / встановлення переднього бампера',
    'Заміна датчика',
    'Заміна переднього сальника колінвала',
    'Заміна рульової тяги',
    'Зняття / встановлення деталі',
    'Заміна котушки запалювання',
    'Заміна підшипника маточини',
    'Заміна кульової опори',
    'Зняття / встановлення інтеркулера',
    'Розбірка / збірка гальмівного супорта',
    'Заміна рульової тяги з наконечником',
    'Зняття / встановлення впускного колектора M57',
    'Зняття / встановлення дверної ручки',
    'Зняття / встановлення повітряного патрубка',
    'Заміна клапана Vanos',
    'Заміна радіатора охолодження',
    'Заміна заднього сальника колінвала та ремкомплекту 8HP',
    'Заміна датчика кисню (лямбда-зонда)',
    'Заміна фланця роздавальної коробки',
    'Протікання води в салон через гідроізоляцію дверних карт'
]

RESULT_OF_DIALOGUE = [
    'Запис',
    'Повторна консультація',
    'Передано іншому філалу',
    'Передзвонити',
    'Іншe'
]