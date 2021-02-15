import logging

from constant import Constant
from os.path import splitext
from service import HttpService

logger = logging.getLogger('FxStock')


class Ocr:
    def __init__(self, api_key='helloworld'):
        self.cmds = {'ocr': self.ocr_parse_image}
        self.desc = {'ocr': 'read text from image'}
        self.examples = {'ocr': Constant.OCR_EXAMPLE}
        self.ocr_url = 'https://api.ocr.space/parse/image'
        self.api_key = api_key
        self.supported_file_type = {'.gif': 'GIF', '.jpg': 'JPG', '.jpeg': 'JPG', '.png': 'PNG'}
        self.supported_language = {'chs': 'Chinese(Simplified)',
                                   'cht': 'Chinese(Traditional)',
                                   'eng': 'English',
                                   'kor': 'Korean',
                                   'jpn': 'Japanese'}

    def ocr_parse_image(self, data):
        data['method'] = 'sendMessage'
        args = data['args'].strip().lower()
        language = 'eng'
        file_url = data.get('file_url', '')
        if args != '':
            if args in self.supported_language:
                language = args
            else:
                data['text'] = 'We only support 24 languages, e.g.\n' + ''.join(
                    ['{} - {}\n'.format(k, v) for k, v in self.supported_language.items()])
                return ''
        file_extension = splitext(file_url)[1].lower()
        if file_url == '':
            data['text'] = ('Please send a photo with caption /ocr\n'
                            'or reply a photo with command /ocr')
        elif file_extension not in self.supported_file_type:
            data['text'] = '{} file format is not supported'.format(file_extension)
        else:
            data['text'] = self.get_image_text(file_url, language, self.supported_file_type[file_extension])

    def post_ocr_space_url(self, url, language='eng', file_type='JPG'):
        params = {
            'apikey': self.api_key,
            'url': url,
            'language': language,
            'filetype': file_type
        }
        return HttpService.post_json(self.ocr_url, params)

    def get_image_text(self, url, language, file_type):
        resp = self.post_ocr_space_url(url, language, file_type)
        if isinstance(resp, dict):
            if resp.get('IsErroredOnProcessing', False):
                return resp.get('ErrorMessage', ['Error in getting error message!'])[0]
            elif len(resp.get('ParsedResults', [])) > 0:
                text = resp.get('ParsedResults')[0].get('ParsedText', 'Error in reading text!')
                if text == '':
                    return 'No text found in the image!'
                return text
        logger.error('ocr get_image_text: Error in processing image!')
        return 'Error in processing image!'
