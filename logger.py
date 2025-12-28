import logging
from logging import getLevelName
from logging.handlers import QueueListener, TimedRotatingFileHandler, QueueHandler
from queue import Queue
import sys
import os
from types import TracebackType
from .config import LOG_DIR, LOG_LEVEL

# configure a logger instance, should be called only once
def configure_logger():
    levels = {
        "DEBUG": logging.DEBUG,
        "INFO": logging.INFO,
        "WARNING": logging.WARNING,
        "ERROR": logging.ERROR,
        "CRITICAL": logging.CRITICAL
    }
    lvl = levels.get(LOG_LEVEL.upper(), logging.INFO)
    # Ensure log directory exists
    os.makedirs(LOG_DIR, exist_ok=True)
    
    # create a queue for logging
    log_queue = Queue(-1)
    queue_handler = QueueHandler(log_queue)

    # File handler
    file_handler = TimedRotatingFileHandler(f"{LOG_DIR}/crawler.{getLevelName(lvl).lower()}.log", when="midnight", interval=1, backupCount=36, encoding="utf-8")
    file_handler.setLevel(lvl)
    file_handler.suffix = "%Y-%m-%d"

    # Formatter
    formatter = logging.Formatter('%(asctime)s [%(levelname)s]<Thread-%(thread)d> - %(name)s.%(funcName)s:%(lineno)d - %(message)s')
    file_handler.setFormatter(formatter)

    # configure root logger
    root_logger = logging.getLogger()
    root_logger.addHandler(queue_handler)
    root_logger.setLevel(lvl)

    # Create and start the queue listener
    listener = QueueListener(log_queue, file_handler)
    listener.start()
    
    # Set up exception hook to log uncaught exceptions
    def handle_exception(exc_type: type[BaseException], exc_value: BaseException, exc_traceback: TracebackType | None):
        # Log the exception
        root_logger.error(
            "Uncaught exception:",
            exc_info=(exc_type, exc_value, exc_traceback)
        )

        if issubclass(exc_type, (KeyboardInterrupt, SystemExit)):
            # Let KeyboardInterrupt pass through
            sys.__excepthook__(exc_type, exc_value, exc_traceback)
            return
    
    # Install exception hook
    sys.excepthook = handle_exception

    return listener
