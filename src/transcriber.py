import logging
from pathlib import Path

import whisper

from config.config import WHISPER_MODEL, ALLOWED_LANGUAGES

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


def detect_language(
        model: whisper.Whisper,
        audio: Path | str,
        original_name: str
) -> str:
    """
    Detect the spoken language of an audio file, restricted to allowed languages.

    Loads the first ~30 seconds of audio, computes a mel spectrogram,
    and uses Whisper's built-in language detection. Probability scores are
    filtered to only ALLOWED_LANGUAGES to avoid misdetection of similar
    languages (e.g. Serbian, Polish). If none of the allowed languages
    have non-zero probability, defaults to 'uk'.

    Args:
        model: Loaded Whisper model instance.
        audio: Path to the audio file (Path or str).
        original_name: Original audio file name used for logging purposes.

    Returns:
        Detected language code, e.g. 'uk' or 'ru'.

    Raises:
        Exception: If language detection fails.

    Note:
        To extend supported languages, update ALLOWED_LANGUAGES constant.
    """
    try:
        audio_loaded = whisper.load_audio(str(audio))
        audio_trimmed = whisper.pad_or_trim(audio_loaded)
        n_mels = model.dims.n_mels
        mel = whisper.log_mel_spectrogram(audio_trimmed, n_mels=n_mels).to(model.device)

        _, probs = model.detect_language(mel)

        allowed_probs = {lang: probs.get(lang, 0) for lang in ALLOWED_LANGUAGES}
        detected_lang = max(allowed_probs, key=allowed_probs.get) if any(allowed_probs.values()) else 'uk'

        logger.info(f'Detected language: {detected_lang} for {original_name}')
        return detected_lang

    except Exception as e:
        logger.error(f'Language detection failed for {original_name}: {e}')
        raise


def transcribe_audio(
        model: whisper.Whisper,
        audio: Path | str,
        original_name: str,
        initial_prompt: str | None = None
) -> str:
    """
    Transcribe audio file to text using Whisper model.

    Automatically detects the spoken language prior to transcription
    (restricted to ALLOWED_LANGUAGES) to prevent misdetection on
    ambiguous or low-quality audio.

    Args:
        model: Whisper model
        audio: Audio that needs to be transcribed. Type: Path or path in str type
        initial_prompt: Initial context promt for Wisper model
        original_name: Original audio file name used for logging purposes.

    Returns:
        Resulting text

    Raises:
        Exception: If transcription fails.
    """
    detected_lang = detect_language(model, audio, original_name)

    carry_initial_prompt = initial_prompt is not None

    try:
        result = model.transcribe(
            str(audio),
            language=detected_lang,
            initial_prompt=initial_prompt,
            carry_initial_prompt=carry_initial_prompt,
            condition_on_previous_text=False,
            no_speech_threshold=0.8,
        )
        logger.info(f'Transcription completed for: {original_name}')
        return result['text']

    except Exception as e:
        logger.error(f'Transcription failed for {original_name}: {e}')
        raise