import logging
import os

import coloredlogs

# setup logger
ROOT_SOURCE_DIR = os.path.dirname(os.path.abspath(__file__))  # top source directory
LOG_FILE_DIR = os.path.join(ROOT_SOURCE_DIR, "logs")
# LOGGING_FORMAT = "%(name)s - %(levelname)s - %(message)s"
FORMAT = "%(asctime)s %(levelname)-8s [%(filename)s:%(lineno)d] %(message)s"
DATE_FORMAT = "%Y-%m-%d %H:%M:%S"

logging.basicConfig(format=FORMAT, datefmt=DATE_FORMAT, level=logging.INFO)

# create logger
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

coloredlogs.DEFAULT_LOG_FORMAT = os.environ.get("COLOREDLOGS_LOG_FORMAT", FORMAT)
coloredlogs.DEFAULT_DATE_FORMAT = os.environ.get("COLOREDLOGS_DATE_FORMAT", DATE_FORMAT)
coloredlogs.install(level="INFO", logger=logger)

# create console handler and set level to debug
ch = logging.StreamHandler()
ch.setLevel(logging.INFO)

# create formatter
# formatter = logging.Formatter(FORMAT, datefmt=DATE_FORMAT)

# # add formatter to ch
# ch.setFormatter(formatter)

# add ch to logger
logger.addHandler(ch)
