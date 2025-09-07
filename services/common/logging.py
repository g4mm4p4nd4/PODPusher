import sys
from loguru import logger

logger.remove()
logger.add(sys.stdout, serialize=True)

__all__ = ["logger"]
