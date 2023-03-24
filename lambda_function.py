import json
import logging

from bot import Bot
from cloud import Cloud
from doodle import Doodle
from fxstock import FxStock
from ocr import Ocr
from service import FbService

# Setting
token = 'YOUR_TOKEN'
fb = FbService('YOUR_BUCKET_NAME')
modules = [FxStock(fb),
           Ocr(api_key='YOUR_API_KEY'),
           Doodle(url='YOUR_URL'),
           Cloud(fb)]

logger = logging.getLogger('FxStock')
logger.setLevel(logging.DEBUG)
formatter = logging.Formatter('[%(asctime)s] %(levelname)s [%(module)s.%(funcName)s:%(lineno)d] %(message)s')
stream_handler = logging.StreamHandler()
stream_handler.setFormatter(formatter)
logger.addHandler(stream_handler)

bot = Bot(token, modules)


def lambda_handler(event, context):
    if 'body' in event:
        current_update = json.loads(event['body'])
        bot.process_update(current_update)
    else:
        scheduled_cmds = event.get('scheduled_cmds', [])
        for cmd in scheduled_cmds:
            bot.execute(cmd['cmd'], cmd['data'])
    return {'statusCode': 200}
