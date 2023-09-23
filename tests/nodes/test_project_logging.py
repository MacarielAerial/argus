import logging

from gaia.nodes.project_logging import default_logging

logger = logging.getLogger(__name__)


def test_default_logging() -> None:
    default_logging()

    logger.info("Logging module test message")
