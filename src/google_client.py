import io
import tempfile
from pathlib import Path

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload

from config.config import SCOPES, TOKEN_PATH, CREDENTIALS_PATH


def get_credentials():
    """
    Loads Google OAuth credentials from TOKEN_PATH or runs OAuth flow if missing/invalid.

    Returns:
        Credentials: Authorized Google API credentials.

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
            creds.refresh(Request())
        # Otherwise start OAuth flow
        else:
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
    """
    new_folder_metadata = {
        'name': folder_name,
        'mimeType': 'application/vnd.google-apps.folder'
    }
    if parent_targe_folder_id:
        new_folder_metadata['parents'] = [parent_targe_folder_id]

    new_folder = service_drive.files().create(body=new_folder_metadata, fields='id').execute()
    new_folder_id = new_folder['id']

    return new_folder_id


def get_file_name(
        drive_service,
        source_file_id: str
) -> str:
    # сделал функцию более универсальной, не привязывая конкретно к имени папки (это может быть как файл так и папка) просто получаем имя по id
    """
    Retrieves the name of a file or folder from Google Drive by its ID.

    Args:
        drive_service: Authorized Google Drive API service instance.
        source_file_id: The ID of the file or folder to retrieve the name for.

    Returns:
        str: The name of the specified file or folder.
    """
    source = drive_service.files().get(fileId=source_file_id, fields='name').execute()
    source_file_name = source['name']

    return source_file_name


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
    """
    audios = []
    page_token = None

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

    return audios


def copy_audio(drive_service, audios_dir_id: str, audios: list[dict, dict]):
    """
    Copies a list of audio files to a destination folder.

    Args:
        drive_service: Authorized Google Drive API service instance.
        audios_dir_id: The ID of the destination folder where files will be saved.
        audios: A list of dictionaries containing 'id' and 'name' of the audio files to copy.
    """
    for audio in audios:
        audio_metadata = {
            'name': audio['name'],
            'parents': [audios_dir_id]
        }
        drive_service.files().copy(fileId=audio['id'], body=audio_metadata).execute()


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
    """
    name = get_file_name(drive_service, source_sheets_id)
    sheets_metadata = {
        'name': name,
        'parents': [parent_file_id]
    }

    request = drive_service.files().copy(fileId=source_sheets_id, body=sheets_metadata, fields='id').execute()
    copied_sheets_id = request['id']

    return copied_sheets_id


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
    """
    data = sheets_service.spreadsheets().values().get(
        spreadsheetId=sheets_id,
        range=sheets_range
    ).execute()
    return [row for row in data.get('values', []) if row]


def get_unprocessed_audio(
        drive_service,
        sheets_service,
        source_folder_id,
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

    return [item for item in all_target_audios if item['name'] not in all_processed_audio]


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
    """
    with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as temp_file:
        temp_audio_path = Path(temp_file.name)

    request = drive_service.files().get_media(fileId=audio_id)

    with io.FileIO(temp_audio_path, 'wb') as f:
        downloader = MediaIoBaseDownload(f, request)
        done = False

        while not done:
            status, done = downloader.next_chunk()

    return temp_audio_path
