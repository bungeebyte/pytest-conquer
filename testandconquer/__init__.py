import logging


__version__ = '1.0'

logger = logging.getLogger(__name__)
logger.addHandler(logging.NullHandler())


def debug_logger():
    logger.setLevel(logging.DEBUG)
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

    sh = logging.StreamHandler()
    sh.setFormatter(formatter)
    logger.addHandler(sh)

    fh = logging.FileHandler('conquer.log')
    fh.setFormatter(formatter)
    logger.addHandler(fh)
