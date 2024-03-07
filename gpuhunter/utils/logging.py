import logging
import os.path
import sys
from logging.handlers import TimedRotatingFileHandler

verbose_formatter = logging.Formatter(
    "[%(asctime)s][%(levelname)s][%(name)s][%(filename)s:%(lineno)d]%(message)s"
)
simple_formatter = logging.Formatter(
    fmt="[%(levelname)s][%(asctime)s]%(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)


def get_logger(logger_name, logs_dir):
    logger = logging.getLogger(logger_name)
    logger.setLevel(logging.DEBUG)
    # 屏幕
    stream_handler = logging.StreamHandler(sys.stdout)
    stream_handler.setLevel(logging.INFO)
    stream_handler.setFormatter(simple_formatter)
    logger.addHandler(stream_handler)
    # 文件
    for level, filename in ((logging.DEBUG, "main.log"), (logging.INFO, "output.log")):
        file_handler = TimedRotatingFileHandler(
            filename=os.path.join(logs_dir, filename),
            when="D",
            backupCount=5,
        )
        file_handler.setLevel(level)
        file_handler.setFormatter(verbose_formatter)
        logger.addHandler(file_handler)
    return logger
