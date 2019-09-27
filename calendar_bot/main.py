import datetime
import json
import random
import time
from urllib import request, parse

import db

#Setting
token = 'YOUR_TOKEN'
refresh_time = 0.2

class Bot:
    def __init__(self, token):
        self.api_url = "https://api.telegram.org/bot{}/".format(token)
        self.commands = {'start':self.send_command_list,
                         'hi':self.send_greeting,
                         'photo':self.send_photo,
                         'show':self.show,
                         'mark':self.mark,
                         'reset':self.reset}
        self.db = db.DB()

    def execute(self, command, data):
        print(datetime.datetime.now().strftime("%H:%M:%S"), command)
        self.commands[command](data)
        
    def send_request(self, url, params=None):
        data = None if params is None else parse.urlencode(params).encode()
        req = request.Request(url, data=data)
        with request.urlopen(req) as resp:
            return json.loads(resp.read())
        
    def get_updates(self, offset=0, timeout=30):
        method = 'getUpdates'
        params = {'timeout': timeout, 'offset': offset}
        json_resp = self.send_request(self.api_url + method, params)
        return json_resp['result']

    def send_message(self, data):
        method = 'sendMessage'
        params = {'chat_id': data['chat_id'], 'text': data['text'], 'parse_mode': 'HTML'}
        self.send_request(self.api_url + method, params)

    def send_greeting(self, data):
        data['text'] =  'Hi, ' + data['text']
        self.send_message(data)

    def show(self, data):
        data['text'] =  self.db.get_calendar()
        self.send_message(data)

    def mark(self, data):
        if self.is_int(data['date']) and int(data['date'])>0 and int(data['date'])<32:
            self.db.add(int(data['date']))
            data['text'] = '<b>Mark date '+data['date']+' on the calendar</b>'
        else:
            data['text'] =  '"'+data['date']+'" is not a valid date. Please retry.'
        self.send_message(data)

    def reset(self, data):
        self.db.reset()
        data['text'] =  '<b>Reset the calendar</b>'
        self.send_message(data)
        
    def is_int(self, s):
        try: 
            int(s)
            return True
        except ValueError:
            return False
    
    def send_command_list(self, data):
        data['text'] = ('/show - show calendar\n'
                        '/mark - mark calendar e.g. /mark 9\n'
                        '/reset - reset calendar\n'
                        '/hi - greeting\n'
                        '/photo - get a random photo')
        self.send_message(data)
        
    def get_image_url(self):
        rand_int = random.randint(0,1084)
        url = 'https://picsum.photos/id/{}/info'.format(str(rand_int))
        json_resp = self.send_request(url)
        return json_resp['download_url']

    def send_photo(self, data):
        method = 'sendPhoto'
        params = {'chat_id': data['chat_id'], 'photo': self.get_image_url(), 'parse_mode': 'HTML'}
        self.send_request(self.api_url + method, params)
        
bot = Bot(token)

def get_data(json_obj):
    if 'text' in json_obj['message']:
        message_text = json_obj['message']['text']
    else:
        message_text=''
        
    if 'first_name' in json_obj['message']:
        sender_name = json_obj['message']['chat']['first_name']
    elif 'new_chat_member' in json_obj['message']:
        sender_name = json_obj['message']['new_chat_member']['username']
    elif 'from' in json_obj['message']:
        sender_name = json_obj['message']['from']['first_name']
    else:
        sender_name = "unknown"

    return {'update_id': json_obj['update_id'],
            'chat_id': json_obj['message']['chat']['id'],
            'message_text': message_text,
            'text': sender_name}

def main():
    new_offset = 0
    
    while True:
        time.sleep(refresh_time)
        print(datetime.datetime.now().strftime("%H:%M:%S"))
        
        all_updates = bot.get_updates(new_offset)

        if len(all_updates) > 0:
            for current_update in all_updates:
                
                data = get_data(current_update)
                message_text = data['message_text']
                
                if message_text.startswith('/'):
                    
                    if message_text.startswith('/mark ') and len(message_text)>6:
                        command = 'mark'
                        data['date'] = message_text[6:]
                    else:
                        command = message_text[1:]
                        
                    if command in bot.commands.keys() and message_text!='/mark':
                        try:
                            bot.execute(command, data)
                        except Exception as e:
                            print('Exception: '+str(e))
                new_offset = data['update_id'] + 1


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt as e:
        print('KeyboardInterrupt Exception: '+str(e))
        exit()
