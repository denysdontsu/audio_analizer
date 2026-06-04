import logging

from googleapiclient.errors import HttpError

from src.google import get_audios

logger = logging.getLogger(__name__)

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