import logging
import requests

logger = logging.getLogger('FxStock')


class TgService:
    TOKEN = 'YOUR_TOKEN'
    API_URL = "https://api.telegram.org/bot{}/".format(TOKEN)
    FILE_URL = "https://api.telegram.org/file/bot{}/".format(TOKEN)

    @staticmethod
    def get_updates(offset=0, timeout=30):
        params = {'timeout': timeout, 'offset': offset}
        json_resp = HttpService.post_json(TgService.API_URL + 'getUpdates', params)
        return json_resp.get('result', [])

    @staticmethod
    def get_data(json_obj):
        message_obj = json_obj.get('message', json_obj.get('edited_message', {}))
        message_text = message_obj.get('text', '')
        caption = message_obj.get('caption', '')
        file_url = ''
        if caption.startswith('/ocr'):
            message_text = caption
            file_id = TgService.get_file_id(message_obj)
            file_url = '' if file_id == '' else TgService.get_file_url(file_id)
        chat_id = message_obj.get('chat', {}).get('id', '')
        chat_type = message_obj.get('chat', {}).get('type', 'private')
        message_id = -1 if chat_type == 'private' else message_obj.get('message_id', -1)

        if 'from' in message_obj:
            from_id = message_obj['from'].get('id', '')
            first_name = message_obj['from'].get('first_name', '')
            last_name = message_obj['from'].get('last_name', '')
            sender_name = first_name + ' ' + last_name
        else:
            from_id = ''
            sender_name = "unknown"

        return {'update_id': json_obj['update_id'],
                'chat_id': chat_id,
                'from_id': from_id,
                'message_text': message_text,
                'message_id': message_id,
                'file_url': file_url,
                'sender_name': sender_name.strip()}

    @staticmethod
    def send_message(data):
        params = {'chat_id': data['chat_id'], 'text': data['text'], 'parse_mode': 'HTML'}
        message_id = data.get('message_id', -1)
        if message_id > 0:
            params['reply_to_message_id'] = message_id
        HttpService.post_json(TgService.API_URL + 'sendMessage', params)

    @staticmethod
    def send_photo(data):
        params = {'chat_id': data['chat_id'], 'photo': data['image_url'], 'parse_mode': 'HTML'}
        HttpService.post_json(TgService.API_URL + 'sendPhoto', params)

    @staticmethod
    def get_file_id(message_obj):
        photo_list = message_obj.get('photo', [])
        document = message_obj.get('document', {})
        if len(photo_list) > 0:
            return photo_list[-1].get('file_id', '')
        elif len(document) > 0:
            return document.get('file_id', '')
        return ''

    @staticmethod
    def get_file_url(file_id):
        params = {'file_id': file_id}
        json_resp = HttpService.post_json(TgService.API_URL + 'getFile', params)
        file_path = json_resp.get('result', {}).get('file_path', '')
        if file_path == '':
            return ''
        return TgService.FILE_URL + file_path


class HttpService:
    @staticmethod
    def get(url, headers=None):
        try:
            return requests.get(url, headers=headers)
        except Exception as e:
            logger.exception('httpservice get Exception: '+str(e))
            return None

    @staticmethod
    def post_json(url, params=None):
        try:
            resp = requests.post(url, data=params)
            return resp.json()
        except Exception as e:
            logger.exception('httpservice post_json Exception: '+str(e))
            return {}
