# core/prompts.py
import os

PROMPTS_DIR = os.path.abspath(os.path.join(
    os.path.dirname(__file__), '..', 'prompts'))


def load_prompt(name: str) -> str:
    """
    Loads a prompt from the /prompts directory.
    Args:
        name: The name of the prompt file (without the .md extension).
    Returns:
        The content of the prompt file as a string.
    """
    prompt_path = os.path.join(PROMPTS_DIR, f"{name}.md")
    try:
        with open(prompt_path, "r", encoding="utf-8") as f:
            return f.read()
    except FileNotFoundError:
        raise FileNotFoundError(f"Prompt file not found at: {prompt_path}")
