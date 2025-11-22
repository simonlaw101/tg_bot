import configparser
import json
import logging
import sys

from bot import Bot

config = configparser.ConfigParser()
config.read('config.ini')

# Setting
env = 'PROD'

token = config[env]['token']
cloud_db = config[env].getboolean('cloud_db')
cloud_module = config[env].getboolean('cloud_module')
fb = None

modules = []
if cloud_db or cloud_module:
    from service import FbService
    fb = FbService(config[env].get('fb_bucket_name'))
if config[env].getboolean('fxstock_module'):
    from fxstock import FxStock
    db = fb if cloud_db else None
    modules.append(FxStock(db, config[env].getboolean('send_email'), config[env].get('stock_info_lang')))
if config[env].getboolean('ocr_module'):
    from ocr import Ocr
    ocr_api_key = config[env].get('ocr_api_key')
    modules.append(Ocr(ocr_api_key) if ocr_api_key else Ocr())
if config[env].getboolean('doodle_module'):
    from doodle import Doodle
    modules.append(Doodle(config[env].get('doodle_url')))
if cloud_module:
    from cloud import Cloud
    modules.append(Cloud(fb))
if config[env].getboolean('japanese_module'):
    from japanese import Japanese
    modules.append(Japanese(config[env].get('kanji_api_key'), config[env].get('jpn_module_lang'),
                            config[env].get('translate_api_key')))

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
