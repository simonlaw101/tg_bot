import logging
import requests
from bs4 import BeautifulSoup

from db import DB
from myemail import Email
from service import HttpService
from util import JsonUtil, NumberUtil

logger = logging.getLogger('FxStock')

class FxStock:
    def __init__(self, enabled=True, send_email=False):
        self.enabled = enabled
        self.email_service = Email() if send_email else None
        self.cmds = {'s':self.get_stk,
                     'c':self.get_fx,
                     'i':self.get_idx,
                     'alert':self.alert,
                     'reset':self.reset,
                     'ccy':self.get_ccy,
                     'idx':self.get_idx_lst,
                     'check':self.check,
                     'us':self.get_us_stk,
                     'ma':self.get_ma,
                     'rsi':self.get_rsi}
        self.desc = {'s': 'get stock price',
                     'c': 'get currency exchange rate',
                     'i': 'get index',
                     'alert': 'view/set alert',
                     'reset': 'clear alert',
                     'ccy': 'search currency code',
                     'idx': 'search index symbol',
                     'us': 'get us stock price',
                     'ma': 'get stock moving average',
                     'rsi': 'get stock relative strength index'}
        self.db = DB()
        self.ccy_dct = self.get_ccy_dct()
        self.ccy_lst = ''.join(['{} - {}\n'.format(k,v) for k,v in self.ccy_dct.items()])
        self.idx_dct = self.get_idx_dct()
        self.idx_dct_no_prefix = {k.replace('%5E',''):v for k,v in self.idx_dct.items()}
        self.idx_lst = ''.join(['{} - {}\n'.format(k,v) for k,v in self.idx_dct_no_prefix.items()])

    def send_request(self, url, headers=None):
        try:
            return requests.get(url,headers=headers)
        except Exception as e:
            logger.exception('fxstock send_request Exception: '+str(e))
            return None
        
    #s command
    def get_stk(self, data):
        data['method'] = 'sendMessage'
        code = self.get_stock_code(data)
        if code!='':
            stock_info = self.get_stock_info(code)
            if len(stock_info)==0:
                data['text'] = 'Please enter a valid stock code.'
            else:
                data['text'] =  '<b><u>{}</u>\n{}    {}</b>'.format(stock_info.get('company','NA'),
                                                                    stock_info.get('price','NA'),
                                                                    stock_info.get('change','NA'))
   
    def get_stock_code(self, data):
        args = data['args'].strip()
        if len(args)==0 or len(args)>4:
            data['text'] = 'Please use the following format.\ne.g. /s 5\ne.g. /s 0005'
            return ''
        elif not(args.isnumeric()) or int(args)==0:
            data['text'] = '"{}" is not a valid stock code.'.format(args)
            return ''        
        return args
    
    def get_stock_info(self, code):
        url = 'https://finance.yahoo.com/quote/{}.HK/'.format(code.zfill(4))
        headers = {'User-Agent':''}
        page = HttpService.get(url, headers)
        soup = BeautifulSoup(page.content, 'html.parser')
        stock_info = {}

        price_ele = soup.find('span',{'class':'Trsdu(0.3s) Fw(b) Fz(36px) Mb(-4px) D(ib)'})
        if price_ele is None or price_ele.get_text(strip=True)=='':
            logger.error('yahoo finance stock price is not available!')
        else:
            stock_info['price'] = price_ele.get_text(strip=True).replace(',','')

        company_ele = soup.find('h1',{'class':'D(ib) Fz(18px)'})
        if company_ele is None or company_ele.get_text(strip=True)=='':
            logger.error('yahoo finance company name is not available!')
        else:
            company = company_ele.get_text(strip=True)
            company = company[:company.find('(')].strip()
            stock_info['company'] = company

        change_ele = soup.find_all('span',{'class':['Trsdu(0.3s) Fw(500) Pstart(10px) Fz(24px) C($negativeColor)',
                                                    'Trsdu(0.3s) Fw(500) Pstart(10px) Fz(24px) C($positiveColor)',
                                                    'Trsdu(0.3s) Fw(500) Pstart(10px) Fz(24px)']})
        if change_ele is None or len(change_ele)==0 or change_ele[0].get_text(strip=True)=='':
            logger.error('yahoo finance change is not available!')
        else:
            stock_info['change'] = change_ele[0].get_text(strip=True)
        
        return stock_info
    
    #c command
    def get_fx(self, data):
        data['method'] = 'sendMessage'
        ccy_param = self.get_ccy_param(data)
        if len(ccy_param)!=0:
            current = self.get_xrates(ccy_param[0],ccy_param[1],1)
            current = 'NA' if current=='-1' else current
            data['text'] =  '<b>{}</b>'.format(current)
   
    def get_ccy_param(self, data):
        args = data['args'].strip()
        if (' to ' in args and len(args)!=10) or (' to ' not in args and len(args)!=3):
            data['text'] = 'Please use the following format.\ne.g. /c jpy\ne.g. /c jpy to hkd'
            return []

        args = (args+' to HKD') if len(args)==3 else args
        ccys = args.split(' to ')
        ccy = ccys[0]
        ccy2 = ccys[1]
        
        if ccy.upper() not in self.ccy_dct.keys():
            data['text'] = '"{}" is not a valid currency code. Please retry.'.format(ccy)
            return []
        if ccy2.upper() not in self.ccy_dct.keys():
            data['text'] = '"{}" is not a valid currency code. Please retry.'.format(ccy2)
            return []  
        return [ccy, ccy2]

    def get_xrates(self, ccy, ccy2, amount):
        url = 'https://www.x-rates.com/calculator/?from={}&to={}&amount={}'.format(ccy.upper(),ccy2.upper(),amount)
        page = HttpService.get(url)
        soup = BeautifulSoup(page.content, 'html.parser')
        ele = soup.find('span',{'class':'ccOutputTrail'})
        if ele is None:
            logger.error('xrates is not available!')
            return '-1'
        return ele.previous_sibling.replace(',','') + ele.get_text(strip=True)

    #i command
    def get_idx(self, data):
        data['method'] = 'sendMessage'
        args = data['args'].strip()
        if args=='':
            idx_info = self.get_idx_info('%5EHSI')
            data['text'] =  '<b><u>{}</u>\n{}    {}</b>'.format(idx_info.get('name','NA'), idx_info.get('price','NA'), idx_info.get('change','NA'))
        elif args.upper() not in self.idx_dct_no_prefix.keys():
            data['text'] = '"{}" is not a valid index code. Please retry.'.format(args)
        else:
            code = args.upper()
            if '%5E'+code in self.idx_dct.keys():
                code = '%5E'+code
            idx_info = self.get_idx_info(code)
            data['text'] =  '<b><u>{}</u>\n{}    {}</b>'.format(idx_info.get('name','NA'), idx_info.get('price','NA'), idx_info.get('change','NA'))
    
    def get_idx_info(self, code):
        url = 'https://finance.yahoo.com/quote/{0}?p={0}'.format(code)
        headers = {'User-Agent':''}
        page = HttpService.get(url, headers)
        soup = BeautifulSoup(page.content, 'html.parser')
        idx_info = {}

        price_ele = soup.find('span',{'class':'Trsdu(0.3s) Fw(b) Fz(36px) Mb(-4px) D(ib)'})
        if price_ele is None or price_ele.get_text(strip=True)=='':
            logger.error('yahoo finance index is not available!')
        else:
            idx_info['price'] = price_ele.get_text(strip=True).replace(',','')

        name_ele = soup.find('h1',{'class':'D(ib) Fz(18px)'})
        if name_ele is None or name_ele.get_text(strip=True)=='':
            logger.error('yahoo finance index name is not available!')
        else:
            name = name_ele.get_text(strip=True)
            name = name[:name.find('(')].strip()
            idx_info['name'] = name
        
        change_ele = soup.find_all('span',{'class':['Trsdu(0.3s) Fw(500) Pstart(10px) Fz(24px) C($negativeColor)',
                                                    'Trsdu(0.3s) Fw(500) Pstart(10px) Fz(24px) C($positiveColor)',
                                                    'Trsdu(0.3s) Fw(500) Pstart(10px) Fz(24px)']})
        if change_ele is None or len(change_ele)==0 or change_ele[0].get_text(strip=True)=='':
            logger.error('yahoo finance index change is not available!')
        else:
            idx_info['change'] = change_ele[0].get_text(strip=True)

        return idx_info
        
    #alert command
    def alert(self, data):
        args = data['args']
        data['method'] = 'sendMessage'
        if args.strip()=='':
            data['text'] = self.view_alert(data)
            return

        alert_param = self.verify_alert(data)
        if len(alert_param)!=0:
            self.set_alert(data, alert_param)
            data['text'] =  self.view_alert(data)

    def view_alert(self, data):
        from_id = data['from_id']
        sql = 'SELECT * FROM alerts WHERE fromid=?'
        param = (from_id,)
        rows = self.db.execute(sql, param)
        if len(rows)==0:
            return '<b>No alert set.</b>'
        else:
            msg = ''
            for row in rows:
                types, code, operators, amount = row[2], row[3], row[4], row[5]
                code_text = code
                
                if types=='STK':
                    current = self.get_stock_info(code).get('price','NA')
                elif types=='FX':
                    ccy = code.split(':')[0]
                    ccy2 = code.split(':')[1]
                    current = self.get_xrates(ccy, ccy2, 1)
                    current = 'NA' if current=='-1' else current
                    code_text = code_text.replace(':',' to ')
                elif types=='IDX':
                    current = self.get_idx_info(code).get('price','NA')
                    code_text = code_text.replace('%5E','')
                    
                msg += '{} {} {}   ({})\n'.format(code_text, operators, amount, current)
            return '<b>'+msg+'</b>'

    def verify_alert(self, data):
        args = data['args'].strip().replace('<','&lt').replace('>','&gt')
        err_msg = ('Please use the following format.\n'
                   'For stock:\n'
                   'e.g. /alert 5 50\n'
                   'e.g. /alert 0005 &gt50\n\n'
                   'For exchange rate:\n'
                   'e.g. /alert jpy 0.07\n'
                   'e.g. /alert aud &lt5\n'
                   'e.g. /alert jpy to hkd 0.07\n'
                   'e.g. /alert twd to hkd &gt3.8\n\n'
                   'For index:\n'
                   'e.g. /alert hsi 25000\n'
                   'e.g. /alert hsi &lt25000\n'
                   'e.g. /alert hsi &gt28000')

        types = ''
        code = ''
        operators = ''
        amount = ''

        end_idx = args.find(' ')
        end_idx = len(args) if end_idx<0 else end_idx
        code = args[:end_idx].upper()
        
        if code in self.idx_dct_no_prefix.keys():
            #verify index code
            types = 'IDX'
            sym_idx = args.find('&lt')
            sym_idx = args.find('&gt') if sym_idx<0 else sym_idx
            if sym_idx<0:
                args = '&lt'+args[end_idx:].strip()
            else:
                args = args[sym_idx:].strip()
            operators = args[:3]
            amount = args[3:].strip()
            if '%5E'+code in self.idx_dct.keys():
                code = '%5E'+code
        elif args[0].isnumeric():
            #verify stock code
            types = 'STK'
            if len(code)>4 or not(code.isnumeric()) or\
               int(code)==0 or len(self.get_stock_info(code))==0:
                data['text'] = '"{}" is not a valid stock code. Please retry.'.format(code)
                return {}
            code = code.zfill(4)
            if '&lt' not in args and '&gt' not in args:
                args = code+'&lt'+args[end_idx:].strip()
            else:
                args = code+args[end_idx:].strip()
            operators = args[4:7]
            amount = args[7:].strip()
        else:
            #verify currency
            types = 'FX'
            if len(args)<5:
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
       
            if ccy.upper() not in self.ccy_dct.keys():
                data['text'] = '"{}" is not a valid currency code. Please retry.'.format(ccy)
                return {}
            elif ccy2.upper() not in self.ccy_dct.keys():
                data['text'] = '"{}" is not a valid currency code. Please retry.'.format(ccy2)
                return {}
            code = ccy.upper()+':'+ccy2.upper()
        
        if operators not in ['&lt','&gt']:
            data['text'] = err_msg
            return {}

        if amount.strip()=='':
            data['text'] = 'Please enter an amount.'
            return {}
        elif not(NumberUtil.is_float(amount)) or float(amount)<=0:
            data['text'] = '"{}" is not a valid amount. Please retry.'.format(amount)
            return {}
        elif len(str(float(amount)).replace('.',''))>9:
            data['text'] = 'Maximum length of amount is 9. Please retry.'
            return {}            
        
        return {'types': types,
                'code': code,
                'operators': operators,
                'amount': str(float(amount))}

    def set_alert(self, data, param):
        sql = 'REPLACE INTO alerts(fromid,name,types,code,operators,amount,chatid) VALUES(?,?,?,?,?,?,?)'
        param = (data['from_id'],
                 data['sender_name'],
                 param['types'],
                 param['code'],
                 param['operators'],
                 param['amount'],
                 data['chat_id'])
        self.db.execute(sql, param)

    #reset command
    def reset(self, data):
        data['method'] = 'sendMessage'
        args = data['args'].strip()
        if args=='':
            data['text'] = self.reset_all(data)
            return
        reset_param = self.verify_reset(data)
        if len(reset_param)!=0:
            data['text'] = self.reset_alert(data, reset_param)
        
    def reset_all(self, data):
        from_id = data['from_id']
        sql = 'DELETE FROM alerts WHERE fromid=?'
        param = (from_id,)
        self.db.execute(sql, param)
        return '<b>Hi {}, you have cleared all alerts.</b>'.format(data.get('sender_name',''))

    def verify_reset(self, data):
        args = data['args'].strip()
        err_msg = ('Please use the following format.\n'
                   'For stock:\n'
                   'e.g. /reset 5\n'
                   'e.g. /reset 0005\n\n'
                   'For exchange rate:\n'
                   'e.g. /reset jpy\n'
                   'e.g. /reset twd to hkd\n\n'
                   'For index:\n'
                   'e.g. /reset hsi')

        types = ''
        code = ''

        if args.upper() in self.idx_dct_no_prefix.keys():
            #verify index code
            types = 'IDX'
            if '%5E'+args.upper() in self.idx_dct.keys():
                code = '%5E'+args.upper()
            else:
                code = args.upper()
        elif args[0].isnumeric():
            #verify stock code
            types = 'STK'
            if len(args)>4 or not(args.isnumeric()) or int(args)==0:
                data['text'] = '"{}" is not a valid stock code. Please retry.'.format(args)
                return {}
            code = args.zfill(4)
        else:
            #verify currency
            types = 'FX'
            if (' to ' not in args and len(args)!=3) or (' to ' in args and len(args)!=10):
                data['text'] = err_msg
                return {}

            if len(args)==3:
                args = args[:3] + ' to HKD'
            
            ccy = args[:3]
            ccy2 = args[7:10]
       
            if ccy.upper() not in self.ccy_dct.keys():
                data['text'] = '"{}" is not a valid currency code. Please retry.'.format(ccy)
                return {}
            elif ccy2.upper() not in self.ccy_dct.keys():
                data['text'] = '"{}" is not a valid currency code. Please retry.'.format(ccy2)
                return {}
            code = ccy.upper()+':'+ccy2.upper()
                
        return {'types': types,
                'code': code}
    
    def reset_alert(self, data, reset_param):
        from_id = data['from_id']
        types = reset_param['types']
        code = reset_param['code']
        select_sql = 'SELECT * FROM alerts WHERE fromid=? and types=? and code=?'
        delete_sql = 'DELETE FROM alerts WHERE fromid=? and types=? and code=?'
        param = (from_id, types, code)
        sender_name = data.get('sender_name','')
        
        desc = {'STK':'stock', 'FX':'exchange rate', 'IDX':'index'}[types]
        code_text = code

        if types=='FX':
            code_text = code_text.replace(':',' to ')
        elif types=='IDX':
            code_text = code_text.replace('%5E','')
            
        rows = self.db.execute(select_sql, param)
        if len(rows)==0:
            return '<b>Hi {}, you do not have alerts on {} {}</b>'.format(sender_name, desc, code_text)
        else:
            self.db.execute(delete_sql, param)
            return '<b>Hi {}, you have cleared alerts on {} {}</b>'.format(sender_name, desc, code_text)

    #ccy command
    def get_ccy(self, data):
        data['method'] = 'sendMessage'
        args = data['args'].strip()
        if args=='':
            data['text'] =  self.ccy_lst
        else:
            data['text'] = self.search_ccy(args)

    def get_ccy_dct(self):
        try:
            rows = self.db.execute('SELECT * FROM currencies')
            return dict(rows)
        except Exception as e:
            logger.exception('get_ccy_dct Exception',str(e))
            return {}
        
    def search_ccy(self, args):
        msg = ''
        for k,v in self.ccy_dct.items():
            if args.upper() in k or args.upper() in v.upper():
                msg += '{} - {}\n'.format(k,v)
        if msg=='':
            return 'No results found.'
        return msg

    #idx command
    def get_idx_lst(self, data):
        data['method'] = 'sendMessage'
        args = data['args'].strip()
        if args=='':
            data['text'] =  self.idx_lst
        else:
            data['text'] = self.search_idx(args)

    def get_idx_dct(self):
        try:
            rows = self.db.execute('SELECT * FROM indices')
            return dict(rows)
        except Exception as e:
            logger.exception('get_idx_dct Exception',str(e))
            return {}
        
    def search_idx(self, args):
        msg = ''
        for k,v in self.idx_dct_no_prefix.items():
            if args.upper() in k or args.upper() in v.upper():
                msg += '{} - {}\n'.format(k,v)
        if msg=='':
            return 'No results found.'
        return msg
        
    #check command
    def check(self, data):
        select_sql = 'SELECT * FROM alerts'
        rows = self.db.execute(select_sql)
        msgs = []
        for row in rows:
            from_id, name, types, code, operators, amount, chat_id = row
            amount = float(amount)
            
            current = -1
            code_text = code
            
            if types=='STK':
                current = float(self.get_stock_info(code).get('price',-1))
            elif types=='FX':
                ccy = code.split(':')[0]
                ccy2 = code.split(':')[1]
                current = float(self.get_xrates(ccy, ccy2, 1))
                code_text = code_text.replace(':',' to ')
            elif types=='IDX':
                current = float(self.get_idx_info(code).get('price',-1))
                code_text = code_text.replace('%5E','')
                
            if current<=0:
                continue
            elif (operators=='&lt' and current < amount) or (operators=='&gt' and current > amount):
                logger.info('name: [{}], code: [{}], current: [{}], amount: [{}]'.format(name, code, current, amount))
                msg = {}
                desc = {'STK':'stock price', 'FX':'rate', 'IDX':'index'}[types]
                word = {'&lt': 'lower', '&gt': 'higher'}[operators]
                msg_text = '<b>Hi {},\n{} {} is now {},\n{} than {}</b>'.format(name, code_text, desc, current, word, amount)
                msg['text'] = msg_text
                msg['chat_id'] = chat_id
                msgs.append(msg)
                delete_sql = 'DELETE FROM alerts WHERE fromid=? AND types=? AND code=? AND operators=?'
                param = (from_id, types, code, operators)
                self.db.execute(delete_sql, param)
                if self.email_service:
                    subject = '{} {} notice to {}'.format(code_text, desc, name)
                    self.email_service.send_email(subject, msg_text)
                    
        if len(msgs)!=0:
            data['method'] = 'sendMultiMessage'
            data['msgs'] = msgs


    #us command
    def get_us_stk(self, data):
        data['method'] = 'sendMessage'
        code = self.get_us_stock_code(data)
        if code!='':
            stock_info = self.get_us_stock_info(code)
            if len(stock_info)==0 or stock_info.get('price','')=='':
                data['text'] = 'Please enter a valid US stock code.'
            else:
                data['text'] =  '<b><u>{}</u>\n{}    {}</b>'.format(stock_info.get('company','NA'),
                                                                    stock_info.get('price','NA'),
                                                                    stock_info.get('change','NA'))
   
    def get_us_stock_code(self, data):
        args = data['args'].strip()
        if len(args)==0:
            data['text'] = 'Please use the following format.\ne.g. /us amzn\ne.g. /us aapl'
            return ''
        elif not(args.replace('.','').isalnum()):
            data['text'] = '"{}" is not a valid US stock code.'.format(args)
            return ''        
        return args.upper()
    
    def get_us_stock_info(self, code):
        url = 'https://finance.yahoo.com/quote/{}/'.format(code)
        headers = {'User-Agent':''}
        page = HttpService.get(url, headers)
        soup = BeautifulSoup(page.content, 'html.parser')
        stock_info = {}

        price_ele = soup.find('span',{'class':'Trsdu(0.3s) Fw(b) Fz(36px) Mb(-4px) D(ib)'})
        if price_ele is None:
            logger.error('yahoo finance US stock price is not available!')
        else:
            stock_info['price'] = price_ele.get_text(strip=True).replace(',','')

        company_ele = soup.find('h1',{'class':'D(ib) Fz(18px)'})
        if company_ele is None:
            logger.error('yahoo finance US company name is not available!')
        else:
            company = company_ele.get_text(strip=True)
            company = company[:company.find('(')].strip()
            stock_info['company'] = company

        change_ele = soup.find_all('span',{'class':['Trsdu(0.3s) Fw(500) Pstart(10px) Fz(24px) C($negativeColor)',
                                                    'Trsdu(0.3s) Fw(500) Pstart(10px) Fz(24px) C($positiveColor)',
                                                    'Trsdu(0.3s) Fw(500) Pstart(10px) Fz(24px)']})
        if change_ele is None or len(change_ele)==0:
            logger.error('yahoo finance US stock change is not available!')
        else:
            stock_info['change'] = change_ele[0].get_text(strip=True)
        
        return stock_info           

    #ma command
    def get_ma(self, data):
        data['method'] = 'sendMessage'
        code = self.get_ma_code(data)
        if code!='':
            ma_info = self.get_ma_info(code)
            if len(ma_info)==0:
                data['text'] = 'Please enter a valid stock code.'
            else:
                data['text'] =  ('<b>10-Day Moving Average: {}\n'
                                 '50-Day Moving Average: {}\n'
                                 '200-Day Moving Average: {}</b>').format(ma_info.get('10','NA'),
                                                                          ma_info.get('50','NA'),
                                                                          ma_info.get('200','NA'))
   
    def get_ma_code(self, data):
        args = data['args'].strip()
        if len(args)==0 or len(args)>5:
            data['text'] = 'Please use the following format.\ne.g. /ma 2888\ne.g. /ma 02888'
            return ''
        elif not(args.isnumeric()) or int(args)==0:
            data['text'] = '"{}" is not a valid stock code.'.format(args)
            return ''        
        return args
    
    def get_ma_info(self, code):
        url = 'https://finance.now.com/stock/?s={}'.format(code.zfill(5))
        url_2 = 'https://finance.yahoo.com/quote/{0}.HK/key-statistics?p={0}.HK'.format(code[1:] if len(code)>4 else code.zfill(4))
        headers = {'User-Agent':''}
        page = HttpService.get(url, headers)
        soup = BeautifulSoup(page.content, 'html.parser')
        page_2 = HttpService.get(url_2, headers)
        soup_2 = BeautifulSoup(page_2.content, 'html.parser')        
        try:
            ma_10 = soup.find('td',text='10天平均').find_next('td').get_text(strip=True).replace(',','')
            ma_50 = soup.find('td',text='50天平均').find_next('td').get_text(strip=True).replace(',','')
            ma_200 = soup_2.find('span',text='200-Day Moving Average').parent.find_next('td').get_text(strip=True).replace(',','')
        except AttributeError as ae:
            logger.error('now finance moving average is not available!')
            logger.exception('fxstock get_ma_info AttributeError: '+str(ae))
            return {}
        return {'10':ma_10, '50':ma_50, '200':ma_200}
    
    #rsi command
    def get_rsi(self, data):
        data['method'] = 'sendMessage'
        code = self.get_rsi_code(data)
        if code!='':
            rsi_info = self.get_rsi_info(code)
            if len(rsi_info)==0:
                data['text'] = 'Please enter a valid stock code.'
            else:
                data['text'] =  ('<b>RSI: {}</b>').format(rsi_info.get('rsi','NA'))
   
    def get_rsi_code(self, data):
        args = data['args'].strip()
        if len(args)==0 or len(args)>4:
            data['text'] = 'Please use the following format.\ne.g. /rsi 5\ne.g. /rsi 0005'
            return ''
        elif not(args.isnumeric()) or int(args)==0:
            data['text'] = '"{}" is not a valid stock code.'.format(args)
            return ''        
        return args
    
    def get_rsi_info(self, code):
        #url = 'https://finance.yahoo.com/quote/AAPL/history?p=AAPL'
        #url = 'https://finance.yahoo.com/quote/%5EHSI/history?p=%5EHSI'
        url = 'https://finance.yahoo.com/quote/{0}.HK/history?p={0}.HK'.format(code.zfill(4))
        headers = {'User-Agent':''}
        page = HttpService.get(url, headers)
        soup = BeautifulSoup(page.content, 'html.parser')
        prices = []
        try:
            trs = soup.find_all('tr',{'class':'BdT Bdc($seperatorColor) Ta(end) Fz(s) Whs(nw)'})
            i = 0
            while len(prices)<90:
                tds = trs[i].find_all('td')
                i += 1
                if len(tds)<5:
                    continue
                else:
                    span = tds[4].find('span')
                    if span is None:
                        continue
                    else:
                        price = span.get_text(strip=True).replace(',','')
                        prices.append(price)
                    
            prices.reverse()
            
            rsi = self.rsi_func(prices)
        except AttributeError as ae:
            logger.error('yahoo finance relative strength index is not available!')
            logger.exception('fxstock get_rsi AttributeError: '+str(ae))
            return {}
        return {'rsi': rsi}

    def rsi_func(self, prices, n=14):
        deltas = [float(j)-float(i) for i, j in zip(prices[:-1], prices[1:])]
        seed = deltas[:n+1]
        up = sum([i for i in seed if i>0])/n
        down = sum([-i for i in seed if i<0])/n
        rs = up/down
        
        for i in range(n, len(prices)):
            delta = deltas[i-1]
            if delta > 0:
                upval = delta
                downval = 0.
            else:
                upval = 0.
                downval = -delta

            up = (up*(n-1)+upval)/n
            down = (down*(n-1)+downval)/n
            rs = up/down
        rsi = 100. - 100./(1.+rs)
        return round(rsi, 3)
    
