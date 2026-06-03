import logging

from config.config import LOG_PATH


def setup_logging():
    """
    Configure the root logger for the application.

    Writes all log messages (INFO and above) to the log file defined
    by LOG_PATH in append mode. Errors are also printed to the console.

    Note:
        Should be called once at application startup before any logging occurs.
        Log format: 'YYYY-MM-DD HH:MM:SS LEVEL [function_name] message'
    """
    LOG_PATH.parent.mkdir(parents=True, exist_ok=True)

    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s %(levelname)s [%(funcName)s] %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S',
        filename=LOG_PATH,
        filemode='a',
        encoding='utf-8'
    )
    # Errors to console
    console = logging.StreamHandler()
    console.setLevel(logging.ERROR)
    console.setFormatter(logging.Formatter('%(levelname)s: [%(funcName)s] %(message)s'))
    logging.getLogger().addHandler(console)