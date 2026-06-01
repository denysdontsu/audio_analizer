import json

from dotenv import load_dotenv
from openai import OpenAI

from config.config import OPENAI_MODEL
from src.prompts import get_system_prompt, get_user_prompt

load_dotenv()


client = OpenAI()


def generate_chat_report(dialogue: str) -> dict:
    """
    Generates a structured report from a dialogue using the OpenAI Chat Completions API.

    Args:
        dialogue (str): Raw dialogue text to be analyzed.

    Returns:
        dict: Parsed JSON object containing the generated report.
    """
    chat_messages = [
        {'role': 'system', 'content': get_system_prompt()},
        {'role': 'user', 'content': get_user_prompt(dialogue)},
    ]

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

    return json.loads(generated_text)