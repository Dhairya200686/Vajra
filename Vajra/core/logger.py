# VAJRA — Centralised logging. Configure once here, use everywhere.

import logging
import sys
from core.config import BASE_DIR

LOG_FILE    = BASE_DIR / "vajra.log"
_configured = False


def setup_logger(verbose: bool = False) -> logging.Logger:
    global _configured
    logger = logging.getLogger("vajra")
    logger.setLevel(logging.DEBUG)

    if not _configured:
        fh = logging.FileHandler(LOG_FILE, encoding="utf-8")
        fh.setLevel(logging.DEBUG)
        fh.setFormatter(logging.Formatter(
            "%(asctime)s [%(levelname)s] %(module)s: %(message)s"
        ))
        logger.addHandler(fh)

        ch = logging.StreamHandler(sys.stderr)
        ch.setLevel(logging.DEBUG if verbose else logging.WARNING)
        ch.setFormatter(logging.Formatter("[%(levelname)s] %(message)s"))
        logger.addHandler(ch)
        _configured = True

    return logger


def get_logger(name: str = "vajra") -> logging.Logger:
    return logging.getLogger(name)
