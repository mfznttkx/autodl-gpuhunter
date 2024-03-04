import logging
import sys
from logging.handlers import TimedRotatingFileHandler

verbose_formatter = logging.Formatter(
    "[%(asctime)s][%(levelname)s][%(name)s][%(filename)s:%(lineno)d]%(message)s"
)
simple_formatter = logging.Formatter(
    fmt="[%(levelname)s][%(asctime)s]%(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)


def get_logger(logger_name, file_name):
    logger = logging.getLogger(logger_name)
    logger.setLevel(logging.DEBUG)

    stream_handler = logging.StreamHandler(sys.stdout)
    stream_handler.setLevel(logging.DEBUG)
    stream_handler.setFormatter(verbose_formatter)

    file_handler = TimedRotatingFileHandler(
        filename=file_name,
        when="D",
        backupCount=5,
    )
    file_handler.setLevel(logging.INFO)
    file_handler.setFormatter(simple_formatter)

    logger.addHandler(stream_handler)
    logger.addHandler(file_handler)
    return logger
