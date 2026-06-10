import json
import logging
from pathlib import Path
from typing import Any

from config.config import OUTPUT_DIR

logger = logging.getLogger(__name__)


def save_local_cache(
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
    file_name = Path(data['audio_id']).with_suffix('.json')
    new_file_path = OUTPUT_DIR / file_name

    try:
        with open(new_file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=4, ensure_ascii=False)
        logger.info(f"Report cached: {new_file_path}")

    except OSError as e:
        logger.error(f"Failed to save report {data['audio_id']}: {e}")
        raise


def is_audio_processed(universal_name: str) -> Path | None:
    """
    Checks whether a processed report already exists for the given audio file.
    The function converts the audio filename to its corresponding JSON report
    filename and verifies whether the report file exists in the output directory.

    Args:
        universal_name (str): ID of the audio file on Google Drive.

    Returns:
        Path | None: Path to the existing JSON report if found; otherwise None.
    """
    audio_name = Path(universal_name).with_suffix('.json')
    target_path = OUTPUT_DIR / audio_name
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


def load_local_cache(universal_name: str) -> dict[str, str] | None:
    """
    Loads cached report data for the given audio file if it exists locally.

    Args:
        universal_name (str): Universal filename used as cache key.

    Returns:
        dict[str, str] | None: Cached report data, or None if not found.
    """
    audio_path = is_audio_processed(universal_name)
    if audio_path:
        return json_reader(audio_path)
    return None