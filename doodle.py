import logging

from constant import Constant

logger = logging.getLogger('FxStock')


class Doodle:
    def __init__(self, url):
        self.cmds = {'doodle': self.doodle}
        self.desc = {'doodle': 'draw your masterpiece'}
        self.examples = {'doodle': Constant.DOODLE_EXAMPLE}
        self.STATIC_URL = url

    def doodle(self, data):
        if data.get('callback_query_id', -1) != -1:
            data['method'] = 'answerCallbackQuery'
            data['url'] = self.STATIC_URL
            return
        data['method'] = 'sendGame'
        data['game_short_name'] = 'doodle'
        btn_lst = [{'text': 'Draw', 'callback_game': ''}]
        data['reply_markup'] = {"inline_keyboard": [btn_lst]}
