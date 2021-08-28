import logging
import os
import re
import tempfile
from datetime import datetime
from os.path import splitext

from constant import Constant
from service import FbService, HttpService

logger = logging.getLogger('FxStock')


class Cloud:
    def __init__(self, bucket_name):
        self.cmds = {'cloud': self.cloud,
                     'c1': self.cloud_select,
                     'c2': self.cloud_download,
                     'c3': self.cloud_delete,
                     'c4': self.cloud_cancel}
        self.desc = {'cloud': 'upload/download file'}
        self.examples = {'cloud': Constant.CLOUD_EXAMPLE}
        self.fb = FbService(bucket_name)

    def cloud(self, data):
        data['method'] = 'sendMessage'
        file_url = data.get('file_url', '')
        if file_url != '':
            args = data['args'].strip()
            if (args != '' and not re.match('^[a-zA-Z0-9_-]+$', args)) or len(args) > 20:
                data['text'] = 'Filename must be alphanumeric and within 20 characters!'.format(args)
            else:
                data['text'] = self.upload_file(args, file_url, data['from_id'])
        else:
            self.list_file(data)

    def list_file(self, data):
        files = self.fb.list_file(str(data['from_id']))
        if len(files) == 0:
            data['text'] = 'Cloud Storage is empty'
        else:
            data['text'] = 'Cloud Storage:'
            btn_lst = [[{'text': file['name'], 'callback_data': '/c1 {}'.format(file['full_path'])}]
                       for file in files]
            data['reply_markup'] = {'inline_keyboard': btn_lst}

    def upload_file(self, args, file_url, from_id):
        full_path = ''
        filename = self.get_des_filename(args, file_url)
        try:
            with tempfile.NamedTemporaryFile(mode='wb', delete=False) as f:
                full_path = f.name
                resp = HttpService.get(file_url)
                f.write(resp.content)
            self.fb.upload_file(full_path, '{}/{}'.format(from_id, filename))
            return '{} uploaded successfully'.format(filename)
        except Exception as e:
            logger.error('cloud Error in uploading file: ', str(e))
            return '<br>Failed to upload {}!</br>'.format(filename)
        finally:
            if full_path != '':
                os.remove(full_path)

    def get_des_filename(self, args, file_url):
        if args == '':
            return datetime.now().strftime('%Y%m%d%H%M%S%f')[:-3] + splitext(file_url)[1]
        return args + splitext(file_url)[1]

    def cloud_select(self, data):
        if data.get('callback_query_id', -1) != -1:
            data['method'] = ['editMessageText', 'answerCallbackQuery']
            args = data['args'].strip()
            data['text'] = 'Cloud Storage:\n{}'.format(os.path.split(args)[1])
            btn_lst = [[{'text': 'Download', 'callback_data': '/c2 ' + args},
                        {'text': 'Delete', 'callback_data': '/c3 ' + args}],
                       [{'text': 'Cancel', 'callback_data': '/c4 ' + args}]]
            data['reply_markup'] = {'inline_keyboard': btn_lst}
            return

    def cloud_cancel(self, data):
        if data.get('callback_query_id', -1) != -1:
            args = data['args'].strip()
            data['method'] = ['editMessageText', 'answerCallbackQuery']
            data['from_id'] = os.path.split(args)[0]
            self.list_file(data)

    def cloud_download(self, data):
        if data.get('callback_query_id', -1) != -1:
            args = data['args'].strip()
            if os.path.splitext(args)[1].lower() in ['.gif', '.jpg', '.jpeg', '.png']:
                data['method'] = ['sendPhoto', 'answerCallbackQuery', 'editMessageText']
                data['text'] = '{} downloaded successfully'.format(os.path.split(args)[1])
                data['photo'] = self.fb.get_file_url(args)
            else:
                data['method'] = ['sendDocument', 'answerCallbackQuery', 'editMessageText']
                data['text'] = '{} downloaded successfully'.format(os.path.split(args)[1])
                data['document'] = self.fb.get_file_url(args)

    def cloud_delete(self, data):
        if data.get('callback_query_id', -1) != -1:
            args = data['args']
            self.fb.delete_file(args)
            data['method'] = ['editMessageText', 'answerCallbackQuery']
            data['text'] = '<s>{}</s> deleted successfully'.format(os.path.split(args)[1])
