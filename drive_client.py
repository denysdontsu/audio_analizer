from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

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


def create_new_folder(
        service,
        parent_targe_folder_id: str | None,
        folder_name: str
) -> str:
    """
    Creates a new folder in Google Drive.

    Args:
        service: Authorized Google Drive API service instance.
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

    new_folder = service.files().create(body=new_folder_metadata, fields='id').execute()
    new_folder_id = new_folder['id']

    return new_folder_id


def get_folder_name(
        service,
        source_folder_id: str
) -> str:
    """
    Retrieves the name of a folder from Google Drive by its ID.

    Args:
        service: Authorized Google Drive API service instance.
        source_folder_id: The ID of the folder to retrieve the name for.

    Returns:
        str: The name of the specified folder.
    """
    source_folder = service.files().get(fileId=source_folder_id, fields='id, name').execute()
    source_folder_name = source_folder['name']

    return source_folder_name


def get_audio(
        service,
        source_folder_id: str
) -> list:
    """
    Retrieves all audio files from a specific Google Drive folder.

    Args:
        service: Authorized Google Drive API service instance.
        source_folder_id: The ID of the folder to scan for audio files.

    Returns:
        list[dict]: A list of dictionaries, where each dictionary contains
            the 'id' and 'name' of an audio file.
    """
    audios = []
    page_token = None

    while True:
        response = service.files().list(
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


def copy_audio(service, audios_dir_id: str, audios: list[dict, dict]):
    """
    Copies a list of audio files to a destination folder.

    Args:
        service: Authorized Google Drive API service instance.
        audios_dir_id: The ID of the destination folder where files will be saved.
        audios: A list of dictionaries containing 'id' and 'name' of the audio files to copy.
    """
    for audio in audios:
        audio_metadata = {
            'name': audio['name'],
            'parents': [audios_dir_id]
        }
        service.files().copy(fileId=audio['id'], body=audio_metadata).execute()