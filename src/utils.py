import json
import logging
from pathlib import Path
from typing import Any

from config.config import OUTPUT_DIR

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


def save_report(
        data: dict,
):
    """
    Saves the flat chat analysis data as a JSON file for caching and deduplication.

    The function names the file using the unique Google Drive audio ID, adds a `.json`
    extension, and writes the structured dictionary data into the output directory.

    Args:
        data (dict): The flat dictionary containing all gathered analysis fields
            (the `raw_data` returned by `build_row`).

    Raises:
        OSError: If writing the JSON file to disk fails.
    """
    new_file_path = OUTPUT_DIR / f"{data['audio_id']}.json"
    try:
        with open(new_file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=4, ensure_ascii=False)

    except OSError as e:
        logger.error(f"Failed to save report {data['audio_id']}: {e}")
        raise


def is_audio_processed(audio_id: str) -> Path | None:
    """
    Checks whether a processed report already exists for the given audio file.
    The function converts the audio filename to its corresponding JSON report
    filename and verifies whether the report file exists in the output directory.

    Args:
        audio_id (str): ID of the audio file on Google Drive.

    Returns:
        Path | None: Path to the existing JSON report if found; otherwise None.
    """
    target_path = OUTPUT_DIR / f'{audio_id}.json'
    return target_path if target_path.is_file() else None


def json_reader(file: Path) -> dict[str, Any] | None:
    """
    Safely reads and deserializes a JSON file.

    Args:
        file (Path): Path to a configuration or report file.

    Returns:
        dict[str, Any] | None: Dictionary containing the parsed data,
        or None if an error occurs.

    Raises:
        No exceptions are propagated. The function handles the following errors
        internally and returns None:
            - FileNotFoundError: If the file does not exist.
            - json.JSONDecodeError: If the file contains invalid JSON or is empty.
    """
    try:
        with open(file, 'r', encoding='utf-8') as f:
            data_dict = json.load(f)
        logger.info(f'Successfully read JSON report: {file}')
        return data_dict

    except FileNotFoundError:
        logger.error(f"Read error: File not found error on path: {file}")
        return None

    except json.JSONDecodeError as e:
        logger.error(f"Decoder error: File {file} contains non-valid JSON or empty. Details: {e}")
        return None