import json

from config.config import BASE_DIR


def parse_audio_filename(filename: str) -> dict | None:
    """
    Parses an audio filename into its components.

    Expected format:
        DATE_TIME_PHONE_NUMBER_CALL_TYPE

    Args:
        filename (str): Filename separated by underscores ("_").

    Returns:
        dict | None: A dictionary containing the parsed values:
            {
                'data_time': str,
                'number': str,
                'call_type': str
            }
    Returns None if the filename format is invalid.
    """
    fields = filename.split('_')
    if len(fields) == 4:
        date = fields[0]
        time = fields[1].replace('-', ':')
        parsed_name = {
            'date_time': f'{date} {time}',
            'number': fields[2],
            'call_type': fields[3].replace('.mp3', '')
        }
        return parsed_name
    return None


def save_chat_report(audio_name: str, data: dict):
    """
    Saves the chat analysis report as a JSON file.
    The function creates an `output` directory inside BASE_DIR if it does not exist,
    converts the audio filename from `.mp3` to `.json`, and writes the provided
    dictionary data into a JSON file.

    Args:
        audio_name (str): Original audio filename (expected to end with `.mp3`).
        data (dict): Dictionary containing chat/report data to be saved.
    """
    new_folder = BASE_DIR / 'output'
    new_folder.mkdir(parents=True, exist_ok=True)

    audio_name = audio_name.replace('.mp3', '.json')
    new_file_path = new_folder / f'{audio_name}'

    with open(new_file_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ident=4, ensure_ascii=False)


def build_row(
        filename: str,
        char_report: dict,
        transcription: str,
        manager_score: float
) -> list:
    """
    Builds a structured row for insertion into a Google Sheets table.

    The function combines data from the parsed audio filename, chat report,
    transcription text, and manager evaluation score into a single ordered list.
    This row is intended to match a predefined spreadsheet schema.

    Args:
        filename (str): Audio filename.
        char_report (dict): Analysis report containing structured call metrics
            (e.g., manager_name, greeting, car details, outcomes, etc.).
        transcription (str): Full transcription of the conversation.
        manager_score (float): Final evaluation score assigned to the manager.

    Returns:
        list: Ordered list representing a single row for Google Sheets insertion.
    """
    parsed_f = parse_audio_filename(filename)
    if not parsed_f:
        parsed_f = {}

    report = char_report or {}

    row = [
        filename,
        parsed_f.get('date_time', ''),
        parsed_f.get('call_type', ''),
        '',  # No data for the column 'Тип звернення'
        parsed_f.get('number', ''),
        '',  # No data for the column 'Філія'
        report.get('manager_name', 'Не представився'),
        transcription or '',
        report.get('greeting', ''),
        report.get('car_body', ''),
        report.get('car_year', ''),
        report.get('mileage', ''),
        report.get('diagnostics_offer', ''),
        report.get('previous_work', ''),
        report.get('appointment_made', ''),
        report.get('farewell', ''),
        report.get('work_types', 'Інший варіант'),
        '',  # No data for the column 'Чи дотримувався всіх інструкцій з топ 100 робіт Да/Ні'
        '',  # No data for the column 'Яких рекоменадцій менеджер не дотримувався з топ 100 робіт'
        report.get('result_type', ''),
        manager_score if manager_score is not None else 0.0,
        report.get('spare_parts', ''),
        report.get('comments', '')
    ]

    return row