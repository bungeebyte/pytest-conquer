import logging

__version__ = '1.0'

logger = logging.getLogger(__name__)
formatter = logging.Formatter('%(asctime)s %(levelname)s [%(name)s|%(filename)s:%(lineno)d] %(message)s')


# log warnings by default
logger.setLevel(logging.INFO)
sh = logging.StreamHandler()
sh.setFormatter(formatter)
logger.addHandler(sh)

fh = logging.FileHandler('conquer.log')
fh.setFormatter(formatter)
logger.addHandler(fh)


def debug_logger():
    logger.setLevel(logging.DEBUG)

    fh = logging.FileHandler('conquer.log')
    fh.setFormatter(formatter)
    logger.addHandler(fh)
