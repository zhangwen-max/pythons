import os

from dotenv import load_dotenv


load_dotenv()


MODEL_NAME = os.getenv("DSZNZS_MODEL", "deepseek-chat")
OPENAI_BASE_URL = os.getenv("DSZNZS_BASE_URL", "https://api.deepseek.com")
API_KEY_ENV = os.getenv("DSZNZS_API_KEY_ENV", "DEEPSEEK_API_KEY")
API_KEY = os.getenv(API_KEY_ENV)

CHAT_TEMPERATURE = float(os.getenv("DSZNZS_CHAT_TEMPERATURE", "0.3"))
INTENT_TEMPERATURE = float(os.getenv("DSZNZS_INTENT_TEMPERATURE", "0.0"))

CONFIDENCE_THRESHOLD = float(os.getenv("DSZNZS_CONFIDENCE_THRESHOLD", "0.55"))
HUMAN_TRANSFER_THRESHOLD = float(os.getenv("DSZNZS_HUMAN_TRANSFER_THRESHOLD", "0.25"))

PROMPT_VERSION = os.getenv("DSZNZS_PROMPT_VERSION", "ecommerce-v1")
TRACE_ENABLED = os.getenv("DSZNZS_TRACE_ENABLED", "true").lower() == "true"
MEMORY_WINDOW_SIZE = int(os.getenv("DSZNZS_MEMORY_WINDOW_SIZE", "6"))

