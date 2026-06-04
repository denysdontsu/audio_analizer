import logging

logger = logging.getLogger(__name__)


def calculate_operation_score(chat_report: dict) -> float:
    """
    Calculates the final call performance score based on checklist completion
    and the manager's evaluation.

    Scoring formula:
    - 40%: percentage of completed mandatory checklist items.
    - 60%: manager score (manager_score).

    Args:
        chat_report (dict): Dictionary containing call analysis results.

    Returns:
        float: Final score in the range of 0–100, rounded to 2 decimal places.
    """
    checklist_score = []
    mandatory_keys = [
        'greeting', 'manager_name', 'car_body', 'car_year',
        'mileage', 'diagnostics_offer', 'previous_work', 'appointment_made'
    ]
    for key in mandatory_keys:
        try:
            checklist_score.append(int(chat_report.get(key, 0)))
        except (ValueError, TypeError):
            checklist_score.append(0)

    checklist_percent = (sum(checklist_score) / len(mandatory_keys)) * 100
    manager_score = chat_report.get('manager_score', 0)
    operation_score = round((checklist_percent * 0.4) + (manager_score * 0.6), 2)

    logger.info(f'Operation score calculated: {operation_score}')
    return operation_score