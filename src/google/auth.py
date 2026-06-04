import logging

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

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