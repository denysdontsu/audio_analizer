import json
import logging

from dotenv import load_dotenv
from openai import OpenAI, OpenAIError

from config.config import OPENAI_MODEL
from src.prompts import get_system_prompt, get_user_prompt

load_dotenv()
client = OpenAI()
logger = logging.getLogger(__name__)


def generate_chat_report(dialogue: str) -> dict:
    """
    Generates a structured report from a dialogue using the OpenAI Chat Completions API.

    Args:
        dialogue (str): Raw dialogue text to be analyzed.

    Returns:
        dict: Parsed JSON object containing the generated report.

    Raises:
        OpenAIError: If the API request fails.
        json.JSONDecodeError: If the response cannot be parsed as JSON.
    """
    chat_messages = [
        {'role': 'system', 'content': get_system_prompt()},
        {'role': 'user', 'content': get_user_prompt(dialogue)},
    ]

    try:
        response = client.chat.completions.create(
            # input prompt
            messages=chat_messages,
            # model parameters
            model=OPENAI_MODEL,
            response_format={"type": "json_object"},
            temperature=0.0,  # keep low for conservative answers
            max_tokens=1536
        )
        generated_text = response.choices[0].message.content
        logger.info('Successfully generated chat report')
        return json.loads(generated_text)

    except OpenAIError as e:
        logger.error(f'OpenAI API request failed: {e}')
        raise
    except json.JSONDecodeError as e:
        logger.error(f'Failed to parse OpenAI response as JSON: {e}')
        raise