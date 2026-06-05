import logging

from config.config import (
    TARGET_PARENT_ID,
    SOURCE_FOLDER_ID,
    SOURCE_SHEET_ID,
    WHISPER_PROMPT, TARGET_SHEET_NAME, TARGET_AUDIO_FOLDER_NAME
)
from log.logger_config import setup_logging
from src.analyzer import generate_chat_report
from src.google import (
    get_drive_service,
    get_sheets_service,
    create_new_folder,
    get_unprocessed_audio,
    copy_audio,
    download_audio_by_id,
    write_transcribe,
    get_last_sheet_index,
    write_result,
    copy_sheets,
    get_file_id_by_name
)
from src.sheets_writer import calculate_operation_score, build_row
from src.transcriber import get_whisper_model, transcribe_audio

setup_logging()
logger = logging.getLogger(__name__)

def main():
    """
    Main pipeline entry point.
    Fetches unprocessed audio from Google Drive, transcribes each file,
    analyzes the dialogue via OpenAI, and writes results to Google Sheets.
    """
    # Initialize services and models
    drive_service = get_drive_service()
    sheets_service = get_sheets_service()
    whisper_model = get_whisper_model()

    # Check if target sheet already exists, copy from source if not
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

    # Fetch unprocessed audio from source folder
    unprocessed_audio = get_unprocessed_audio(
        drive_service,
        sheets_service,
        SOURCE_FOLDER_ID,
        copied_sheet_id,
        'Лист1!A3:A'
    )
    if not unprocessed_audio:
        logger.info('No unprocessed audio files found. Exiting.')
        return

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

    # Copy audio files to target folder
    copy_audio(
        drive_service,
        audio_folder_id,
        unprocessed_audio
    )

    # Process each audio file
    result = []
    audio_id, audio_name = None, None
    temp_audio_path = None
    for audio in unprocessed_audio:
        try:
            audio_id = audio['id']
            audio_name = audio['name']

            # Transcribe
            temp_audio_path = download_audio_by_id(drive_service, audio_id, audio_name)
            transcription = transcribe_audio(
                whisper_model,
                temp_audio_path,
                audio_name,
                WHISPER_PROMPT
            )
            print(f'Transcribed: {audio_name}')

            # Save transcription to Drive, next to audio
            write_transcribe(
                drive_service,
                audio_folder_id,
                audio_name,
                transcription
            )

            # Analyze and build row
            chat_report = generate_chat_report(transcription)
            manager_score = calculate_operation_score(chat_report)
            row = build_row(audio_name, chat_report, transcription, manager_score)
            result.append(row)

        except Exception as e:
            logger.error(f'Failed to process audio {audio_name}: {e}')
            continue
        finally:
            if temp_audio_path and temp_audio_path.exists():
                temp_audio_path.unlink()

    # Write results to Google Sheets
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
        logger.warning('No results to write.')


if __name__ == '__main__':
    main()