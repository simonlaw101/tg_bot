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
    def __init__(self):
        self.cmds = {'cloud': self.cloud,
                     'cloud_download': self.cloud_download,
                     'cloud_delete': self.cloud_delete,
                     'cloud_cancel': self.cloud_cancel}
        self.desc = {'cloud': 'upload/download file'}
        self.examples = {'cloud': Constant.CLOUD_EXAMPLE}
        self.fb = FbService()
        self.tmp_dir = os.path.join(os.path.dirname(__file__), 'cloud')

    def cloud(self, data):
        args = data['args'].strip()
        file_url = data.get('file_url', '')

        if data.get('callback_query_id', -1) != -1:
            data['method'] = 'editMessageText'
            args_lst = args.split('|')
            data['text'] = "{}'s Cloud Storage:\n{}".format(args_lst[1],
                                                            os.path.split(args_lst[0])[1])
            btn_lst = [[{'text': 'Download', "callback_data": "/cloud_download " + args},
                        {'text': 'Delete', "callback_data": "/cloud_delete " + args}],
                       [{'text': 'Cancel', "callback_data": "/cloud_cancel " + args}]]
            data['reply_markup'] = {"inline_keyboard": btn_lst}
            return

        data['method'] = 'sendMessage'
        if file_url != '':
            if args != '' and not re.match('^[a-zA-Z0-9_-]+$', args):
                data['text'] = '"{}" is not a valid file name!'.format(args)
            else:
                data['text'] = self.upload_file(args, file_url, data['from_id'])
        else:
            self.list_file(data)

    def list_file(self, data):
        sender_name = data['sender_name']
        files = self.fb.list_file(str(data['from_id']))
        if len(files) == 0:
            data['text'] = "{}'s Cloud Storage is empty".format(sender_name)
        else:
            data['text'] = "{}'s Cloud Storage:".format(data['sender_name'])
            btn_lst = [[{'text': file['name'], "callback_data": "/cloud {}|{}".format(file['full_path'], sender_name)}]
                       for file in files]
            data['reply_markup'] = {"inline_keyboard": btn_lst}

    def upload_file(self, args, file_url, from_id):
        full_path = ''
        filename = self.get_des_filename(args, file_url)
        try:
            with tempfile.NamedTemporaryFile(mode="wb", delete=False, dir=self.tmp_dir) as f:
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

    def cloud_cancel(self, data):
        args = data['args'].strip()
        args_lst = args.split('|')
        if data.get('callback_query_id', -1) != -1:
            data['method'] = 'editMessageText'
            data['sender_name'] = args_lst[1]
            data['from_id'] = os.path.split(args_lst[0])[0]
            self.list_file(data)

    def cloud_download(self, data):
        args = data['args'].strip()
        args_lst = args.split('|')
        if data.get('callback_query_id', -1) != -1:
            if os.path.splitext(args)[1].lower() in ['.gif', '.jpg', '.jpeg', '.png']:
                data['method'] = 'sendPhotoEditMessageText'
                data['text'] = ("{}'s Cloud Storage:\n"
                                "{} downloaded successfully").format(args_lst[1],
                                                                     os.path.split(args_lst[0])[1])
                data['photo'] = self.fb.get_file_url(args_lst[0])
            else:
                data['method'] = 'sendDocumentEditMessageText'
                data['text'] = ("{}'s Cloud Storage:\n"
                                "{} downloaded successfully").format(args_lst[1],
                                                                     os.path.split(args_lst[0])[1])
                data['document'] = self.fb.get_file_url(args_lst[0])
                print(data['document'])

    def cloud_delete(self, data):
        args = data['args']
        args_lst = args.split('|')
        if data.get('callback_query_id', -1) != -1:
            self.fb.delete_file(args_lst[0])
            data['method'] = 'editMessageText'
            data['text'] = ("{}'s Cloud Storage:\n"
                            "{} deleted successfully").format(args_lst[1],
                                                              os.path.split(args_lst[0])[1])
