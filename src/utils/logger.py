import logging.config
import os

logger_config = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "simpleFormater": {
            "format": "%(asctime)s.%(msecs)03d - %(levelname)7s: %(name)10s: %(message)s",
            "datefmt": "%Y-%m-%d %H:%M:%S"
        }
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "simpleFormater",
            "level": "INFO"
        },
        "log_file_handler": {
            "class": "logging.handlers.TimedRotatingFileHandler",
            "level": "INFO",
            "formatter": "simpleFormater",
            "when": "d",
            "interval": 1,
            "backupCount": 5,
            "encoding": "utf8"
        }
    },
    "root": {
        "level": "INFO",
        "handlers": [
            "console",
            "log_file_handler"
        ]
    }
}


def config_logger(log_dir):
    # config logger
    filename = os.path.join(log_dir, 'master.log')
    logger_config['handlers']['log_file_handler']['filename'] = filename
    os.makedirs(os.path.dirname(filename), exist_ok=True)
    logging.config.dictConfig(logger_config)
