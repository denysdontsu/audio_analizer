import logging
from pathlib import Path

import whisper

from config.config import WHISPER_MODEL

logger = logging.getLogger(__name__)


def get_whisper_model():
    """
    Get Whisper model

    Returns:
        whisper.Whisper: Loaded Whisper model instance.

    Raises:
        Exception: If the model fails to load.

    Notion:
        Model version change in config.py (WHISPER_MODEL)
    """
    try:
        logger.info(f'Whisper model "{WHISPER_MODEL}" loaded successfully')
        return whisper.load_model(WHISPER_MODEL)

    except Exception as e:
        logger.error(f'Failed to load Whisper model "{WHISPER_MODEL}": {e}')
        raise

def transcribe_audio(
        model: whisper.Whisper,
        audio: Path | str,
        initial_prompt: str | None = None
) -> str:
    """
    Transcribe audio

    Args:
        model: Whisper model
        audio: Audio that needs to be transcribed. Type: Path or path in str type
        initial_prompt: Initial context promt for Wisper model

    Returns:
        Resulting text

    Raises:
        Exception: If transcription fails.
    """
    carry_initial_prompt = initial_prompt is not None

    try:
        result = model.transcribe(
            str(audio),
            initial_prompt=initial_prompt,
            carry_initial_prompt=carry_initial_prompt
        )
        logger.info(f'Transcription completed for: {audio}')
        return result['text']

    except Exception as e:
        logger.error(f'Transcription failed for {audio}: {e}')
        raise