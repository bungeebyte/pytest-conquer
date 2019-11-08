import logging

__version__ = '1.0'

logger = logging.getLogger(__name__)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')


# log warnings by default
logger.setLevel(logging.WARNING)
sh = logging.StreamHandler()
sh.setFormatter(formatter)
logger.addHandler(sh)


def debug_logger():
    logger.setLevel(logging.DEBUG)

    fh = logging.FileHandler('conquer.log')
    fh.setFormatter(formatter)
    logger.addHandler(fh)
