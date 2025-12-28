import os
import logging
from pathlib import Path
import sys
from enum import Enum

LOG_DIR = '/var/log/app'
LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')

from .logger import configure_logger
logger_listener = configure_logger()

logger = logging.getLogger(__name__)

def get_docker_secret(secret_name: str) -> str | None:
    try:
        return Path(f"/run/secrets/{secret_name}").read_text().strip()
    except Exception:
        return None

# Strategy service connection settings
STRATEGY_HOST = os.getenv('STRATEGY_HOST', 'strategy')
STRATEGY_PORT = int(os.getenv('STRATEGY_PORT', '8238'))

# Tradebot database connection settings
TRADEBOT_DB_USER = os.getenv('TRADEBOT_DB_USER', 'tradebot_user')
TRADEBOT_DB_PASSWORD = os.getenv('TRADEBOT_DB_PASSWORD') or get_docker_secret('crawler_tradebot_db_password') or ''
TRADEBOT_DB_HOST = os.getenv('TRADEBOT_DB_HOST', 'tradebotdb')
TRADEBOT_DB_PORT = int(os.getenv('TRADEBOT_DB_PORT', '5432'))
TRADEBOT_DB_NAME = os.getenv('TRADEBOT_DB_NAME', 'tradebot_db')

FINNHUB_API_KEY = os.getenv('FINNHUB_API_KEY') or get_docker_secret("finnhub_api_key")

PERPLEXITY_SEARCHER_MODEL = os.getenv('PERPLEXITY_SEARCHER_MODEL', 'sonar-pro')
PERPLEXITY_API_KEY = get_docker_secret('perplexity_api_key')
if PERPLEXITY_API_KEY:
    os.environ['PERPLEXITY_API_KEY'] = PERPLEXITY_API_KEY # Perplexity sdk use this envrionment variable

def load_system_prompt(file_path: str) -> str:
    """Load system prompt from a markdown file."""

    # Get absolute path to crawler module directory
    script_path = Path(__file__).resolve()

    # Get the parent directory of the script
    script_directory = script_path.parent
    root = script_directory.parent
    sys.path.insert(0, str(root))
    file_dir = os.path.join(script_directory, file_path)
    try:
        with open(file_dir, 'r', encoding='utf-8') as f:
            return f.read().strip()
    except FileNotFoundError:
        logger.error(f"System prompt file not found: {file_dir}")
        raise
    except Exception as e:
        logger.error(f"Error loading system prompt from {file_path}: {e}")
        raise

PERPLEXITY_SEARCHER_SYSTEM_PROMPT = load_system_prompt('static/prompt/perplexity_search_sys.md')

OPENROUTER_SEARCHER_MODEL = os.getenv('OPENROUTER_SEARCHER_MODEL', '')
OPENROUTER_SEARCHER_SYSTEM_PROMPT = load_system_prompt('static/prompt/openrouter_search_sys.md')
OPENROUTER_BASE_URL = os.getenv('OPENROUTER_BASE_URL', 'https://openrouter.ai/api/v1')
OPENROUTER_API_KEY = os.getenv('OPENROUTER_API_KEY') or get_docker_secret("openrouter_api_key")

# Activated sites configuration
from .const import ArticleSite, FlashNewsSite

def _parse_enum_list[T: Enum](env_var: str, enum_class: type[T]) -> list[T]:
    """Parse comma-separated environment variable into list of enum values (case insensitive)."""
    raw = os.getenv(env_var, '')
    if not raw.strip():
        return []
    result = []
    for item in raw.split(','):
        item = item.strip().upper()
        if item:
            try:
                result.append(enum_class[item])
            except KeyError:
                logger.warning(f"Invalid {enum_class.__name__} value: {item}")
    return result

ACTIVATED_ARTICLE_SITES: list[ArticleSite] = _parse_enum_list('ACTIVATED_ARTICLE_SITES', ArticleSite)
ACTIVATED_FLASH_NEWS_SITES: list[FlashNewsSite] = _parse_enum_list('ACTIVATED_FLASH_NEWS_SITES', FlashNewsSite)

# Server configuration
UVICORN_PORT = int(os.getenv('UVICORN_PORT', 9238))
UVICORN_LOG_LEVEL = os.getenv('UVICORN_LOG_LEVEL', 'info')

# for debug
# class DummyListener:
#     def stop(self):
#         pass

# logger_listener = DummyListener()