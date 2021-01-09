import datetime
import logging
import sched
import sys
import time

from logging.handlers import TimedRotatingFileHandler

from fxstock import FxStock
from helper import Helper
from service import TgService

# Setting
refresh_time = 0.2
modules = [FxStock(enabled=True, send_email=False),
           Helper(enabled=True)]

logger = logging.getLogger('FxStock')
logger.setLevel(logging.DEBUG)
formatter = logging.Formatter('[%(asctime)s] %(levelname)s [%(module)s.%(funcName)s:%(lineno)d] %(message)s')
file_handler = TimedRotatingFileHandler('log/fxstock.log', when='d', interval=30, backupCount=3)
file_handler.setFormatter(formatter)
stream_handler = logging.StreamHandler()
stream_handler.setFormatter(formatter)
logger.addHandler(file_handler)
logger.addHandler(stream_handler)


class Bot:
    def __init__(self, refresh=0.2):
        self.refresh_time = refresh
        self.check_freq = 10
        self.scheduler = sched.scheduler(time.time, time.sleep)
        self.cmds = {'start': self.send_cmd_list,
                     'freq': self.set_freq}
        self.desc = ''
        for module in modules:
            if module.enabled:
                self.cmds.update(module.cmds)
                self.desc += ''.join(['/{} - {}\n'.format(k, v) for k, v in module.desc.items()])
        
        self.start_time = self.get_timestamp(0, 50, 0)  # 00:50
        self.end_time = self.get_timestamp(8, 0, 0)     # 08:00

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
        # self.scheduler.enterabs(self.start_time, 0, self.start_trade)
        # self.scheduler.enterabs(self.end_time, 0, self.end_trade)
        self.scheduler.run()

    def check_msg(self, new_offset=0):
        all_updates = TgService.get_updates(new_offset)
        
        for current_update in all_updates:
            
            data = TgService.get_data(current_update)
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
        # self.execute('ma', {'args': 'CODE', 'chat_id': 'CHAT_ID'})   # health check
        self.execute('freq', {'args':'-2'})
        self.scheduler.enter(60*60*24, 0, self.start_trade)
        
    def end_trade(self):
        self.execute('freq', {'args': '-10'})
        self.scheduler.enter(60*60*24, 0, self.end_trade)
        
    def execute(self, cmd, data):
        try:
            if cmd in self.cmds.keys():
                logger.info('command: [{}]'.format(cmd))

                # self.send_maint_msg(data)  #maintenance
                self.cmds[cmd](data)
                
                if data.get('method') == 'sendMessage':
                    TgService.send_message(data)
                elif data.get('method') == 'sendMultiMessage':
                    msgs = data.get('msgs', {})
                    for msg in msgs:
                        TgService.send_message(msg)
                elif data.get('method') == 'sendPhoto':
                    TgService.send_photo(data)
        except Exception as e:
            logger.exception('main execute Exception: '+str(e))

    def send_cmd_list(self, data):
        data['method'] = 'sendMessage'
        data['text'] = self.desc

    def send_maint_msg(self, data):
        data['method'] = 'sendMessage'
        data['text'] = ('The bot is currently unavailable due to maintenance.\n'
                        'We apologize for any inconvenience caused.')

    def set_freq(self, data):
        args = data['args'].strip()
        if args == '':
            data['method'] = 'sendMessage'
            data['text'] = 'Check frequency: {} mins'.format(self.check_freq)
        elif args in ['-2', '-10']:
            self.check_freq = int(args)*-1
        elif args in ['2', '10', '60']:
            self.check_freq = int(args)
            data['method'] = 'sendMessage'
            data['text'] = 'You have set the check frequency to {} mins'.format(args)
        else:
            data['method'] = 'sendMessage'
            data['text'] = '"{}" is not a valid frequency. We only support 2, 10 and 60'.format(args)

            
def main():
    bot = Bot(refresh_time)
    bot.run()


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt as ke:
        logger.info('Bot is stopped.')
        logger.debug('main KeyboardInterrupt Exception: '+str(ke))
        sys.exit(0)
