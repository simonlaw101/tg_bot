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
    def __init__(self, db):
        self.cmds = {'cloud': self.cloud,
                     'c1': self.cloud_select,
                     'c2': self.cloud_download,
                     'c3': self.cloud_delete,
                     'c4': self.cloud_cancel,
                     'pin': self.pin,
                     'p1': self.pin_select,
                     'p2': self.pin_view,
                     'p3': self.pin_unpin,
                     'p4': self.pin_cancel}
        self.desc = {'cloud': 'upload/download file',
                     'pin': 'pin message'}
        self.examples = {'cloud': Constant.CLOUD_EXAMPLE,
                         'pin': Constant.PIN_EXAMPLE}
        self.fb = db

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
            return '<b>Failed to upload {}!</b>'.format(filename)
        finally:
            if full_path != '':
                os.remove(full_path)

    def get_des_filename(self, args, file_url):
        if args == '':
            return datetime.now().strftime('%Y%m%d%H%M%S%f')[:-3] + splitext(file_url)[1]
        return args + splitext(file_url)[1]

    def cloud_select(self, data):
        if data.get('callback_query_id', -1) != -1:
            data['method'] = 'editMessageText, answerCallbackQuery'
            args = data['args'].strip()
            data['text'] = 'Cloud Storage:\n{}'.format(os.path.split(args)[1])
            btn_lst = [[{'text': 'Download', 'callback_data': '/c2 ' + args},
                        {'text': 'Delete', 'callback_data': '/c3 ' + args}],
                       [{'text': 'Cancel', 'callback_data': '/c4 ' + args}]]
            data['reply_markup'] = {'inline_keyboard': btn_lst}

    def cloud_cancel(self, data):
        if data.get('callback_query_id', -1) != -1:
            args = data['args'].strip()
            data['method'] = 'editMessageText, answerCallbackQuery'
            data['from_id'] = os.path.split(args)[0]
            self.list_file(data)

    def cloud_download(self, data):
        if data.get('callback_query_id', -1) != -1:
            args = data['args'].strip()
            if os.path.splitext(args)[1].lower() in ['.gif', '.jpg', '.jpeg', '.png']:
                data['method'] = 'sendPhoto, answerCallbackQuery, editMessageText'
                data['text'] = '{} downloaded successfully'.format(os.path.split(args)[1])
                data['photo'] = self.fb.get_file_url(args)
            else:
                data['method'] = 'sendDocument, answerCallbackQuery, editMessageText'
                data['text'] = '{} downloaded successfully'.format(os.path.split(args)[1])
                data['document'] = self.fb.get_file_url(args)

    def cloud_delete(self, data):
        if data.get('callback_query_id', -1) != -1:
            args = data['args']
            self.fb.delete_file(args)
            data['method'] = 'editMessageText, answerCallbackQuery'
            data['text'] = '<s>{}</s> deleted successfully'.format(os.path.split(args)[1])

    def pin(self, data):
        data['method'] = 'sendMessage'
        reply_msg_text = data.get('reply_msg_text', '')
        if reply_msg_text != '':
            args = data['args'].strip()
            reply_msg_text = reply_msg_text.translate({ord(c): '' for c in '^;<>\\|`'})
            if (args != '' and not re.match('^[a-zA-Z0-9_-]+$', args)) or len(args) > 20:
                data['text'] = 'Message name must be alphanumeric and within 20 characters!'.format(args)
            else:
                data['text'] = self.set_pin(args, data['from_id'], reply_msg_text)
        else:
            self.list_pin(data)

    def set_pin(self, args, from_id, reply_msg_text):
        if args == '':
            args = datetime.now().strftime('%Y%m%d%H%M%S%f')[:-3]
        try:
            self.fb.set_doc('pin', str(from_id), {args: reply_msg_text})
            return 'Pinned message "{}" successfully'.format(args)
        except Exception as e:
            logger.error('cloud Error in pinning message: ', str(e))
            return '<b>Failed to pin message "{}"!</b>'.format(args)

    def list_pin(self, data):
        from_id = str(data['from_id'])
        doc = self.fb.get_doc('pin', from_id)
        if doc is None or len(doc) == 0:
            data['text'] = 'No pinned message'
        else:
            data['text'] = 'Pinned message:'
            btn_lst = [[{'text': k, 'callback_data': '/p1 {}|{}'.format(from_id, k)}]
                       for k in doc.keys()]
            data['reply_markup'] = {'inline_keyboard': btn_lst}

    def pin_select(self, data):
        if data.get('callback_query_id', -1) != -1:
            data['method'] = 'editMessageText, answerCallbackQuery'
            args = data['args'].strip()
            args_lst = args.split('|')
            data['text'] = 'Pinned message:\n{}'.format(args_lst[1])
            btn_lst = [[{'text': 'View', 'callback_data': '/p2 ' + args},
                        {'text': 'Unpin', 'callback_data': '/p3 ' + args}],
                       [{'text': 'Cancel', 'callback_data': '/p4 ' + args}]]
            data['reply_markup'] = {'inline_keyboard': btn_lst}

    def pin_cancel(self, data):
        if data.get('callback_query_id', -1) != -1:
            args = data['args'].strip()
            args_lst = args.split('|')
            data['method'] = 'editMessageText, answerCallbackQuery'
            data['from_id'] = args_lst[0]
            self.list_pin(data)

    def pin_unpin(self, data):
        if data.get('callback_query_id', -1) != -1:
            args = data['args']
            args_lst = args.split('|')
            self.fb.delete_doc('pin', args_lst[0], args_lst[1])
            data['method'] = 'editMessageText, answerCallbackQuery'
            data['text'] = 'Unpinned message "{}"'.format(args_lst[1])

    def pin_view(self, data):
        if data.get('callback_query_id', -1) != -1:
            args = data['args'].strip()
            from_id, tag = args.split('|')

            data['method'] = 'editMessageText, answerCallbackQuery'
            doc = self.fb.get_doc('pin', from_id)
            if doc is not None and len(doc) > 0:
                data['text'] = 'Pinned message "{}":\n{}'.format(tag, doc.get(tag, ''))