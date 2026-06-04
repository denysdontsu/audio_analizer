import json
import logging

from config.config import BASE_DIR

logger = logging.getLogger(__name__)

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

    Note:
        Implemented as a defensive backup mechanism. Not yet integrated into
        the main pipeline. Planned as an additional deduplication layer to
        verify processed files independently of Google Sheets.
    """
    new_folder = BASE_DIR / 'output'
    new_folder.mkdir(parents=True, exist_ok=True)

    audio_name = audio_name.replace('.mp3', '.json')
    new_file_path = new_folder / f'{audio_name}'
    try:
        with open(new_file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=4, ensure_ascii=False)
    except OSError as e:
        logger.error(f'Failed to save chat report {audio_name}: {e}')
        raise