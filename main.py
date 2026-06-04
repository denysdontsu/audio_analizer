import logging

from config.config import (
    TARGET_PARENT_ID,
    TARGET_SHEET_ID,
    SOURCE_FOLDER_ID,
    SOURCE_SHEET_ID,
    WHISPER_PROMPT
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
    get_audios
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

    # Fetch unprocessed audio from source folder
    unprocessed_audio = get_unprocessed_audio(
        drive_service,
        sheets_service,
        SOURCE_FOLDER_ID,
        SOURCE_SHEET_ID,
        'Лист1!A3:A'
    )
    if not unprocessed_audio:
        logger.info('No unprocessed audio files found. Exiting.')
        return

    # Copy audio files to target folder
    new_audio_folder_id = create_new_folder(
        drive_service,
        TARGET_PARENT_ID,
        'audios'
    )
    copy_audio(
        drive_service,
        new_audio_folder_id,
        unprocessed_audio
    )
    copied_audios = get_audios(drive_service, new_audio_folder_id)

    # Process each audio file
    result = []
    audio_id, audio_name = None, None
    temp_audio_path = None
    for audio in copied_audios:
        try:
            audio_id = audio['id']
            audio_name = audio['name']

            # Transcribe
            temp_audio_path = download_audio_by_id(drive_service, audio_id)
            transcription = transcribe_audio(
                whisper_model,
                temp_audio_path,
                WHISPER_PROMPT
            )

            # Save transcription to Drive, next to audio
            write_transcribe(
                drive_service,
                new_audio_folder_id,
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
        last_sheet_index = get_last_sheet_index(sheets_service, TARGET_SHEET_ID)
        write_result(
            sheets_service,
            TARGET_SHEET_ID,
            result,
            f'Лист1!A{last_sheet_index}'
        )
        logger.info(f'Pipeline complete. Processed {len(result)} audio files.')
    else:
        logger.warning('No results to write.')


if __name__ == '__main__':
    main()