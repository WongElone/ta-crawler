import signal
import time
from typing import Callable

from . import logger_listener
import logging
log = logging.getLogger(__name__)


def start_wait_stop_runner(
    start_callback: Callable[[], None],
    stop_callback: Callable[[], None],
    name: str):
    """
    Start a runner and wait for it to finish.
    
    Args:
        start_callback: should run infinitely until stop_callback is called.
        stop_callback: should stop the runner.
        name: Name of the runner.
    """
    try:
        def signal_handler(sig, frame):
            log.info(f"=== Graceful termination signal {sig} received for {name}, triggering stop_callback...")
            stop_callback()
            log.info(f"=== {name} stop callback finished ===")
        signal.signal(signal.SIGTERM, signal_handler)  # Handle termination signal
        signal.signal(signal.SIGINT, signal_handler)  # Handle termination signal
        log.info(f"=== starting {name}... ===")
        start_callback()
        log.info(f"=== {name} ended ===")
    except KeyboardInterrupt:
        log.info(f"=== KeyboardInterrupt, stopping {name}...")
        stop_callback()
        log.info(f"=== {name} stopped ===")
    except SystemExit:
        log.info(f"=== SystemExit, stopping {name}...")
        stop_callback()
        log.info(f"=== {name} stopped ===")
    except Exception as e:
        log.error(f"=== {name} on ERROR: {e}", exc_info=True)
        stop_callback()
        log.info(f"=== {name} stopped on ERROR ===")
    finally:
        log.info("=== shutting down... ===")
        time.sleep(1)
        logger_listener.stop()

def run(callback: Callable[[], None]):
    try:
        log.info(f"=== starting {callback.__name__}... ===")
        callback()
    except Exception as e:
        log.error(f"=== on ERROR: {e}", exc_info=True)
    finally:
        log.info(f"=== shutting down {callback.__name__}... ===")
        time.sleep(1)
        logger_listener.stop()
