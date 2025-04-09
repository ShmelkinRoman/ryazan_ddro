import logging
from logging.handlers import RotatingFileHandler


def get_logger(module_name: str) -> logging.Logger:
    logger = logging.getLogger(module_name)
    logger.setLevel(logging.INFO)
    handler = RotatingFileHandler(
        'ryazan_ddro.log', maxBytes=50000000, backupCount=5)
    logger.addHandler(handler)

    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    handler.setFormatter(formatter)
    return logger