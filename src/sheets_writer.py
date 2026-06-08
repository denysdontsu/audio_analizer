import logging

from src.utils import parse_audio_filename

logger = logging.getLogger(__name__)


def calculate_operation_score(chat_report: dict) -> float:
    """
    Calculates the final call performance score based on checklist completion
    and the manager's evaluation.

    If the call is flagged as non-actionable or short by the AI in the
    'comments' field (contains the "[НЕАКТУАЛЬНИЙ ДЗВІНОК]" marker),
    the function immediately returns 0.0 to avoid mathematical bias.

    Scoring formula:
    - 40%: percentage of completed mandatory checklist items.
    - 60%: manager score (manager_score).

    Args:
        chat_report (dict): Dictionary containing call analysis results.

    Returns:
        float: Final score in the range of 0–100, rounded to 2 decimal places.
    """
    comments = chat_report.get('comments', '').lower()

    if 'неактуальний дзвінок' in comments:
        logger.info('Operation score calculated: 0.0 (Flagged as non-actionable call)')
        return 0.0

    checklist_score = []
    boolean_keys = [
        'greeting', 'diagnostics_offer', 'previous_work',
        'appointment_made', 'farewell'
    ]
    presence_keys = [
        'manager_name', 'car_body', 'car_year', 'mileage'
    ]

    for key in boolean_keys:
        try:
            checklist_score.append(1 if int(chat_report.get(key, 0)) else 0)
        except (ValueError, TypeError):
            checklist_score.append(0)

    for key in presence_keys:
        value = chat_report.get(key, 0)
        checklist_score.append(0 if value == 0 or value == '0' else 1)

    checklist_percent = (
        sum(checklist_score) / len(boolean_keys + presence_keys)
    ) * 100
    manager_score = chat_report.get('manager_score', 0)
    operation_score = round((checklist_percent * 0.4) + (manager_score * 0.6), 2)

    logger.info(f'Operation score calculated: {operation_score}')
    return operation_score


def build_row(
        audio_id: str,
        filename: str,
        char_report: dict,
        transcription: str,
        manager_score: float
) -> list:
    """
    Builds a structured row for insertion into a Google Sheets table.

    The function combines data from the parsed audio filename, chat report,
    transcription text, and manager evaluation score into a single ordered list.
    This row is intended to match a predefined spreadsheet schema.

    Args:
        audio_id (str): Identifier for audio, google audio id.
        filename (str): Audio filename.
        char_report (dict): Analysis report containing structured call metrics
            (e.g., manager_name, greeting, car details, outcomes, etc.).
        transcription (str): Full transcription of the conversation.
        manager_score (float): Final evaluation score assigned to the manager.

    Returns:
        list: Ordered list representing a single row for Google Sheets insertion.
    """
    parsed_f = parse_audio_filename(filename)
    if not parsed_f:
        parsed_f = {}

    report = char_report or {}

    row = [
        audio_id,
        parsed_f.get('date_time', ''),
        parsed_f.get('call_type', ''),
        '',  # No data for the column 'Тип звернення'
        parsed_f.get('number', ''),
        '',  # No data for the column 'Філія'
        report.get('manager_name', 'Не представився'),
        transcription or '',
        report.get('greeting', ''),
        report.get('car_body', ''),
        report.get('car_year', ''),
        report.get('mileage', ''),
        report.get('diagnostics_offer', ''),
        report.get('previous_work', ''),
        report.get('appointment_made', ''),
        report.get('farewell', ''),
        report.get('work_types', 'Інший варіант'),
        '',  # No data for the column 'Чи дотримувався всіх інструкцій з топ 100 робіт Да/Ні'
        '',  # No data for the column 'Яких рекоменадцій менеджер не дотримувався з топ 100 робіт'
        report.get('result_type', ''),
        manager_score if manager_score is not None else 0.0,
        report.get('spare_parts', ''),
        report.get('comments', '')
    ]

    return row