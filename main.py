import datetime
import json
import logging
import sched
import sys
import time
from urllib import request, parse

from fxstock import FxStock
from helper import Helper

#Setting
token = 'YOUR_TOKEN'
refresh_time = 0.2
modules = [FxStock(enabled=True, send_email=False),
           Helper(enabled=True)]

logger = logging.getLogger('FxStock')
logger.setLevel(logging.DEBUG)
formatter = logging.Formatter('[%(asctime)s] %(levelname)s [%(module)s.%(funcName)s:%(lineno)d] %(message)s')
file_handler = logging.FileHandler('log/fxstock.log')
file_handler.setFormatter(formatter)
stream_handler = logging.StreamHandler()
stream_handler.setFormatter(formatter)
logger.addHandler(file_handler)
logger.addHandler(stream_handler)


class Bot:
    def __init__(self, token, refresh_time=0.2):
        self.api_url = "https://api.telegram.org/bot{}/".format(token)
        self.refresh_time = refresh_time
        self.check_freq = 10
        self.scheduler = sched.scheduler(time.time, time.sleep)
        self.cmds = {'start':self.send_cmd_list,
                     'freq':self.set_freq}
        self.desc = ''
        for module in modules:
            if module.enabled:
                self.cmds.update(module.cmds)
                self.desc += ''.join(['/{} - {}\n'.format(k,v) for k,v in module.desc.items()])
        
        self.start_time = self.get_timestamp(0, 50, 0)  #00:50
        self.end_time = self.get_timestamp(8, 0, 0)     #08:00

    def get_timestamp(self, h, m, s):
        now = datetime.datetime.now()
        sched_time = datetime.datetime(now.year, now.month, now.day, h, m, s)
        if sched_time < now:
            sched_time = sched_time.replace(day=now.day+1)
        return sched_time.timestamp()
        
    def run(self):
        logger.info('Bot is running...')
        self.scheduler.enter(self.refresh_time, 0, self.check_msg)
        self.scheduler.enter(self.check_freq*60, 0, self.check_alert)
        #self.scheduler.enterabs(self.start_time, 0, self.start_trade)
        #self.scheduler.enterabs(self.end_time, 0, self.end_trade)
        self.scheduler.run()

    def check_msg(self, new_offset=0):
        all_updates = self.get_updates(new_offset)
        
        for current_update in all_updates:
            
            data = self.get_data(current_update)
            message_text = data['message_text']
            
            if message_text.startswith('/'):
                end_idx = len(message_text) if message_text.find(' ') < 0 else message_text.find(' ')
                cmd = message_text[1:end_idx]
                data['args'] = message_text[end_idx+1:]
                
                self.execute(cmd, data)
            
            new_offset = data['update_id'] + 1
            logger.info('new_offset: ['+str(new_offset)+']')

        self.scheduler.enter(self.refresh_time, 0, self.check_msg, (new_offset,))

    def check_alert(self):
        self.execute('check', {})
        self.scheduler.enter(self.check_freq*60, 0, self.check_alert)

    def start_trade(self):
        #self.execute('ma', {'args':'CODE','chat_id':'CHAT_ID'})   #health check
        self.execute('freq', {'args':'-2'})
        self.scheduler.enter(60*60*24, 0, self.start_trade)
        
    def end_trade(self):
        self.execute('freq', {'args':'-10'})
        self.scheduler.enter(60*60*24, 0, self.end_trade)
        
    def execute(self, cmd, data):
        try:
            if cmd in self.cmds.keys():
                logger.info('command: [{}]'.format(cmd))

                #self.send_maint_msg(data)  #maintenance
                self.cmds[cmd](data)
                
                if data.get('method')=='sendMessage':
                    self.send_message(data)
                elif data.get('method')=='sendMultiMessage':
                    msgs = data.get('msgs',{})
                    for msg in msgs:
                        self.send_message(msg)
                elif data.get('method')=='sendPhoto':
                    self.send_photo(data)
        except Exception as e:
            logger.exception('main execute Exception: '+str(e))
        
    def send_request(self, url, params=None):
        data = None if params is None else parse.urlencode(params).encode()
        req = request.Request(url, data=data)
        try:
            with request.urlopen(req) as resp:
                return json.loads(resp.read())
        except Exception as e:
            #handle urllib.error.HTTPError: HTTP Error 500: Internal Server Error
            logger.error('main send_request Exception: '+str(e))
            return {}
        
    def get_updates(self, offset=0, timeout=30):
        method = 'getUpdates'
        params = {'timeout': timeout, 'offset': offset}
        json_resp = self.send_request(self.api_url + method, params)
        return json_resp.get('result',[])

    def send_message(self, data):
        method = 'sendMessage'
        params = {'chat_id': data['chat_id'], 'text': data['text'], 'parse_mode': 'HTML'}
        self.send_request(self.api_url + method, params)

    def send_photo(self, data):
        method = 'sendPhoto'
        params = {'chat_id': data['chat_id'], 'photo': data['image_url'], 'parse_mode': 'HTML'}
        self.send_request(self.api_url + method, params)
        
    def get_data(self, json_obj):
        message_obj = json_obj.get('message', json_obj.get('edited_message',{}))
        message_text = message_obj.get('text','')
        chat_id = message_obj.get('chat',{}).get('id','')
            
        if 'from' in message_obj:
            from_id = message_obj['from'].get('id','')
            first_name = message_obj['from'].get('first_name','')
            last_name = message_obj['from'].get('last_name','')
            sender_name = first_name+' '+last_name
        else:
            from_id = ''
            sender_name = "unknown"

        return {'update_id': json_obj['update_id'],
                'chat_id': chat_id,
                'from_id': from_id,
                'message_text': message_text,
                'sender_name': sender_name.strip()}
    
    def send_cmd_list(self, data):
        data['method'] = 'sendMessage'
        data['text'] = self.desc

    def send_maint_msg(self, data):
        data['method'] = 'sendMessage'
        data['text'] = 'The bot is currently unavailable due to maintenance.\nWe apologize for any inconvenience caused.'

    def set_freq(self, data):
        args = data['args'].strip()
        if args=='':
            data['method'] = 'sendMessage'
            data['text'] = 'Check frequency: {} mins'.format(self.check_freq)
        elif args in ['-2','-10']:
            self.check_freq = int(args)*-1
        elif args in ['2','10','60']:
            self.check_freq = int(args)
            data['method'] = 'sendMessage'
            data['text'] = 'You have set the check frequency to {} mins'.format(args)
        else:
            data['method'] = 'sendMessage'
            data['text'] = '"{}" is not a valid frequency. We only support 2, 10 and 60'.format(args)

            
def main():
    bot = Bot(token, refresh_time)
    bot.run()

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt as e:
        logger.info('Bot is stopped.')
        logger.debug('main KeyboardInterrupt Exception: '+str(e))
        sys.exit(0)

        
