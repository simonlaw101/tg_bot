import logging
import re
from bs4 import BeautifulSoup

from constant import Constant
from service import FbService, HttpService
from util import JsonUtil, NumberUtil

try:
    from db import DB
except ImportError:
    DB = None

try:
    from myemail import Email
except ImportError:
    Email = None

logger = logging.getLogger('FxStock')


class FxStock:
    def __init__(self, db=None, send_email=False, stock_info_lang='en'):
        self.email_service = Email() if send_email else None
        self.stock_info_lang = stock_info_lang
        self.cmds = {'s': self.get_stk,
                     'c': self.get_fx,
                     'i': self.get_idx,
                     'alert': self.alert,
                     'reset': self.reset,
                     'check': self.check,
                     'query': self.query}
        self.desc = {'s': 'get stock price',
                     'c': 'get currency exchange rate',
                     'i': 'get index',
                     'alert': 'view/set alert',
                     'reset': 'clear alert'}
        self.examples = {'s': Constant.S_EXAMPLE,
                         'c': Constant.C_EXAMPLE,
                         'i': Constant.I_EXAMPLE,
                         'alert': Constant.ALERT_EXAMPLE,
                         'reset': Constant.RESET_EXAMPLE}
        self.lambda_mode = type(db) is FbService
        self.db = db if self.lambda_mode else DB()


    # query command
    def query(self, data):
        data['method'] = 'answerInlineQuery'
        code = data['args'].strip().upper()
        if (code.isnumeric() and 0 < len(code) < 5 and int(code) > 0) or\
                code.replace('.', '').replace('-', '').isalnum():
            stock_info = self.get_stock_info(code)
            if len(stock_info) != 0:
                s = {i: stock_info.get(i, 'NA') for i in ['company', 'price', 'change']}
                data['results'] = [{
                                        "type": "article",
                                        "id": "unique",
                                        "title": '{company}'.format(**s),
                                        "description": '{price}    {change}'.format(**s),
                                        "input_message_content": {
                                            "parse_mode": "HTML",
                                            "message_text": '<b><u>{company}</u>\n{price}    {change}</b>'.format(**s)
                                        }
                                    }]
                if code.isnumeric():
                    btn_lst = [{'text': 'View details', "callback_data": "/s " + code}]
                    data['results'][0]["reply_markup"] = {"inline_keyboard": [btn_lst]}

    # s command
    def get_stk(self, data):
        if data.get('callback_query_id', -1) != -1:
            data['method'] = 'editMessageText, answerCallbackQuery'
            data['text'] = self.get_stock_detail(data['args'])
            return
        data['method'] = 'sendMessage'
        code = self.get_stock_code(data)
        if code != '':
            stock_info = self.get_stock_info(code)
            if len(stock_info) == 0 or stock_info.get('price', '') == '':
                data['text'] = 'Please enter a valid stock code.'
            else:
                data['text'] = '<b><u>{}</u>\n{}    {}</b>'.format(stock_info.get('company', 'NA'),
                                                                   stock_info.get('price', 'NA'),
                                                                   stock_info.get('change', 'NA'))
                if code.isnumeric():
                    btn_lst = [{'text': 'View details', "callback_data": "/s " + code}]
                    data['reply_markup'] = {"inline_keyboard": [btn_lst]}

    def get_stock_code(self, data):
        args = data['args'].strip()
        if len(args) == 0:
            return '5'
        if args.isnumeric():
            if len(args) > 4:
                data['text'] = 'Please use the following format.\ne.g. /s 5\ne.g. /s 0005'
                return ''
            elif int(args) == 0:
                data['text'] = '"{}" is not a valid stock code.'.format(args)
                return ''
        elif not (args.replace('.', '').replace('-', '').isalnum()):
            data['text'] = '"{}" is not a valid US stock code.'.format(args)
            return ''
        return args.upper()

    def get_stock_info(self, code):
        code = '{}.HK'.format(code.zfill(4)) if code.isnumeric() else code
        url = 'https://finance.yahoo.com/quote/{}'.format(code)
        url = url + '?region=HK&lang=zh-Hant-HK' if self.stock_info_lang == 'zh' else url
        headers = {'User-Agent': 'Mozilla/5.0 (iPad; CPU OS 12_2 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Mobile/15E148'}
        page = HttpService.get(url, headers)
        soup = BeautifulSoup(page.content, 'html.parser')
        stock_info = {}

        price_ele = soup.find('fin-streamer', {'data-symbol': code, 'data-field': 'regularMarketPrice'})
        if price_ele is None or price_ele.get_text(strip=True) == '':
            logger.error('yahoo finance stock price is not available!')
        else:
            stock_info['price'] = price_ele.get_text(strip=True).replace(',', '')

        company_ele = soup.find('h1', {'class': 'svelte-3a2v0c'})
        if company_ele is None or company_ele.get_text(strip=True) == '':
            logger.error('yahoo finance company name is not available!')
        else:
            company = company_ele.get_text(strip=True)
            company = company[:company.find('(')].strip()
            stock_info['company'] = company

        change_ele = soup.find_all('fin-streamer', {'data-symbol': code, 'class': 'priceChange svelte-mgkamr',
                                                    'data-field': ['regularMarketChange', 'regularMarketChangePercent']})
        if len(change_ele) > 0 and change_ele[0].select_one('span') is not None:
            stock_info['change'] = ' '.join([e.select_one('span').get_text(strip=True) for e in change_ele])
        else:
            logger.error('yahoo finance change is not available!')

        return stock_info

    def get_stock_detail(self, code):
        url = 'http://realtime-money18-cdn.on.cc/securityQuote/genStockDetailHKJSON.php?stockcode={}'
        json_resp = HttpService.cf_get_json(url.format(code.zfill(5)))

        json_obj = JsonUtil.to_json_obj(json_resp)

        change = json_obj.calculation.change
        percent_change = json_obj.calculation.pctChange
        json_obj.change = '+' + str(change) if change > 0 else str(change)
        json_obj.pctChange = '+' + str(percent_change) if percent_change > 0 else str(percent_change)

        json_obj.real.vol = NumberUtil.format_num(json_obj.real.vol)
        json_obj.real.tvr = NumberUtil.format_num(json_obj.real.tvr)
        json_obj.calculation.marketValue = NumberUtil.format_num(json_obj.calculation.marketValue)
        json_obj.daily.issuedShare = NumberUtil.format_num(json_obj.daily.issuedShare)
        json_obj.shortPut.Trade[0].Qty = NumberUtil.format_num(json_obj.shortPut.Trade[0].Qty)
        json_obj.shortPut.Trade[0].Amount = NumberUtil.format_num(json_obj.shortPut.Trade[0].Amount)

        np = float(json_obj.real.np) if NumberUtil.is_float(json_obj.real.np) else 0
        eps = float(json_obj.daily.eps) if NumberUtil.is_float(json_obj.daily.eps) else 0
        lot_size = float(json_obj.daily.lotSize) if NumberUtil.is_float(json_obj.daily.lotSize) else 0
        dividend = float(json_obj.daily.dividend) if NumberUtil.is_float(json_obj.daily.dividend) else 0
        json_obj.peRatio = 0 if eps == 0 else (np / eps)
        json_obj.dividendYield = 0 if np == 0 else (dividend * 100 / np)
        json_obj.minSubscriptionFee = np * lot_size
        json_obj.daily.lotSize = int(lot_size)

        qty_price = json_obj.bulkTrade.Trade[0].Transaction[0].Qty_price
        json_obj.bulkTradeQty = '' if str(qty_price) == '' else qty_price.split('-')[0]
        json_obj.bulkTradePrice = '' if str(qty_price) == '' else qty_price.split('-')[1]

        template = Constant.STK_DETAIL_TEMPLATE_CHI if self.stock_info_lang == 'zh' else Constant.STK_DETAIL_TEMPLATE_ENG
        return template.format(s=json_obj)

    # c command
    def get_fx(self, data):
        if data.get('callback_query_id', -1) != -1:
            data['method'] = 'editMessageText, answerCallbackQuery'
            data['text'] = ''.join(['{} - {}\n'.format(k, v) for k, v in Constant.CCY_DCT.items()])
            return
        data['method'] = 'sendMessage'
        ccy_param = self.get_ccy_param(data)
        if len(ccy_param) != 0:
            current = self.get_xrates(ccy_param[0], ccy_param[1], 1)
            current = 'NA' if current == '-1' else current
            data['text'] = '<b>{} to {}\n{}</b>'.format(ccy_param[0].upper(), ccy_param[1].upper(), current)

    def get_ccy_param(self, data):
        args = data['args'].strip()
        if args == '':
            args = 'jpy'
        elif (' to ' in args and len(args) != 10) or (' to ' not in args and len(args) != 3):
            data['text'] = 'Please use the following format.\ne.g. /c jpy\ne.g. /c jpy to hkd'
            return []

        args = (args + ' to HKD') if len(args) == 3 else args
        ccys = args.split(' to ')
        ccy = ccys[0]
        ccy2 = ccys[1]

        if ccy.upper() not in Constant.CCY_DCT.keys():
            data['text'] = '"{}" is not a valid currency code. Please retry.'.format(ccy)
            btn_lst = [{'text': 'View currency code', "callback_data": "/c"}]
            data['reply_markup'] = {"inline_keyboard": [btn_lst]}
            return []
        if ccy2.upper() not in Constant.CCY_DCT.keys():
            data['text'] = '"{}" is not a valid currency code. Please retry.'.format(ccy2)
            btn_lst = [{'text': 'View currency code', "callback_data": "/c"}]
            data['reply_markup'] = {"inline_keyboard": [btn_lst]}
            return []
        return [ccy, ccy2]

    def get_xrates(self, ccy, ccy2, amount):
        url = 'https://www.x-rates.com/calculator/?from={}&to={}&amount={}'.format(ccy.upper(), ccy2.upper(), amount)
        page = HttpService.get(url)
        soup = BeautifulSoup(page.content, 'html.parser')
        ele = soup.find('span', {'class': 'ccOutputRslt'})
        if ele is None:
            logger.error('xrates is not available!')
            return '-1'
        text = ele.get_text(strip=True).replace(',', '')
        decimal_lst = re.findall('\d+[.]?\d+', text)
        if len(decimal_lst) == 0:
            logger.error('xrates not found in text: {}'.format(text))
            return '-1'
        return decimal_lst[0]

    # i command
    def get_idx(self, data):
        if data.get('callback_query_id', -1) != -1:
            data['method'] = 'editMessageText, answerCallbackQuery'
            data['text'] = ''.join(['{} - {}\n'.format(k, v) for k, v in Constant.IDX_DCT_NO_PREFIX.items()])
            return
        data['method'] = 'sendMessage'
        args = data['args'].strip()
        if args == '':
            idx_info = self.get_idx_info('%5EHSI')
            data['text'] = '<b><u>{}</u>\n{}    {}</b>'.format(idx_info.get('name', 'NA'), idx_info.get('price', 'NA'),
                                                               idx_info.get('change', 'NA'))
        elif args.upper() not in Constant.IDX_DCT_NO_PREFIX.keys():
            data['text'] = '"{}" is not a valid index code. Please retry.'.format(args)
            btn_lst = [{'text': 'View index code', "callback_data": "/i"}]
            data['reply_markup'] = {"inline_keyboard": [btn_lst]}
        else:
            code = args.upper()
            if '%5E' + code in Constant.IDX_DCT.keys():
                code = '%5E' + code
            idx_info = self.get_idx_info(code)
            data['text'] = '<b><u>{}</u>\n{}    {}</b>'.format(idx_info.get('name', 'NA'), idx_info.get('price', 'NA'),
                                                               idx_info.get('change', 'NA'))

    def get_idx_info(self, code):
        url = 'https://finance.yahoo.com/quote/{0}?p={0}'.format(code)
        headers = {'User-Agent': 'Mozilla/5.0 (iPad; CPU OS 12_2 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Mobile/15E148'}
        page = HttpService.get(url, headers)
        soup = BeautifulSoup(page.content, 'html.parser')
        idx_info = {}

        price_ele = soup.find('fin-streamer', {'data-symbol': code.replace('%5E', '^'),
                                               'data-field': 'regularMarketPrice'})
        if price_ele is None or price_ele.get_text(strip=True) == '':
            logger.error('yahoo finance index is not available!')
        else:
            idx_info['price'] = price_ele.get_text(strip=True).replace(',', '')

        name_ele = soup.find('h1', {'class': 'svelte-3a2v0c'})
        if name_ele is None or name_ele.get_text(strip=True) == '':
            logger.error('yahoo finance index name is not available!')
        else:
            name = name_ele.get_text(strip=True)
            name = name[:name.find('(')].strip()
            idx_info['name'] = name

        change_ele = soup.find_all('fin-streamer', {'data-symbol': code.replace('%5E', '^'),
                                                    'data-field': ['regularMarketChange',
                                                                   'regularMarketChangePercent']})
        if len(change_ele) > 0 and change_ele[0].select_one('span') is not None:
            idx_info['change'] = ' '.join([e.select_one('span').get_text(strip=True) for e in change_ele])
        else:
            logger.error('yahoo finance index change is not available!')

        return idx_info

    # alert command
    def alert(self, data):
        args = data['args']
        data['method'] = 'sendMessage'
        if args.strip() == '':
            data['text'] = self.view_alert(data)
            return

        alert_param = self.verify_alert(data)
        if len(alert_param) != 0:
            self.set_alert(data, alert_param)
            data['text'] = self.view_alert(data)

    def view_alert(self, data):
        from_id = data['from_id']
        if self.lambda_mode:
            docs = self.db.query_doc('alert', 'from_id', '==', from_id)
            rows = [(d['from_id'], d['name'], d['types'], d['code'], d['operators'], d['amount'], d['chatid']) for d in docs]
        else:
            sql = 'SELECT * FROM alerts WHERE fromid=?'
            param = (from_id,)
            rows = self.db.execute(sql, param)
        if len(rows) == 0:
            return '<b>No alert set.</b>'
        else:
            msg = ''
            for row in rows:
                current = 'NA'
                types, code, operators, amount = row[2], row[3], row[4], row[5]
                code_text = code

                if types == 'STK':
                    current = self.get_stock_info(code).get('price', 'NA')
                elif types == 'FX':
                    ccy = code.split(':')[0]
                    ccy2 = code.split(':')[1]
                    current = self.get_xrates(ccy, ccy2, 1)
                    current = 'NA' if current == '-1' else current
                    code_text = code_text.replace(':', ' to ')
                elif types == 'IDX':
                    current = self.get_idx_info(code).get('price', 'NA')
                    code_text = code_text.replace('%5E', '')

                msg += '{} {} {}   ({})\n'.format(code_text, operators, amount, current)
            return '<b>' + msg + '</b>'

    def verify_alert(self, data):
        args = data['args'].strip().replace('<', '&lt').replace('>', '&gt')
        err_msg = Constant.ALERT_ERR_MSG

        end_idx = args.find(' ')
        end_idx = len(args) if end_idx < 0 else end_idx
        code = args[:end_idx].upper()

        if code in Constant.CCY_DCT.keys():
            # verify currency
            types = 'FX'
            if len(args) < 5:
                data['text'] = err_msg
                return {}

            if ' to ' not in args:
                args = args[:3] + ' to HKD' + args[3:]

            if '&lt' not in args and '&gt' not in args:
                args = args[:10] + ' &lt' + args[10:]

            ccy = args[:3]
            ccy2 = args[7:10]
            operators = args[11:14]
            amount = args[14:].strip()

            if ccy.upper() not in Constant.CCY_DCT.keys():
                data['text'] = '"{}" is not a valid currency code. Please retry.'.format(ccy)
                return {}
            elif ccy2.upper() not in Constant.CCY_DCT.keys():
                data['text'] = '"{}" is not a valid currency code. Please retry.'.format(ccy2)
                return {}
            code = ccy.upper() + ':' + ccy2.upper()
        elif code in Constant.IDX_DCT_NO_PREFIX.keys():
            # verify index code
            types = 'IDX'
            sym_idx = args.find('&lt')
            sym_idx = args.find('&gt') if sym_idx < 0 else sym_idx
            if sym_idx < 0:
                args = '&lt' + args[end_idx:].strip()
            else:
                args = args[sym_idx:].strip()
            operators = args[:3]
            amount = args[3:].strip()
            if '%5E' + code in Constant.IDX_DCT.keys():
                code = '%5E' + code
        else:
            # verify stock code
            types = 'STK'
            if code.isnumeric():
                if len(code) > 4 or int(code) == 0:
                    data['text'] = '"{}" is not a valid stock code. Please retry.'.format(code)
                    return {}
                code = code.zfill(4)
            elif not (code.replace('.', '').replace('-', '').isalnum()):
                data['text'] = '"{}" is not a valid US stock code. Please retry.'.format(code)
                return {}
            if len(self.get_stock_info(code)) == 0:
                data['text'] = 'Please enter a valid stock code.'
                return {}

            if '&lt' not in args and '&gt' not in args:
                operators = '&lt'
                amount = args[end_idx:].strip()
            else:
                args = args[end_idx:].strip()
                operators = args[:3]
                amount = args[3:].strip()

        if operators not in ['&lt', '&gt']:
            data['text'] = err_msg
            return {}

        if amount.strip() == '':
            data['text'] = 'Please enter an amount.'
            return {}
        elif not (NumberUtil.is_float(amount)) or float(amount) <= 0:
            data['text'] = '"{}" is not a valid amount. Please retry.'.format(amount)
            return {}
        elif len(str(float(amount)).replace('.', '')) > 9:
            data['text'] = 'Maximum length of amount is 9. Please retry.'
            return {}

        return {'types': types,
                'code': code,
                'operators': operators,
                'amount': str(float(amount))}

    def set_alert(self, data, param):
        if self.lambda_mode:
            from_id = data['from_id']
            types = param['types']
            code = param['code']
            operators = param['operators']
            db_data = {'from_id': from_id,
                       'name': data['sender_name'],
                       'types': types,
                       'code': code,
                       'operators': operators,
                       'amount': param['amount'],
                       'chatid': data['chat_id']}
            docs = self.db.compound_query_doc('alert', ('from_id', '==', from_id),
                                                       ('types', '==', types),
                                                       ('code', '==', code),
                                                       ('operators', '==', operators))
            if len(docs) > 0:
                self.db.set_doc('alert', docs[0]['doc_id'], db_data)
            else:
                self.db.add_doc('alert', db_data)
        else:
            sql = 'REPLACE INTO alerts(fromid,name,types,code,operators,amount,chatid) VALUES(?,?,?,?,?,?,?)'
            param = (data['from_id'],
                     data['sender_name'],
                     param['types'],
                     param['code'],
                     param['operators'],
                     param['amount'],
                     data['chat_id'])
            self.db.execute(sql, param)

    # reset command
    def reset(self, data):
        data['method'] = 'sendMessage'
        args = data['args'].strip()
        if args == '':
            data['text'] = self.reset_all(data)
            return
        reset_param = self.verify_reset(data)
        if len(reset_param) != 0:
            data['text'] = self.reset_alert(data, reset_param)

    def reset_all(self, data):
        from_id = data['from_id']
        if self.lambda_mode:
            docs = self.db.query_doc('alert', 'from_id', '==', from_id)
            for doc in docs:
                self.db.delete_doc_by_id('alert', doc['doc_id'])
        else:
            sql = 'DELETE FROM alerts WHERE fromid=?'
            param = (from_id,)
            self.db.execute(sql, param)
        return '<b>Hi {}, you have cleared all alerts.</b>'.format(data.get('sender_name', ''))

    def verify_reset(self, data):
        args = data['args'].strip()
        end_idx = args.find(' ')
        end_idx = len(args) if end_idx < 0 else end_idx
        code = args[:end_idx].upper()
        err_msg = Constant.RESET_ERR_MSG

        if code in Constant.CCY_DCT.keys():
            # verify currency
            types = 'FX'
            if (' to ' not in args and len(args) != 3) or (' to ' in args and len(args) != 10):
                data['text'] = err_msg
                return {}

            if len(args) == 3:
                args = args[:3] + ' to HKD'

            ccy = args[:3]
            ccy2 = args[7:10]

            if ccy.upper() not in Constant.CCY_DCT.keys():
                data['text'] = '"{}" is not a valid currency code. Please retry.'.format(ccy)
                return {}
            elif ccy2.upper() not in Constant.CCY_DCT.keys():
                data['text'] = '"{}" is not a valid currency code. Please retry.'.format(ccy2)
                return {}
            code = ccy.upper() + ':' + ccy2.upper()
        elif code in Constant.IDX_DCT_NO_PREFIX.keys():
            # verify index code
            types = 'IDX'
            if '%5E' + code in Constant.IDX_DCT.keys():
                code = '%5E' + code
        else:
            # verify stock code
            types = 'STK'
            if code.isnumeric():
                if len(code) > 4 or int(code) == 0:
                    data['text'] = '"{}" is not a valid stock code. Please retry.'.format(code)
                    return {}
                code = code.zfill(4)
            elif not (code.replace('.', '').replace('-', '').isalnum()):
                data['text'] = '"{}" is not a valid US stock code. Please retry.'.format(code)
                return {}

        return {'types': types,
                'code': code}

    def reset_alert(self, data, reset_param):
        from_id = data['from_id']
        types = reset_param['types']
        code = reset_param['code']
        param = (from_id, types, code)
        sender_name = data.get('sender_name', '')

        desc = {'STK': 'stock', 'FX': 'exchange rate', 'IDX': 'index'}[types]
        code_text = code

        if types == 'FX':
            code_text = code_text.replace(':', ' to ')
        elif types == 'IDX':
            code_text = code_text.replace('%5E', '')

        if self.lambda_mode:
            rows = self.db.compound_query_doc('alert', ('from_id', '==', from_id),
                                                       ('types', '==', types),
                                                       ('code', '==', code))
        else:
            select_sql = 'SELECT * FROM alerts WHERE fromid=? and types=? and code=?'
            rows = self.db.execute(select_sql, param)
        if len(rows) == 0:
            return '<b>Hi {}, you do not have alerts on {} {}</b>'.format(sender_name, desc, code_text)
        else:
            if self.lambda_mode:
                for doc in rows:
                    self.db.delete_doc_by_id('alert', doc['doc_id'])
            else:
                delete_sql = 'DELETE FROM alerts WHERE fromid=? and types=? and code=?'
                self.db.execute(delete_sql, param)
            return '<b>Hi {}, you have cleared alerts on {} {}</b>'.format(sender_name, desc, code_text)

    # check command
    def check(self, data):
        if self.lambda_mode:
            docs = self.db.get_all_doc('alert')
            rows = [(d['from_id'], d['name'], d['types'], d['code'], d['operators'], d['amount'], d['chatid']) for d in docs]
            doc_ids = [d['doc_id'] for d in docs]
        else:
            select_sql = 'SELECT * FROM alerts'
            rows = self.db.execute(select_sql)
        msgs = []
        for i, row in enumerate(rows):
            from_id, name, types, code, operators, amount, chat_id = row
            amount = float(amount)

            current = -1
            code_text = code

            if types == 'STK':
                current = float(self.get_stock_info(code).get('price', -1))
            elif types == 'FX':
                ccy = code.split(':')[0]
                ccy2 = code.split(':')[1]
                current = float(self.get_xrates(ccy, ccy2, 1))
                code_text = code_text.replace(':', ' to ')
            elif types == 'IDX':
                current = float(self.get_idx_info(code).get('price', -1))
                code_text = code_text.replace('%5E', '')

            if current <= 0:
                continue
            elif (operators == '&lt' and current < amount) or (operators == '&gt' and current > amount):
                logger.info('name: [{}], code: [{}], current: [{}], amount: [{}]'.format(name, code, current, amount))
                msg = {}
                desc = {'STK': 'stock price', 'FX': 'rate', 'IDX': 'index'}[types]
                word = {'&lt': 'lower', '&gt': 'higher'}[operators]
                msg_text = '<b>Hi {},\n{} {} is now {},\n{} than {}</b>'.format(name, code_text, desc, current, word,
                                                                                amount)
                msg['method'] = 'sendMessage'
                msg['text'] = msg_text
                msg['chat_id'] = chat_id
                msgs.append(msg)

                if self.lambda_mode:
                    self.db.delete_doc_by_id('alert', doc_ids[i])
                else:
                    delete_sql = 'DELETE FROM alerts WHERE fromid=? AND types=? AND code=? AND operators=?'
                    param = (from_id, types, code, operators)
                    self.db.execute(delete_sql, param)
                if self.email_service:
                    subject = '{} {} notice to {}'.format(code_text, desc, name)
                    self.email_service.send_email(subject, msg_text)

        if len(msgs) != 0:
            data['method'] = msgs
