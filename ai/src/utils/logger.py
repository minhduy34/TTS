import logging
import sys
from datetime import date
from pathlib import Path

LOGS_DIR = Path(__file__).parent / "logs"

_loggers: dict[str, logging.Logger] = {}


def get_logger(session_id: str) -> logging.Logger:
    if session_id in _loggers:
        return _loggers[session_id]

    today = date.today().isoformat()
    log_dir = LOGS_DIR / today
    log_dir.mkdir(parents=True, exist_ok=True)
    log_file = log_dir / f"{session_id}.log"

    logger = logging.getLogger(session_id)
    logger.setLevel(logging.DEBUG)

    if not logger.handlers:
        fmt = logging.Formatter("%(asctime)s %(levelname)s %(message)s")

        fh = logging.FileHandler(log_file, encoding="utf-8")
        fh.setFormatter(fmt)
        logger.addHandler(fh)

        sh = logging.StreamHandler(sys.stdout)
        sh.setFormatter(fmt)
        logger.addHandler(sh)

    _loggers[session_id] = logger
    return logger
