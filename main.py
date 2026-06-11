import logging

from config.config import SOURCE_FOLDER_ID, SHEETS_DATA_RANGE
from src.google import (
    get_drive_service,
    get_sheets_service,
    get_files,
    get_unprocessed_audio,
    get_last_sheet_index,
    write_result
)
from src.pipeline import setup_workspace, process_single_audio
from src.transcriber import get_whisper_model

logger = logging.getLogger(__name__)


def main():
    """
    Main pipeline entry point.
    Fetches unprocessed audio from Google Drive, transcribes each file,
    analyzes the dialogue via OpenAI, and writes results to Google Sheets.
    """
    drive_service = get_drive_service()
    sheets_service = get_sheets_service()
    whisper_model = get_whisper_model()

    copied_sheet_id, audio_folder_id = setup_workspace(drive_service)

    # Collect inventory of files that are already on the Disk (.mp3 and .txt)
    drive_inventory = get_files(
        drive_service=drive_service,
        source_folder_id=audio_folder_id,
        mime_type_filter=['audio/mpeg', 'text/plain'],
        by_name=True
    )

    # Fetch unprocessed audio from source folder
    unprocessed_audio = get_unprocessed_audio(
        drive_service,
        sheets_service,
        SOURCE_FOLDER_ID,
        copied_sheet_id,
        SHEETS_DATA_RANGE
    )

    if not unprocessed_audio:
        logger.info('No unprocessed audio files found. Exiting.')
        return

    result = []

    for audio_id, audio_name in unprocessed_audio.items():
        try:
            sheets_row = process_single_audio(
                drive_service=drive_service,
                whisper_model=whisper_model,
                audio_id=audio_id,
                audio_name=audio_name,
                drive_inventory=drive_inventory,
                audio_folder_id=audio_folder_id,
            )
            result.append(sheets_row)

        except Exception as e:
            logger.error(f'Failed to process audio "{audio_name}" (ID: {audio_id}): {e}')
            continue

    if result:
        last_sheet_index = get_last_sheet_index(sheets_service, copied_sheet_id)
        write_result(
            sheets_service,
            copied_sheet_id,
            result,
            f'Лист1!A{last_sheet_index}'
        )
        logger.info(f'Pipeline complete. Processed {len(result)} audio files.')
    else:
        logger.warning('No new results to write to Google Sheets.')


if __name__ == '__main__':
    main()