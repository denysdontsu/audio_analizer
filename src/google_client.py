import io
import logging
import tempfile
from pathlib import Path

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from googleapiclient.http import MediaIoBaseDownload, MediaInMemoryUpload

from config.config import SCOPES, TOKEN_PATH, CREDENTIALS_PATH

logger = logging.getLogger(__name__)

def get_credentials():
    """
    Loads Google OAuth credentials from TOKEN_PATH or runs OAuth flow if missing/invalid.

    Returns:
        Credentials: Authorized Google API credentials.

    Raises:
        FileNotFoundError: If credentials.json is missing.
        Exception: If token refresh or OAuth flow fails.

    Notes:
        Refreshes expired tokens automatically and saves updated credentials.
        On first run, opens browser for user login.
    """
    creds = None

    # If token exists
    if TOKEN_PATH.exists():
        creds = Credentials.from_authorized_user_file(
            TOKEN_PATH,
            SCOPES
        )

    # If token not exists or not valid
    if not creds or not creds.valid:
        # Try to update token
        if creds and creds.expired and creds.refresh_token:
            try:
                creds.refresh(Request())

            except Exception as e:
                logger.warning(f'Token refresh failed, restarting OAuth flow: {e}')
                creds = None

        # Otherwise start OAuth flow
        if not creds:
            if not CREDENTIALS_PATH.exists():
                raise FileNotFoundError(f'credentials.json not found at {CREDENTIALS_PATH}')
            flow = InstalledAppFlow.from_client_secrets_file(
                CREDENTIALS_PATH,
                SCOPES
            )
            creds = flow.run_local_server(port=0)

        with open(TOKEN_PATH, "w") as token:
          token.write(creds.to_json())

    return creds


def get_drive_service():
    """
    Creates and returns an authorized Google Drive API service instance.

    Returns:
        googleapiclient.discovery.Resource: Google Drive service object.
    """
    creds = get_credentials()
    service = build('drive', 'v3', credentials=creds)

    return service


def get_sheets_service():
    """
    Creates and returns an authorized Google Sheets API service instance.

    Returns:
        googleapiclient.discovery.Resource: Google Sheets service object.
    """
    creds = get_credentials()
    service = build('sheets', 'v4', credentials=creds)

    return service


def create_new_folder(
        service_drive,
        parent_targe_folder_id: str | None,
        folder_name: str
) -> str:
    """
    Creates a new folder in Google Drive.

    Args:
        service_drive: Authorized Google Drive API service instance.
        parent_targe_folder_id: Optional ID of the parent folder. If provided,
            the folder is created inside it; otherwise, it is created in the root directory.
        folder_name: Name of the folder to be created.

    Returns:
        str: The ID of the newly created folder.

    Raises:
        HttpError: If the Google Drive API request fails.
    """
    new_folder_metadata = {
        'name': folder_name,
        'mimeType': 'application/vnd.google-apps.folder'
    }
    if parent_targe_folder_id:
        new_folder_metadata['parents'] = [parent_targe_folder_id]

    try:
        new_folder = service_drive.files().create(body=new_folder_metadata, fields='id').execute()
        new_folder_id = new_folder['id']
        logger.info(f'Created folder "{folder_name}" with ID: {new_folder_id}')
        return new_folder_id

    except HttpError as e:
        logger.error(f'Failed to create folder "{folder_name}": {e}')
        raise


def get_file_name(
        drive_service,
        source_file_id: str
) -> str:
    """
    Retrieves the name of a file or folder from Google Drive by its ID.

    Args:
        drive_service: Authorized Google Drive API service instance.
        source_file_id: The ID of the file or folder to retrieve the name for.

    Returns:
        str: The name of the specified file or folder.

    Raises:
        HttpError: If the Google Drive API request fails.
    """
    try:
        source = drive_service.files().get(fileId=source_file_id, fields='name').execute()
        source_file_name = source['name']
        return source_file_name

    except HttpError as e:
        logger.error(f'Failed to get file name for ID {source_file_id}: {e}')
        raise


def get_audios(
        drive_service,
        source_folder_id: str
) -> list:
    """
    Retrieves all audio files from a specific Google Drive folder.

    Args:
        drive_service: Authorized Google Drive API service instance.
        source_folder_id: The ID of the folder to scan for audio files.

    Returns:
        list[dict]: A list of dictionaries, where each dictionary contains
            the 'id' and 'name' of an audio file.

    Raises:
        HttpError: If the Google Drive API request fails.
    """
    audios = []
    page_token = None

    try:
        while True:
            response = drive_service.files().list(
                q = f"mimeType contains 'audio/' and '{source_folder_id}' in parents",
                fields = 'nextPageToken, files(id, name)',
                pageSize = 100,
                pageToken = page_token
            ).execute()
            audios.extend(response.get('files', []))
            page_token = response.get('nextPageToken', None)
            if not page_token:
                break

    except HttpError as e:
        logger.error(f'Failed to fetch audio files from folder {source_folder_id}: {e}')
        raise

    logger.info(f'Found {len(audios)} audio files in folder {source_folder_id}')
    return audios


def copy_audio(drive_service, audios_dir_id: str, audios: list[dict]):
    """
    Copies a list of audio files to a destination folder.

    Args:
        drive_service: Authorized Google Drive API service instance.
        audios_dir_id: The ID of the destination folder where files will be saved.
        audios: A list of dictionaries containing 'id' and 'name' of the audio files to copy.

    Raises:
        HttpError: If any individual file copy operation fails.
    """
    for audio in audios:
        audio_metadata = {
            'name': audio['name'],
            'parents': [audios_dir_id]
        }
        try:
            drive_service.files().copy(fileId=audio['id'], body=audio_metadata).execute()
            logger.info(f'Copied audio: {audio["name"]}')

        except HttpError as e:
            logger.error(f'Failed to copy audio {audio["name"]}: {e}')
            raise


def copy_sheets(
        drive_service,
        source_sheets_id: str,
        parent_file_id: str
) -> str:
    """
    Copies an existing Google Sheet to a specified destination folder.

    Args:
        drive_service: Authorized Google Drive API service instance (v3).
        source_sheets_id: The ID of the source Google Sheet to copy.
        parent_file_id: The ID of the destination folder where the copy will be saved.

    Returns:
        str: The ID of the newly copied Google Sheet.

    Raises:
        HttpError: If the Google Drive API request fails.

    Note:
        Required by project specification. Not used in the main pipeline
        as the target sheet is managed directly.
    """
    name = get_file_name(drive_service, source_sheets_id)
    sheets_metadata = {
        'name': name,
        'parents': [parent_file_id]
    }

    try:
        request = drive_service.files().copy(fileId=source_sheets_id, body=sheets_metadata, fields='id').execute()
        copied_sheets_id = request['id']
        logger.info(f'Copied sheet "{name}" with ID: {copied_sheets_id}')
        return copied_sheets_id

    except HttpError as e:
        logger.error(f'Failed to copy sheet {source_sheets_id}: {e}')
        raise


def get_data_from_sheet(
        sheets_service,
        sheets_id: str,
        sheets_range: str
) -> list[list]:
    """
    Retrieves rows of data from a specific Google Sheet range, filtering out empty rows.

    Args:
        sheets_service: Authorized Google Sheets API service instance (v4).
        sheets_id: The ID of the Google Spreadsheet.
        sheets_range: The A1 notation range to retrieve data from (e.g., 'Sheet1!A:B').

    Returns:
        list[list]: A list of rows, where each row is a list of cell values.
            Empty rows are excluded.

    Raises:
        HttpError: If the Google Sheets API request fails.
    """
    try:
        data = sheets_service.spreadsheets().values().get(
            spreadsheetId=sheets_id,
            range=sheets_range
        ).execute()
        rows = [row for row in data.get('values', []) if row]
        logger.info(f'Retrieved {len(rows)} rows from range {sheets_range}')
        return rows

    except HttpError as e:
        logger.error(f'Failed to get data from sheet {sheets_id}, range {sheets_range}: {e}')
        raise


def get_unprocessed_audio(
        drive_service,
        sheets_service,
        source_folder_id: str,
        sheets_id: str,
        sheets_range: str
) -> list[dict]:
    """
    Compares audio files in a Google Drive folder against names listed in a Google Sheet
    and returns id and name of the files that are not present in the sheet.

    Args:
        drive_service: Authorized Google Drive API service instance (v3).
        sheets_service: Authorized Google Sheets API service instance (v4).
        source_folder_id: The ID of the Google Drive folder containing audio files.
        sheets_id: The ID of the Google Spreadsheet to check against.
        sheets_range: The A1 notation range containing existing audio names.

    Returns:
        list[dict]: Each dict contains 'id' and 'name' keys.
    """
    all_target_audios = get_audios(drive_service, source_folder_id)
    all_data_from_sheet = get_data_from_sheet(sheets_service, sheets_id, sheets_range)

    all_processed_audio = set(cell[0] for cell in all_data_from_sheet if cell[0])
    unprocessed = [item for item in all_target_audios if item['name'] not in all_processed_audio]

    logger.info(f'Found {len(unprocessed)} unprocessed audio files')
    return unprocessed


def download_audio_by_id(
        drive_service,
        audio_id: str
) -> Path:
    """
    Downloads an audio file from Google Drive into a temporary MP3 file.

    Args:
        drive_service: Authorized Google Drive API service instance (v3).
        audio_id: The ID of the audio file on Google Drive.

    Returns:
        Path: A pathlib.Path object pointing to the downloaded temporary file.

    Raises:
        HttpError: If the Google Drive API request fails.
        OSError: If a temporary file cannot be created or written.
    """
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as temp_file:
            temp_audio_path = Path(temp_file.name)

        request = drive_service.files().get_media(fileId=audio_id)

        with io.FileIO(temp_audio_path, 'wb') as f:
            downloader = MediaIoBaseDownload(f, request)
            done = False

            while not done:
                status, done = downloader.next_chunk()

        logger.info(f'Downloaded audio {audio_id} to {temp_audio_path}')
        return temp_audio_path

    except HttpError as e:
        logger.error(f'Failed to download audio {audio_id}: {e}')
        raise
    except OSError as e:
        logger.error(f'File system error while downloading audio {audio_id}: {e}')
        raise


def write_transcribe(
        drive_service,
        output_dir_id: str,
        file_name: str,
        file_text: str
) -> str:
    """
    Uploads a transcription text file to Google Drive.
    Creates a new `.txt` file in the specified Google Drive folder and uploads
    the provided text content.

    Args:
        drive_service: Authenticated Google Drive service instance.
        output_dir_id (str): ID of the Google Drive folder where the file will be stored.
        file_name (str): Name of the file to be created in Drive.
        file_text (str): Text content to upload as the file body.

    Returns:
        str: ID of the created file in Google Drive.

    Raises:
        HttpError: If the Google Drive API request fails.
    """
    new_file_metadata = {
        'name': file_name.replace('.mp3', ''),
        'mimeType': 'text/plain',
        'parents': [output_dir_id]
    }
    media = MediaInMemoryUpload(file_text.encode('utf-8'), mimetype='text/plain', resumable=True)

    try:
        file = drive_service.files().create(
            body=new_file_metadata,
            media_body=media,
            fields='id'
        ).execute()
        file_id = file['id']
        logger.info(f'Uploaded transcription for "{file_name}" with ID: {file_id}')
        return file_id

    except HttpError as e:
        logger.error(f'Failed to upload transcription for "{file_name}": {e}')
        raise


def get_last_sheet_index(
        sheet_service,
        sheet_id: str,
        sheet_column: str | None = 'Лист1!A:A'
) -> int:
    """
    Returns the next available row index in a Google Sheets column.
    The function reads the specified column range and finds the last non-empty row.
    It then returns the index of the next empty row (1-based indexing).

    Args:
        sheet_service: Authenticated Google Sheets API service instance.
        sheet_id (str): ID of the Google Spreadsheet.
        sheet_column (str | None): Range to inspect (default is 'Лист1!A:A').

    Returns:
        int: Index of the next empty row in the column.

    Raises:
        HttpError: If the Google Sheets API request fails.

    """
    try:
        result = sheet_service.spreadsheets().values().get(
            spreadsheetId=sheet_id,
            range=sheet_column
        ).execute()

    except HttpError as e:
        logger.error(f'Failed to get sheet index for {sheet_id}: {e}')
        raise

    rows = result.get('values', [])
    last_filled_index = 0

    if rows:
        for index, row in enumerate(rows):
            if row and row[0].strip() != '':
                last_filled_index = index + 1

    next_index = last_filled_index + 1
    logger.info(f'Next available row index: {next_index}')
    return next_index


def write_result(
        sheet_service,
        sheet_id: str,
        rows: list,
        zone_range: str
):
    """
    Writes data to a Google Sheets spreadsheet.

    The data is written using the Google Sheets API `update` method with
    `USER_ENTERED` mode, allowing Google Sheets to process values as if they
    were entered manually by a user.

    Args:
        sheet_service: Authenticated Google Sheets API service instance.
        sheet_id (str): ID of the target spreadsheet.
        rows (list): Two-dimensional list of values to write.
        zone_range (str): Target range in A1 notation.

    Returns:
        None

    Raises:
        HttpError: If the Google Sheets API request fails.

    Note:
        Supported range formats (replace 'Sheet1' with your worksheet name):

        - 'Sheet1!A6' (recommended): Uses the specified cell as the starting
          point and automatically expands to fit the provided data matrix.
          Existing values within the target area will be overwritten.
        - 'Sheet1!A6:D6': Limits updates to the specified row range. Data that
          exceeds the defined columns may be truncated by Google Sheets.
        - 'Sheet1!A1:F20': Updates only the specified rectangular range.
          Useful for replacing or clearing a fixed area of the worksheet.
    """
    body = {
        'values': rows
    }
    try:
        sheet_service.spreadsheets().values().update(
            spreadsheetId=sheet_id,
            range=zone_range,
            body=body,
            valueInputOption='USER_ENTERED'
        ).execute()
        logger.info(f'Written {len(rows)} rows to {zone_range}')

    except HttpError as e:
        logger.error(f'Failed to write to sheet {sheet_id}, range {zone_range}: {e}')
        raise