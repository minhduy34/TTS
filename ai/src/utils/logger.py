from collections import OrderedDict
import logging
import sys
from datetime import date
from pathlib import Path

LOGS_DIR = Path(__file__).parent / "logs"
MAX_LOGGERS = 500

_loggers: OrderedDict[tuple[str, str], logging.Logger] = OrderedDict()


def get_logger(session_id: str) -> logging.Logger:
    today = date.today().isoformat()
    key = (session_id, today)
    if key in _loggers:
        return _loggers[key]

    if len(_loggers) >= MAX_LOGGERS:
        _, old_logger = _loggers.popitem(last=False)
        for h in old_logger.handlers[:]:
            h.close()
            old_logger.removeHandler(h)

    log_dir = LOGS_DIR / today
    log_dir.mkdir(parents=True, exist_ok=True)
    log_file = log_dir / f"{session_id}.log"

    logger = logging.getLogger(f"{session_id}.{today}")
    logger.setLevel(logging.DEBUG)

    if not logger.handlers:
        fmt = logging.Formatter("%(asctime)s %(levelname)s %(message)s")
        fh = logging.FileHandler(log_file, encoding="utf-8")
        fh.setFormatter(fmt)
        logger.addHandler(fh)
        sh = logging.StreamHandler(sys.stdout)
        sh.setFormatter(fmt)
        logger.addHandler(sh)

    _loggers[key] = logger
    return logger
