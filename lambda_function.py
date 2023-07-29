import configparser
import json
import logging
import sys

from bot import Bot
from cloud import Cloud
from doodle import Doodle
from fxstock import FxStock
from ocr import Ocr
from service import FbService

config = configparser.ConfigParser()
config.read('config.ini')

# Setting
env = 'PROD'

token = config[env]['token']
cloud_db = config[env].getboolean('cloud_db')
cloud_module = config[env].getboolean('cloud_module')
fb = FbService(config[env].get('fb_bucket_name')) if cloud_db or cloud_module else None

modules = []
if config[env].getboolean('fxstock_module'):
    db = fb if cloud_db else None
    modules.append(FxStock(db, config[env].getboolean('send_email'), config[env].get('stock_info_lang')))
if config[env].getboolean('ocr_module'):
    ocr_api_key = config[env].get('ocr_api_key')
    modules.append(Ocr(ocr_api_key) if ocr_api_key else Ocr())
if config[env].getboolean('doodle_module'): modules.append(Doodle(config[env].get('doodle_url')))
if cloud_module: modules.append(Cloud(fb))

logger = logging.getLogger('FxStock')
logger.setLevel(logging.DEBUG)
formatter = logging.Formatter('[%(asctime)s] %(levelname)s [%(module)s.%(funcName)s:%(lineno)d] %(message)s')
stream_handler = logging.StreamHandler()
stream_handler.setFormatter(formatter)
logger.addHandler(stream_handler)

if len(modules) == 0:
    logger.error('Please enable at least one module!')
    sys.exit(0)

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
