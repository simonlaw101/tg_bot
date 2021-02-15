import json
import logging
import os
import requests

from datetime import timedelta
from uuid import uuid4

import firebase_admin
from firebase_admin import credentials
from firebase_admin import storage

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
        data = {'update_id': json_obj['update_id'],
                'from_id': -1,
                'sender_name': 'unknown'}

        if 'message' in json_obj:
            message_obj = json_obj['message']
            TgService.set_from(message_obj, data)
        elif 'edited_message' in json_obj:
            message_obj = json_obj['edited_message']
            TgService.set_from(message_obj, data)
        elif 'callback_query' in json_obj:
            callback_query_obj = json_obj['callback_query']
            message_obj = callback_query_obj.get('message', {})
            TgService.set_from(callback_query_obj, data)
            data['callback_query_id'] = callback_query_obj.get('id', -1)
            data['inline_message_id'] = callback_query_obj.get('inline_message_id', -1)
            if 'game_short_name' in callback_query_obj:
                message_obj['text'] = '/'+callback_query_obj['game_short_name']
            else:
                message_obj['text'] = callback_query_obj.get('data', '')
        elif 'inline_query' in json_obj:
            message_obj = json_obj['inline_query']
            TgService.set_from(message_obj, data)
            data['inline_query_id'] = message_obj.get('id', -1)
            message_obj['text'] = '/query '+message_obj.get('query')
        else:
            message_obj = {}

        data['message_text'] = message_obj.get('text', '')
        data['chat_id'] = message_obj.get('chat', {}).get('id', -1)
        data['message_id'] = message_obj.get('message_id', -1)

        caption = message_obj.get('caption', '')
        if caption.startswith(('/ocr', '/cloud')):
            data['message_text'] = caption
            file_id = TgService.get_file_id(message_obj)
            data['file_url'] = '' if file_id == '' else TgService.get_file_url(file_id)
        elif data['message_text'].startswith(('/ocr', '/cloud')) and 'reply_to_message' in message_obj:
            file_id = TgService.get_file_id(message_obj['reply_to_message'])
            data['file_url'] = '' if file_id == '' else TgService.get_file_url(file_id)

        return data

    @staticmethod
    def set_from(json_obj, data):
        if 'from' in json_obj:
            from_obj = json_obj['from']
            data['from_id'] = from_obj.get('id', -1)
            first_name = from_obj.get('first_name', '')
            last_name = from_obj.get('last_name', '')
            data['sender_name'] = first_name.strip() + ' ' + last_name.strip()

    @staticmethod
    def send_message(data):
        params = {'chat_id': data['chat_id'], 'text': data['text'], 'parse_mode': 'HTML'}
        message_id = data.get('message_id', -1)
        reply_markup = data.get('reply_markup')
        if data['chat_id'] < 0 and message_id != -1:
            params['reply_to_message_id'] = message_id
        if reply_markup is not None:
            params['reply_markup'] = json.dumps(reply_markup)
        HttpService.post_json(TgService.API_URL + 'sendMessage', params)

    @staticmethod
    def send_photo(data):
        params = {'chat_id': data['chat_id'], 'photo': data['photo'], 'parse_mode': 'HTML'}
        message_id = data.get('message_id', -1)
        if data['chat_id'] < 0 and message_id != -1:
            params['reply_to_message_id'] = message_id
        HttpService.post_json(TgService.API_URL + 'sendPhoto', params)
        TgService.answer_callback_query(data)

    @staticmethod
    def send_document(data):
        params = {'chat_id': data['chat_id'], 'document': data['document'], 'parse_mode': 'HTML'}
        message_id = data.get('message_id', -1)
        if data['chat_id'] < 0 and message_id != -1:
            params['reply_to_message_id'] = message_id
        HttpService.post_json(TgService.API_URL + 'sendDocument', params)
        TgService.answer_callback_query(data)

    @staticmethod
    def get_file_id(message_obj):
        photo_list = message_obj.get('photo', [])
        document = message_obj.get('document', {})
        video = message_obj.get('video', {})
        if len(photo_list) > 0:
            return photo_list[-1].get('file_id', '')
        elif len(document) > 0:
            return document.get('file_id', '')
        elif len(video) > 0:
            return video.get('file_id', '')
        return ''

    @staticmethod
    def get_file_url(file_id):
        params = {'file_id': file_id}
        json_resp = HttpService.post_json(TgService.API_URL + 'getFile', params)
        file_path = json_resp.get('result', {}).get('file_path', '')
        if file_path == '':
            return ''
        return TgService.FILE_URL + file_path

    @staticmethod
    def set_my_commands(commands):
        params = {'commands': json.dumps(commands)}
        return HttpService.post_json(TgService.API_URL + 'setMyCommands', params)

    @staticmethod
    def answer_callback_query(data):
        params = {'callback_query_id': data['callback_query_id']}
        url = data.get('url', '')
        if url != '':
            params['url'] = url
        HttpService.post_json(TgService.API_URL + 'answerCallbackQuery', params)

    @staticmethod
    def edit_message_text(data):
        if data.get('inline_message_id', -1) != -1:
            params = {'inline_message_id': data['inline_message_id'],
                      'text': data['text'], 'parse_mode': 'HTML'}
        else:
            params = {'chat_id': data['chat_id'], 'message_id': data['message_id'],
                      'text': data['text'], 'parse_mode': 'HTML'}
        reply_markup = data.get('reply_markup')
        if reply_markup is not None:
            params['reply_markup'] = json.dumps(reply_markup)
        HttpService.post_json(TgService.API_URL + 'editMessageText', params)
        TgService.answer_callback_query(data)

    @staticmethod
    def answer_inline_query(data):
        params = {'inline_query_id': data['inline_query_id']}
        if data.get('results') is not None:
            params['results'] = json.dumps(data['results'])
        HttpService.post_json(TgService.API_URL + 'answerInlineQuery', params)

    @staticmethod
    def get_webhook_info():
        return HttpService.post_json(TgService.API_URL + 'getWebhookInfo')

    @staticmethod
    def set_web_hook(invoke_url):
        return HttpService.post_json(TgService.API_URL + 'setWebHook?url=' + invoke_url)

    @staticmethod
    def send_game(data):
        params = {'chat_id': data['chat_id'], 'game_short_name': data['game_short_name']}
        message_id = data.get('message_id', -1)
        reply_markup = data.get('reply_markup')
        if data['chat_id'] < 0 and message_id != -1:
            params['reply_to_message_id'] = message_id
        if reply_markup is not None:
            params['reply_markup'] = json.dumps(reply_markup)
        HttpService.post_json(TgService.API_URL + 'sendGame', params)


class FbService:
    def __init__(self):
        cred = credentials.Certificate('cloud/serviceAccountKey.json')
        firebase_admin.initialize_app(cred, {'storageBucket': 'YOUR_STORAGE_BUCKET'})

    def list_file(self, folder_name):
        bucket = storage.bucket()
        lst = []
        for blob in bucket.list_blobs():
            filename = blob.name
            if filename.startswith(folder_name):
                lst.append({'name': os.path.split(filename)[1], 'full_path': filename})
        return lst

    def upload_file(self, src_filename, des_filename):
        bucket = storage.bucket()
        blob = bucket.blob(des_filename)
        blob.metadata = {"firebaseStorageDownloadTokens": uuid4()}
        blob.upload_from_filename(src_filename)

    def delete_file(self, src_filename):
        bucket = storage.bucket()
        blob = bucket.blob(src_filename)
        blob.delete()

    def download_file(self, src_filename, des_filename):
        bucket = storage.bucket()
        blob = bucket.blob(src_filename)
        blob.download_to_filename(des_filename)

    def get_file_url(self, src_filename):
        bucket = storage.bucket()
        blob = bucket.blob(src_filename)
        return blob.generate_signed_url(timedelta(seconds=30), method='GET')


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
