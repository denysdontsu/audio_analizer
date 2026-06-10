import logging
from pathlib import Path

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


def create_name(audio_id: str, audio_name: str) -> str:
    """
    Builds a new name by inserting an audio_id before the file extension.
    The function splits the filename into:
        - base name (without extension)
        - file extension
    Then it constructs a new name in the format:
        {base_name}_{audio_id}{extension}

    Args:
        audio_id (str): Unique identifier for the audio.
        audio_name (str): Original filename (e.g., 'audio032.json').

    Returns:
        str: New filename with the audio_id appended before the extension.
    """
    path = Path(audio_name)
    return f"{path.stem}_{audio_id}{path.suffix}"