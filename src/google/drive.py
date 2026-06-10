import io
import logging
import tempfile
from pathlib import Path

from googleapiclient.errors import HttpError
from googleapiclient.http import MediaIoBaseDownload, MediaInMemoryUpload

logger = logging.getLogger(__name__)

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


def get_files(
        drive_service,
        source_folder_id: str,
        mime_type_filter: str | list[str] | None = None,
        by_name: bool = False
) -> dict[str, str]:
    """
    Retrieves files from a Google Drive folder, optionally filtered by MIME type.

    Args:
        drive_service: Authorized Google Drive API service instance.
        source_folder_id (str): ID of the folder to scan.
        mime_type_filter (str | list[str] | None): MIME type filter(s) to apply.
            If a string is provided, files matching that MIME type pattern
            are returned. If a list is provided, files matching any of the
            specified patterns are returned. If None, all files in the folder
            are retrieved.
        by_name (bool): If True, returns dict with format {name: id}.
                        If False, returns dict with format {id: name}.

    Returns:
        dict: Dict containing {id: name} or {name: id} depending on `by_name` flag.

    Raises:
        HttpError: If the Google Drive API request fails.
    """
    files = {}
    page_token = None

    query = f"'{source_folder_id}' in parents and trashed = false"

    if mime_type_filter:
        filters = [mime_type_filter] if isinstance(mime_type_filter, str) else mime_type_filter
        mime_queries = [f"mimeType contains '{m}'" for m in filters]
        query += f" and ({' or '.join(mime_queries)})"

    try:
        while True:
            response = drive_service.files().list(
                q = query,
                fields = 'nextPageToken, files(id, name)',
                pageSize = 100,
                pageToken = page_token
            ).execute()

            for item in response.get('files', []):
                file_id = item['id']
                file_name = item['name']

                if not (file_id and file_name):
                    logger.error(f'Corrupted file object from Google API: "{item}"')
                    continue

                if by_name:
                    if file_name in files:
                        logger.warning(
                            f'Duplicate filename detected in folder {source_folder_id}: "{file_name}". Old ID {files[file_name]} will be overwritten by new ID {file_id}')
                    files[file_name] = file_id
                else:
                    files[file_id] = file_name

            page_token = response.get('nextPageToken', None)
            if not page_token:
                break

    except HttpError as e:
        logger.error(
            f'Failed to fetch files from folder {source_folder_id} '
            f'(mime_filter={mime_type_filter}): {e}')
        raise

    logger.info(f'Found {len(files)} files in folder {source_folder_id} '
                f'(mime_filter={mime_type_filter})')
    return files


def copy_audio(
        drive_service,
        audio_name: str,
        audios_dir_id: str,
        audio_id: str
) -> str:
    """
    Copies a list of audio files to a destination folder.

    Args:
        drive_service: Authorized Google Drive API service instance.
        audio_name: Universal audio name for the new copy ('[name]_[id].mp3').
        audios_dir_id: The ID of the destination folder where files will be saved.
        audio_id: 'id' of the audio files to copy.

    Returns:
        str: The ID of the newly created copied file on Google Drive.

    Raises:
        HttpError: If any individual file copy operation fails.
    """
    audio_metadata = {
        'name': audio_name,
        'parents': [audios_dir_id]
    }
    try:
        new_file = drive_service.files().copy(
            fileId=audio_id,
            body=audio_metadata,
            fields='id'
        ).execute()
        new_file_id = new_file.get('id')
        logger.info(f'Copied audio: {audio_name}')
        return new_file_id

    except HttpError as e:
        logger.error(f'Failed to copy audio {audio_name}: {e}')
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


def download_audio_by_id(
        drive_service,
        audio_id: str,
        file_name: str
) -> Path:
    """
    Downloads an audio file from Google Drive into a temporary MP3 file.

    Args:
        drive_service: Authorized Google Drive API service instance (v3).
        audio_id: The ID of the audio file on Google Drive.
        file_name: Original audio file name used for logging purposes.

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

        logger.info(f'Downloaded audio file: "{file_name}" (ID: {audio_id})')
        return temp_audio_path

    except HttpError as e:
        logger.error(f'Failed to download audio "{file_name}" (ID: {audio_id}): {e}')
        raise
    except OSError as e:
        logger.error(f'File system error while downloading audio {file_name} (ID: {audio_id}): {e}')
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
        'name': file_name.replace('.mp3', '.txt'),
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


def get_file_id_by_name(
        drive_service,
        parent_folder_id: str,
        file_name: str
) -> str | None:
    """
    Searches for a file or folder by name within a specified Google Drive folder
    and returns its ID if found.
    The function searches for a non-trashed file with the specified name
    within the given parent folder and returns its Google Drive file ID.

    Args:
        drive_service: Authenticated Google Drive API service instance.
        parent_folder_id (str): ID of the parent folder to search in.
        file_name (str): Name of the target file.

    Returns:
        str | None: File ID if a matching file is found; otherwise None.

    Raises:
        HttpError: If the Google Drive API request fails.
    """
    try:
        response = drive_service.files().list(
            q=f"name = '{file_name}' and '{parent_folder_id}' in parents and trashed = false",
            fields='files(id, name)'
        ).execute()

    except HttpError as e:
        logger.error(f'Failed to search for file "{file_name}" in folder {parent_folder_id}: {e}')
        raise

    file = response.get('files', [])
    if file:
        file_id = file[0]['id']
        logger.info(f'File "{file_name}" found with ID: {file_id}')
        return file_id
    return None


def download_text_by_id(drive_service, file_id: str) -> str:
    """
    Downloads a text file from Google Drive directly into RAM
    and returns its content as a string.

    Args:
        drive_service: Authorized Google Drive API service instance (v3).
        file_id (str): The unique ID of the text file on Google Drive.

    Returns:
        str: The full text content of the file decoded in UTF-8.

    Raises:
        HttpError: If the Google Drive API request fails.
    """
    try:
        text_stream = io.BytesIO()

        request = drive_service.files().get_media(fileId=file_id)
        downloader = MediaIoBaseDownload(text_stream, request)

        done = False
        while not done:
            status, done = downloader.next_chunk()

        text_content = text_stream.getvalue().decode('utf-8')

        logger.info(f'Text file (ID: {file_id}) successfully loaded into RAM.')
        return text_content

    except HttpError as e:
        logger.error(f'Google Drive API error while downloading text (ID: {file_id}): {e}')
        raise