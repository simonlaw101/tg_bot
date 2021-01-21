import json
import logging

from bot import Bot
from fxstock import FxStock
from ocr import Ocr

# Setting
modules = [FxStock(lambda_mode=True),
           Ocr()]

logger = logging.getLogger('FxStock')
logger.setLevel(logging.DEBUG)
formatter = logging.Formatter('[%(asctime)s] %(levelname)s [%(module)s.%(funcName)s:%(lineno)d] %(message)s')
stream_handler = logging.StreamHandler()
stream_handler.setFormatter(formatter)
logger.addHandler(stream_handler)

bot = Bot(modules)


def lambda_handler(event, context):
    current_update = json.loads(event['body'])
    bot.process_update(current_update)
    return {'statusCode': 200}
