import os

from dotenv import load_dotenv


def get_dashscope_api_key() -> str | None:
    """Load and return the DashScope API key from .env."""
    load_dotenv()
    return os.getenv("DASHSCOPE_API_KEY")
