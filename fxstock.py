import logging
import requests
from bs4 import BeautifulSoup

from db import DB
from myemail import Email

logger = logging.getLogger('FxStock')

class FxStock:
    def __init__(self, enabled=True, send_email=False):
        self.enabled = enabled
        self.email_service = Email() if send_email else None
        self.cmds = {'stk':self.get_stk,
                     'fx':self.get_fx,
                     'alert':self.alert,
                     'reset':self.reset,
                     'ccy':self.get_ccy,
                     'check':self.check_fxstk}
        self.desc = {'stk': 'get stock price',
                     'fx': 'get exchange rate',
                     'alert': 'view/set alert',
                     'reset': 'clear alert',
                     'ccy': 'search currency code'}
        self.db = DB()
        self.ccy_dct = self.get_ccy_dct()
        self.ccy_lst = ''.join(['{} - {}\n'.format(k,v) for k,v in self.ccy_dct.items()])

    def send_request(self, url, headers=None):
        try:
            return requests.get(url,headers=headers)
        except Exception as e:
            logger.exception('fxstock send_request Exception: '+str(e))
            return None
        
    #stk command
    def get_stk(self, data):
        data['method'] = 'sendMessage'
        code = self.get_stock_code(data)
        if code!='':
            stock_info = self.get_stock_info(code)
            if len(stock_info)==0:
                data['text'] = 'Please enter a valid stock code.'
            else:
                data['text'] =  '<b><u>{}</u>\n{}    {}</b>'.format(stock_info['company'], stock_info['price'], stock_info['change'])
   
    def get_stock_code(self, data):
        args = data['args'].strip()
        if len(args)==0 or len(args)>4:
            data['text'] = 'Please use the following format.\ne.g. /stk 5\ne.g. /stk 0005'
            return ''
        elif not(args.isnumeric()) or int(args)==0:
            data['text'] = '"{}" is not a valid stock code.'.format(args)
            return ''        
        return args
    
    def get_stock_info(self, code):
        url = 'https://finance.yahoo.com/quote/{}.HK/'.format(code.zfill(4))
        headers = {'User-Agent':''}
        page = self.send_request(url,headers)
        soup = BeautifulSoup(page.content, 'html.parser')
        company_ele = soup.find('h1',{'class':'D(ib) Fz(18px)'})
        price_ele = soup.find('span',{'class':'Trsdu(0.3s) Fw(b) Fz(36px) Mb(-4px) D(ib)'})
        change_ele = soup.find('span',{'class':'Trsdu(0.3s) Fw(500) Pstart(10px) Fz(24px) C($dataRed)'})
        if company_ele is None or price_ele is None or change_ele is None:
            return {}
        else:       
            company = company_ele.get_text(strip=True)
            company = company[:company.find('(')].strip()
            price = price_ele.get_text(strip=True)
            change = change_ele.get_text(strip=True)
            return {'company':company, 'price':price, 'change':change}

    #fx command
    def get_fx(self, data):
        data['method'] = 'sendMessage'
        ccy_param = self.get_ccy_param(data)
        if len(ccy_param)!=0:
            data['text'] =  '<b>'+self.get_xrates(ccy_param[0],ccy_param[1],1)+'</b>'
   
    def get_ccy_param(self, data):
        args = data['args'].strip()
        if (' to ' in args and len(args)!=10) or (' to ' not in args and len(args)!=3):
            data['text'] = 'Please use the following format.\ne.g. /fx jpy\ne.g. /fx jpy to hkd'
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
        page = self.send_request(url)
        soup = BeautifulSoup(page.content, 'html.parser')
        ele = soup.find('span',{'class':'ccOutputTrail'})
        return ele.previous_sibling.replace(',','') + ele.get_text(strip=True)
    
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
        rows = self.db.execute(sql,param)
        if len(rows)==0:
            return '<b>No alert set.</b>'
        else:
            msg = ''
            for row in rows:
                msg += '{} {} {}\n'.format(row[3].replace(':',' to '),row[4],row[5])
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
                   'e.g. /alert twd to hkd &gt3.8')

        types = ''
        code = ''
        operators = ''
        amount = ''
        
        if args[0].isnumeric():
            #verify stock code
            types = 'STK'
            space_idx = args.find(' ')
            space_idx = len(args) if space_idx<0 else space_idx
            code = args[:space_idx]
            if len(code)>4 or not(code.isnumeric()) or\
               int(code)==0 or len(self.get_stock_info(code))==0:
                data['text'] = '"{}" is not a valid stock code. Please retry.'.format(code)
                return {}
            code = code.zfill(4)
            if '&lt' not in args and '&gt' not in args:
                args = code+'&lt'+args[space_idx:].strip()
            else:
                args = code+args[space_idx:].strip()
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
        elif not(self.is_float(amount)) or float(amount)<=0:
            data['text'] = '"{}" is not a valid amount. Please retry.'.format(amount)
            return {}
        elif len(str(float(amount)).replace('.',''))>9:
            data['text'] = 'Maximum length of amount is 9. Please retry.'
            return {}            
        
        return {'types': types,
                'code': code,
                'operators': operators,
                'amount': str(float(amount))}
    
    def is_float(self, s):
        try: 
            float(s)
            return True
        except ValueError:
            return False

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
        self.db.execute(sql,param)
        return '<b>Hi {}, you have cleared all alerts.</b>'.format(data.get('sender_name',''))

    def verify_reset(self, data):
        args = data['args'].strip()
        err_msg = ('Please use the following format.\n'
                   'For stock:\n'
                   'e.g. /reset 5\n'
                   'e.g. /reset 0005\n\n'
                   'For exchange rate:\n'
                   'e.g. /reset jpy\n'
                   'e.g. /reset twd to hkd')

        types = ''
        code = ''
        
        if args[0].isnumeric():
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
        desc = 'exchange rate' if types=='FX' else 'stock'
        
        rows = self.db.execute(select_sql,param)
        if len(rows)==0:
            return '<b>Hi {}, you do not have alerts on {} {}</b>'.format(sender_name, desc, code.replace(':',' to '))
        else:
            self.db.execute(delete_sql,param)
            return '<b>Hi {}, you have cleared alerts on {} {}</b>'.format(sender_name, desc, code.replace(':',' to '))

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
        else:
            return msg

    #check command
    def check_fxstk(self, data):
        sql = 'SELECT * FROM alerts'
        delete_sql = 'DELETE FROM alerts WHERE fromid=? AND types=? AND code=? AND operators=?'
        rows = self.db.execute(sql)
        msgs = []
        for row in rows:
            msg = {}
            msg_template = '<b>Hi {},\n{} {} is now {},\n{} than {}</b>'
            desc = ''
            
            from_id = row[0]
            name = row[1]
            chat_id = row[6]
            types = row[2]
            code = row[3]
            operators = row[4]
            amount = float(row[5])
            
            current = 0
            if types=='STK':
                desc = 'stock price'
                current = float(self.get_stock_info(code).get('price',0))
            elif types=='FX':
                desc = 'rate'
                ccy = code.split(':')[0]
                ccy2 = code.split(':')[1]
                current = float(self.get_xrates(ccy, ccy2, 1))
            
            if operators=='&lt' and current < amount:
                logger.info('name: [{}], code: [{}], current: [{}], amount: [{}]'.format(name, code, current, amount))
                msg_text = msg_template.format(name, code.replace(':',' to '), desc, current, 'lower', amount)
                msg['text'] = msg_text
                msg['chat_id'] = chat_id
                msgs.append(msg)
                param = (from_id, types, code, operators)
                self.db.execute(delete_sql, param)
                if self.email_service:
                    subject = '{} {} notice to {}'.format(code.replace(':',' to '), desc, name)
                    self.email_service.send_email(subject, msg_text)
            elif operators=='&gt' and current > amount:
                logger.info('name: [{}], code: [{}], current: [{}], amount: [{}]'.format(name, code, current, amount))
                msg_text = msg_template.format(name, code.replace(':',' to '), desc, current, 'higher', amount)
                msg['text'] = msg_text
                msg['chat_id'] = chat_id
                msgs.append(msg)
                param = (from_id, types, code, operators)
                self.db.execute(delete_sql, param)
                if self.email_service:
                    subject = '{} {} notice to {}'.format(code.replace(':',' to '), desc, name)
                    self.email_service.send_email(subject, msg_text)

        if len(msgs)!=0:
            data['method'] = 'sendMultiMessage'
            data['msgs'] = msgs

            
