from pathlib import Path

import whisper

from config.config import WHISPER_MODEL


def get_whisper_model():
    """
    Get Whisper model

    Notion:
        Model version change in config.py (WHISPER_MODEL)
    """
    return whisper.load_model(WHISPER_MODEL)


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
    """
    carry_initial_prompt = initial_prompt is not None

    result = model.transcribe(
        str(audio),
        initial_prompt=initial_prompt,
        carry_initial_prompt=carry_initial_prompt
    )
    return result['text']