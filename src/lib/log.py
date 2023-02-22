"""Log"""
import logging
import sys

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s %(levelname)-2s: %(message)s"
)

logger = logging.getLogger(__name__)


def debug(msg: str, level=logging.DEBUG):
    """Debug"""
    logger.log(level, msg)


def info(msg: str, level=logging.INFO):
    """Info"""
    logger.log(level, msg)


def warn(msg: str, level=logging.WARNING):
    """Warning"""
    logger.log(level, msg)


def error(msg: str, level=logging.ERROR):
    """Error"""
    logger.log(level, msg)
    sys.exit(1)
