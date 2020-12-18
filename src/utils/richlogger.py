import logging
from rich.logging import RichHandler
from pathlib import Path

logging.basicConfig(
    level="NOTSET",
    format="%(message)s",
    handlers=[RichHandler(rich_tracebacks=False)]
)

def Logger(str_value):
    path = Path(str_value)
    if path.exists():
        logging.getLogger(path.stem)

    return logging.getLogger(str(str_value))