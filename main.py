import logging
import sys

from logging.handlers import TimedRotatingFileHandler

from bot import Bot
from fxstock import FxStock
from ocr import Ocr

# Setting
refresh_time = 0.2
modules = [FxStock(enabled=True, send_email=False),
           Ocr(enabled=False)]

logger = logging.getLogger('FxStock')
logger.setLevel(logging.DEBUG)
formatter = logging.Formatter('[%(asctime)s] %(levelname)s [%(module)s.%(funcName)s:%(lineno)d] %(message)s')
file_handler = TimedRotatingFileHandler('log/fxstock.log', when='d', interval=30, backupCount=3)
file_handler.setFormatter(formatter)
stream_handler = logging.StreamHandler()
stream_handler.setFormatter(formatter)
logger.addHandler(file_handler)
logger.addHandler(stream_handler)


def main():
    bot = Bot(modules, refresh_time)
    bot.run()


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt as ke:
        logger.info('Bot is stopped.')
        logger.debug('main KeyboardInterrupt Exception: '+str(ke))
        sys.exit(0)
