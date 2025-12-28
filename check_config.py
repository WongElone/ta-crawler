from .config import LOG_LEVEL, LOG_DIR, PERPLEXITY_SEARCHER_MODEL, PERPLEXITY_SEARCHER_SYSTEM_PROMPT
from .run import run
import logging

def check_config():
    logger = logging.getLogger(__name__)
    logger.info(f"LOG_LEVEL: {LOG_LEVEL}")
    logger.info(f"LOG_DIR: {LOG_DIR}")
    logger.info(f"PERPLEXITY_SEARCHER_MODEL: {PERPLEXITY_SEARCHER_MODEL}")
    logger.info(f"PERPLEXITY_SEARCHER_SYSTEM_PROMPT: {PERPLEXITY_SEARCHER_SYSTEM_PROMPT}")

if __name__ == "__main__":
    run(check_config)