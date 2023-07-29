import datetime
import logging
import sched
import time

from service import TgService
from util import ArrayUtil

logger = logging.getLogger('FxStock')


class Bot:
    def __init__(self, token, modules, refresh=0.2):
        self.tg = TgService(token)
        self.bot_tag = '@' + self.tg.get_bot_username()
        self.api = {'sendMessage': self.tg.send_message,
                    'answerCallbackQuery': self.tg.answer_callback_query,
                    'editMessageText': self.tg.edit_message_text,
                    'sendDocument': self.tg.send_document,
                    'sendPhoto': self.tg.send_photo,
                    'sendGame': self.tg.send_game,
                    'answerInlineQuery': self.tg.answer_inline_query,
                    'deleteMessage': self.tg.delete_message}
        self.refresh_time = refresh
        self.check_freq = 10
        self.scheduler = sched.scheduler(time.time, time.sleep)
        self.cmds = {'start': self.send_cmd_list,
                     'help': self.help,
                     'h': self.help,
                     'freq': self.set_freq}
        self.desc = ''
        self.examples = {}
        for module in modules:
            self.cmds.update(module.cmds)
            self.examples.update(module.examples)
            self.desc += ''.join(['/{} - {}\n'.format(k, v) for k, v in module.desc.items()])

        # self.init_bot_commands(modules) # run it once only
        self.start_time = self.get_timestamp(0, 50, 0)  # 00:50
        self.end_time = self.get_timestamp(8, 0, 0)  # 08:00

    def init_bot_commands(self, modules):
        commands = []
        for module in modules:
            for k, v in module.desc.items():
                commands.append({'command': k, 'description': v})
        self.tg.set_my_commands(commands)

    def get_timestamp(self, h, m, s):
        now = datetime.datetime.now()
        sched_time = datetime.datetime(now.year, now.month, now.day, h, m, s)
        if sched_time < now:
            sched_time += datetime.timedelta(days=1)
        return sched_time.timestamp()

    def run(self):
        logger.info('Bot is running...')
        self.scheduler.enter(self.refresh_time, 0, self.check_msg)
        self.scheduler.enter(self.check_freq * 60, 0, self.check_alert)
        # self.scheduler.enterabs(self.start_time, 0, self.start_trade)
        # self.scheduler.enterabs(self.end_time, 0, self.end_trade)
        self.scheduler.run()

    def check_msg(self, new_offset=0):
        all_updates = self.tg.get_updates(new_offset)

        for current_update in all_updates:
            data = self.process_update(current_update)
            new_offset = data['update_id'] + 1
            logger.info('new_offset: [' + str(new_offset) + ']')

        self.scheduler.enter(self.refresh_time, 0, self.check_msg, (new_offset,))

    def check_alert(self):
        self.execute('check', {})
        self.scheduler.enter(self.check_freq * 60, 0, self.check_alert)

    def start_trade(self):
        # self.execute('ma', {'args': 'CODE', 'chat_id': 'CHAT_ID'})   # health check
        self.execute('freq', {'args': '-2'})
        self.scheduler.enter(60 * 60 * 24, 0, self.start_trade)

    def end_trade(self):
        self.execute('freq', {'args': '-10'})
        self.scheduler.enter(60 * 60 * 24, 0, self.end_trade)

    def process_update(self, json_obj):
        data = self.tg.get_data(json_obj)
        message_text = data['message_text']
        if message_text.startswith('/'):
            if self.bot_tag in message_text:
                message_text = message_text.replace(self.bot_tag, '')
            end_idx = len(message_text) if message_text.find(' ') < 0 else message_text.find(' ')
            cmd = message_text[1:end_idx]
            data['args'] = message_text[end_idx + 1:]
            self.execute(cmd, data)
        return data

    def execute(self, cmd, data):
        try:
            if cmd in self.cmds.keys():
                logger.info('command: [{}]'.format(cmd))

                # self.send_maint_msg(data)  # maintenance
                self.cmds[cmd](data)

                methods = data.get('method', '')
                if isinstance(methods, list):
                    for method in methods:
                        self.api.get(method['method'], lambda *args: None)(method)
                else:
                    methods = methods.split(',')
                    for method in methods:
                        self.api.get(method.strip(), lambda *args: None)(data)

        except Exception as e:
            logger.exception('bot execute Exception: ' + str(e))

    def send_cmd_list(self, data):
        data['method'] = 'sendMessage'
        data['text'] = self.desc

    def send_maint_msg(self, data):
        data['method'] = 'sendMessage'
        data['text'] = ('The bot is currently unavailable due to maintenance.\n'
                        'We apologize for any inconvenience caused.')

    def set_freq(self, data):
        args = data['args'].strip()
        if args in ['-2', '-10']:
            self.check_freq = int(args) * -1
        elif args in ['2', '10', '60'] and data.get('callback_query_id', -1) != -1:
            self.check_freq = int(args)
            data['method'] = 'editMessageText, answerCallbackQuery'
            data['text'] = 'Check frequency: {} mins'.format(args)
        else:
            data['method'] = 'sendMessage'
            data['text'] = 'Check frequency: {} mins'.format(self.check_freq)
            btn_lst = [{'text': i, "callback_data": "/freq "+i}
                       for i in ['2', '10', '60'] if str(self.check_freq) != i]
            data['reply_markup'] = {"inline_keyboard": [btn_lst]}

    def help(self, data):
        args = data['args'].strip()
        if args in self.examples.keys() and data.get('callback_query_id', -1) != -1:
            data['method'] = 'editMessageText, answerCallbackQuery'
            data['text'] = self.examples[args]
        else:
            data['method'] = 'sendMessage'
            data['text'] = 'Click and see the examples'
            btn_lst = [{'text': k, "callback_data": "/help "+k}
                       for k in self.examples.keys()]
            data['reply_markup'] = {"inline_keyboard": ArrayUtil.reshape(btn_lst, col=5)}
