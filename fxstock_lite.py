import logging

from constant import Constant
from service import HttpService
from util import JsonUtil

logger = logging.getLogger('FxStock')


class FxStockLite:
    def __init__(self, enabled=True):
        self.enabled = enabled
        self.cmds = {'s': self.get_stk}
        self.desc = {'s': 'get stock price'}
        self.examples = {'s': Constant.S_EXAMPLE}

    # s command
    def get_stk(self, data):
        data['method'] = 'sendMessage'
        code = self.get_stock_code(data)
        if code != '':
            stock_info = self.get_stock_info(code)
            if len(stock_info) == 0:
                data['text'] = 'Please enter a valid stock code.'
            else:
                data['text'] = ('<b><u>{s.daily.name}</u>\n'
                                '{s.real.np}    {s.change} ({s.pctChange}%)</b>').format(s=stock_info)

    def get_stock_code(self, data):
        args = data['args'].strip()
        if len(args) == 0 or len(args) > 4:
            data['text'] = 'Please use the following format.\ne.g. /s 5\ne.g. /s 0005'
            return ''
        elif not (args.isnumeric()) or int(args) == 0:
            data['text'] = '"{}" is not a valid stock code.'.format(args)
            return ''
        return args

    def get_stock_info(self, code):
        url = 'http://realtime-money18-cdn.on.cc/securityQuote/genStockDetailHKJSON.php'
        json_resp = HttpService.post_json(url, {'stockcode': code.zfill(5)})

        json_obj = JsonUtil.to_json_obj(json_resp)

        change = json_obj.calculation.change
        percent_change = json_obj.calculation.pctChange
        json_obj.change = '+' + str(change) if change > 0 else str(change)
        json_obj.pctChange = '+' + str(percent_change) if percent_change > 0 else str(percent_change)

        return json_obj
