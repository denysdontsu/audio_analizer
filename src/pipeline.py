from pathlib import Path
import whisper
import logging

from config.config import (
    TARGET_PARENT_ID,
    SOURCE_SHEET_ID,
    WHISPER_PROMPT,
    TARGET_SHEET_NAME,
    TARGET_AUDIO_FOLDER_NAME,
    SHEETS_COLUMNS_SCHEMA
)
from log.logger_config import setup_logging
from src.analyzer import generate_chat_report
from src.google import (
    create_new_folder,
    copy_audio,
    download_audio_by_id,
    write_transcribe,
    copy_sheets,
    get_file_id_by_name,
)
from src.google.drive import download_text_by_id
from src.sheets_writer import calculate_operation_score, build_row
from src.transcriber import transcribe_audio
from src.utils import create_name
from src.cache import load_local_cache, save_local_cache

setup_logging()
logger = logging.getLogger(__name__)


def setup_workspace(
    drive_service
) -> tuple[str, str]:
    """
    Ensures the target Google Sheet and audio folder exist in the target directory.
    Copies the source sheet and creates the audio folder if they are missing.

    Args:
        drive_service: Authorized Google Drive API service instance.

    Returns:
        tuple[str, str]: A tuple of (copied_sheet_id, audio_folder_id).
    """
    # Check if target_sheet already exists, create if not
    copied_sheet_id = get_file_id_by_name(
        drive_service,
        TARGET_PARENT_ID,
        TARGET_SHEET_NAME
    )
    if not copied_sheet_id:
        copied_sheet_id = copy_sheets(
            drive_service,
            SOURCE_SHEET_ID,
            TARGET_PARENT_ID
        )

    # Check if audio folder already exists, create if not
    audio_folder_id = get_file_id_by_name(
        drive_service,
        TARGET_PARENT_ID,
        TARGET_AUDIO_FOLDER_NAME
    )
    if not audio_folder_id:
        audio_folder_id = create_new_folder(
            drive_service,
            TARGET_PARENT_ID,
            TARGET_AUDIO_FOLDER_NAME
        )

    return copied_sheet_id, audio_folder_id


def create_and_write_transcription(
        drive_service,
        audio_id: str,
        audio_name: str,
        universal_audio_name: str,
        whisper_model: whisper.Whisper,
        audio_folder_id: str,
) -> str:
    """
    Downloads an audio file, transcribes it using Whisper, and uploads
    the transcription as a .txt file to the specified Google Drive folder.

    Args:
        drive_service: Authorized Google Drive API service instance.
        audio_id (str): Google Drive ID of the audio file to download.
        audio_name (str): Original filename of the audio.
        universal_audio_name (str): Normalized filename used for storage.
        whisper_model: Loaded Whisper model instance.
        audio_folder_id (str): Google Drive folder ID where the transcription will be saved.

    Returns:
        str: Transcribed text content.
    """
    temp_audio_path = download_audio_by_id(drive_service, audio_id, audio_name)

    transcription = transcribe_audio(
        model=whisper_model,
        audio=temp_audio_path,
        original_name=universal_audio_name,
        initial_prompt=WHISPER_PROMPT
    )
    logger.info(f'Transcribed: {audio_name}')

    # Save transcription to Drive, next to audio
    write_transcribe(
        drive_service=drive_service,
        output_dir_id=audio_folder_id,
        file_name=universal_audio_name,
        file_text=transcription
    )
    temp_audio_path.unlink()

    return transcription


def _process_from_cache(
        drive_service,
        audio_id: str,
        universal_name: str,
        cached_data: dict,
        drive_inventory: dict,
        audio_folder_id: str
) -> list:
    """
    Builds a Sheets row from locally cached report data.
    If the audio file is missing from Google Drive, re-copies it and updates the cache.
    If the transcription .txt file is missing from Google Drive, re-copies it.

    Args:
        drive_service: Authorized Google Drive API service instance.
        audio_id (str): Google Drive ID of the original audio file.
        universal_name (str): Normalized filename used as cache key.
        cached_data (dict): Previously saved report data loaded from local cache.
        drive_inventory (dict): Map of filename → file ID for files already on Drive.
        audio_folder_id (str): Google Drive folder ID where the audio will be saved.

    Returns:
        list: Ordered row ready for Google Sheets insertion.
    """
    copied_id = drive_inventory.get(universal_name)

    if not copied_id:
        logger.warning(f"Audio '{universal_name}' missed from Drive but found in cache. Re-copying...")
        copied_id = copy_audio(
            drive_service=drive_service,
            audio_name=universal_name,
            audios_dir_id=audio_folder_id,
            audio_id=audio_id
        )
        cached_data['audio_link'] = f'https://drive.google.com/file/d/{copied_id}/view?usp=share_link'
        save_local_cache(cached_data)

    transcription_id = drive_inventory.get(universal_name.replace('.mp3', '.txt'))
    if not transcription_id:
        write_transcribe(
            drive_service=drive_service,
            output_dir_id=audio_folder_id,
            file_name=universal_name,
            file_text=cached_data['transcription']
        )

    return [
        f'=HYPERLINK("{cached_data["audio_link"]}"; "Прослухати")' if col == "audio_link"
        else cached_data.get(col, '')
        for col in SHEETS_COLUMNS_SCHEMA
    ]


def _process_full_cycle(
        drive_service,
        whisper_model: whisper.Whisper,
        audio_id: str,
        audio_name: str,
        universal_name: str,
        audio_folder_id: str,
        drive_inventory: dict
) -> list:
    """
    Runs the full processing pipeline for a single audio file:
    copies audio to Drive, transcribes it (or reuses existing transcription),
    analyzes with LLM, builds and caches the result.

    Args:
        drive_service: Authorized Google Drive API service instance.
        whisper_model: Loaded Whisper model instance.
        audio_id (str): Google Drive ID of the source audio file.
        audio_name (str): Original filename of the audio.
        universal_name (str): Normalized filename used for storage and cache lookup.
        audio_folder_id (str): Google Drive folder ID for storing audio and transcriptions.
        drive_inventory (dict): Map of filename → file ID for files already on Drive.

    Returns:
        list: Ordered row ready for Google Sheets insertion.
    """
    # Check/copy audio to Drive
    copied_id = drive_inventory.get(universal_name)
    if not copied_id:
        copied_id = copy_audio(
            drive_service=drive_service,
            audio_name=universal_name,
            audios_dir_id=audio_folder_id,
            audio_id=audio_id
        )
        drive_inventory[universal_name] = copied_id

    # Check/copy transcription
    transcription_file_name = str(Path(universal_name).with_suffix('.txt'))
    transcription_id = drive_inventory.get(transcription_file_name)

    if not transcription_id:
        logger.info(f"Transcription not found for '{transcription_file_name}'. Running Whisper...")
        transcription = create_and_write_transcription(
            drive_service=drive_service,
            audio_id=copied_id,
            audio_name=audio_name,
            universal_audio_name=universal_name,
            whisper_model=whisper_model,
            audio_folder_id=audio_folder_id
        )
    else:
        logger.info(f"Found existing transcription file: '{transcription_file_name}'")
        transcription = download_text_by_id(drive_service, transcription_id)

    # Analytics through LLM
    logger.info(f"Running LLM analysis for '{universal_name}'...")
    chat_report = generate_chat_report(transcription)
    manager_score = calculate_operation_score(chat_report)

    # Collection and preservation of results
    raw_data, sheets_row = build_row(
        universal_audio_name=universal_name,
        filename=audio_name,
        copied_audio_id=copied_id,
        chat_report=chat_report,
        transcription=transcription,
        manager_score=manager_score
    )
    save_local_cache(raw_data)

    return sheets_row


def process_single_audio(
        drive_service,
        whisper_model: whisper.Whisper,
        audio_id: str,
        audio_name: str,
        drive_inventory: dict[str, str],
        audio_folder_id: str
) -> list:
    """
    Processes a single audio file through the full pipeline or from local cache.
    Checks local cache first — if a report exists, builds the row from cached data.
    Otherwise, runs the full cycle: copy, transcribe, analyze, cache.

    Args:
        drive_service: Authorized Google Drive API service instance.
        whisper_model: Loaded Whisper model instance.
        audio_id (str): Google Drive ID of the audio file.
        audio_name (str): Original filename of the audio.
        drive_inventory (dict[str, str]): Map of filename → file ID for Drive files.
        audio_folder_id (str): Google Drive folder ID for audio and transcription storage.

    Returns:
        list: Ordered row ready for Google Sheets insertion.
    """
    universal_name = create_name(audio_id, audio_name)
    cached_data = load_local_cache(universal_name)

    if cached_data:
        # Route A: build row from local cache
        return _process_from_cache(
            drive_service,
            audio_id,
            universal_name,
            cached_data,
            drive_inventory,
            audio_folder_id
        )

    # Route B: run full processing cycle
    return _process_full_cycle(
        drive_service,
        whisper_model,
        audio_id,
        audio_name,
        universal_name,
        audio_folder_id,
        drive_inventory
    )