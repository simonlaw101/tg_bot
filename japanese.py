import logging
import random
import re
import time
from bs4 import BeautifulSoup

from constant import Constant
from service import HttpService

logger = logging.getLogger('FxStock')


class Japanese:
    def __init__(self, kanji_api_key, jpn_module_lang='en', translate_api_key=None):
        self.cmds = {'kana': self.get_jpn_vocab, 'k1': self.start_quiz, 'kanji': self.search_kanji}
        self.desc = {'kana': 'get random japanese vocabulary', 'kanji': 'search a kanji'}
        self.examples = {'kana': Constant.KANA_EXAMPLE, 'kanji': Constant.KANJI_EXAMPLE}
        self.random_jpn_url = 'https://www.coolgenerator.com/random-japanese-words-generator'
        self.translate_url = 'https://translation.googleapis.com/language/translate/v2'
        self.translate_api_key = translate_api_key
        self.kanji_url = 'https://kanjialive-api.p.rapidapi.com/api/public/kanji/{}'
        self.kanji_api_key = kanji_api_key
        self.jpn_module_lang = jpn_module_lang

    def start_quiz(self, data):
        callback_data = dict(data)
        callback_data['method'] = 'answerCallbackQuery'
        del_msg_data = dict(data)
        del_msg_data['method'] = 'deleteMessage'
        send_poll_data = dict(data)
        # avoid replying to deleted group message
        send_poll_data['message_id'] = -1
        send_poll_data['method'] = 'sendPoll'
        send_poll_data['type'] = 'quiz'
        send_poll_data['is_anonymous'] = False
        quiz_data = self.generate_quiz(data['callback_msg_text'])
        send_poll_data['question'] = quiz_data['question']
        send_poll_data['options'] = quiz_data['options']
        send_poll_data['correct_option_id'] = quiz_data['correct_option_id']
        send_poll_data['explanation'] = quiz_data['explanation']
        # tg API doc: at least 5s and no more than 600s in the future
        send_poll_data['close_date'] = int(time.time()) + 30
        data['method'] = [callback_data, del_msg_data, send_poll_data]

    def generate_quiz(self, msg_text):
        vocabs = []
        for vocab_text in msg_text.split('\n\n'):
            furigana, ja, en_or_zh = vocab_text.split('\n')
            vocabs.append({'furigana': furigana.replace('[', '').replace(']', ''), 'ja': ja,
                           self.jpn_module_lang: en_or_zh})
        correct_option_id = random.randint(0, len(vocabs)-1)
        random.shuffle(vocabs)
        answer_vocab = vocabs[correct_option_id]
        quiz_type = random.randint(1, 2)
        question = answer_vocab['furigana'] if quiz_type == 1 else answer_vocab[self.jpn_module_lang]
        options = [vocab[self.jpn_module_lang] if quiz_type == 1 else vocab['furigana'] for vocab in vocabs]
        explanation = '[{}]\n<b>{}</b>\n{}'.format(answer_vocab['furigana'],
                                                   answer_vocab['ja'], answer_vocab[self.jpn_module_lang])
        return {'question': question, 'options': options,
                'correct_option_id': correct_option_id, 'explanation': explanation}

    def get_jpn_vocab(self, data):
        if data.get('callback_query_id', -1) != -1:
            data['method'] = 'editMessageText, answerCallbackQuery'
        else:
            data['method'] = 'sendMessage'
        random_jpn_lst = self.get_random_jpn()
        if len(random_jpn_lst) == 0:
            data['text'] = 'Error in getting japanese vocabulary!'
            return
        word_lst = ['[{}]\n<b>{}</b>\n{}'.format(dct['furigana'], dct['ja'], dct[self.jpn_module_lang])
                    for dct in random_jpn_lst]
        data['text'] = '\n\n'.join(word_lst)
        btn_lst = [[{'text': 'Start Quiz', 'callback_data': '/k1'}], [{'text': 'Refresh', 'callback_data': '/kana'}]]
        data['reply_markup'] = {'inline_keyboard': btn_lst}

    def get_random_jpn(self, no_of_word=4):
        # get random Japanese words from generator (at most 8)
        # add header to fix enable Javascript error
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/102.0.0.0 Safari/537.36'}
        page = HttpService.get(self.random_jpn_url, headers)
        soup = BeautifulSoup(page.content, 'html.parser')
        ele = soup.find('textarea', {'class': 'form-control'})
        if ele is None:
            return []
        text = ele.contents[0].replace('\r', '\n')
        jpn_lst = re.findall('word: (.+)]   \[meaning:', text)
        eng_lst = re.findall('\[meaning:(.+)] \n', text)

        # get chinese translation if enabled
        chi_lst = self.async_google_translate(eng_lst[:no_of_word]) if self.jpn_module_lang == 'zh' else []

        word_lst = []
        for i in range(no_of_word):
            tmp = jpn_lst[i].split('[')
            tmp_dct = {'ja': tmp[0], 'furigana': tmp[1], 'en': eng_lst[i]}
            if len(chi_lst) > 0:
                tmp_dct['zh'] = chi_lst[i]
            word_lst.append(tmp_dct)
        return word_lst

    def async_google_translate(self, texts, from_lang='en', to_lang='zh-TW'):
        query_params = {'q': '', 'source': from_lang, 'target': to_lang, 'key': self.translate_api_key}
        params_lst = []
        for text in texts:
            tmp_params = dict(query_params)
            tmp_params['q'] = text
            params_lst.append(tmp_params)
        json_resps = HttpService.async_post_json(self.translate_url, params_lst)
        return [self.get_translated_text(json_resp) for json_resp in json_resps]

    def get_translated_text(self, json_resp):
        return json_resp.get('data', {}).get('translations', [{}])[0].get('translatedText', '')

    def google_translate(self, text, from_lang='en', to_lang='zh-TW'):
        form_data_params = {'q': text, 'source': from_lang, 'target': to_lang, 'key': self.translate_api_key}
        json_resp = HttpService.post_json(self.translate_url, form_data_params)
        return self.get_translated_text(json_resp)

    def search_kanji(self, data):
        if data.get('callback_query_id', -1) != -1:
            data['method'] = 'editMessageText, answerCallbackQuery'
            headers = {'X-RapidAPI-Key': self.kanji_api_key, 'X-RapidAPI-Host': 'kanjialive-api.p.rapidapi.com'}
            json_resp = HttpService.get_json(self.kanji_url.format(data['args']), headers)
            examples = json_resp.get('examples', [])
            ex_lst = [{'ja': e.get('japanese', ''), 'en': e.get('meaning', {}).get('english', '')} for e in examples]
            eng_lst = [ex['en'] for ex in ex_lst]

            # get chinese translation if enabled
            if self.jpn_module_lang == 'zh':
                chi_lst = self.async_google_translate(eng_lst)
                template = '<b>{}</b>\n意思: {}\n\n'
            else:
                chi_lst = []
                template = '<b>{}</b>\nmeaning: {}\n\n'

            text = '<b>{}</b>\n\n'.format(data['args'])
            for i, ex in enumerate(ex_lst):
                en_or_zh = chi_lst[i] if len(chi_lst) > 0 else ex['en']
                text += template.format(ex['ja'], en_or_zh)
            data['text'] = text
            return
        data['method'] = 'sendMessage'
        args = data['args'].strip()
        r1 = re.compile(u'[\u4e00-\u9faf]')     # CJK unified ideographs - Common and uncommon Kanji
        r2 = re.compile(u'[\u3400-\u4dbf]')     # CJK unified ideographs Extension A - Rare Kanji
        if len(args) != 1 or (r1.search(args) is None and r1.search(args) is None):
            data['text'] = 'Please enter a kanji.'
            return
        headers = {'X-RapidAPI-Key': self.kanji_api_key, 'X-RapidAPI-Host': 'kanjialive-api.p.rapidapi.com'}
        resp = HttpService.get(self.kanji_url.format(args), headers)
        json_resp = resp.json() if resp else {'error': 'No kanji found.'}
        if 'error' in json_resp:
            data['text'] = 'Kanji not found'
            return
        kunyomi = json_resp['kunyomi']
        onyomi = json_resp['onyomi']
        meaning = json_resp['meaning']
        meaning = self.google_translate(meaning) if self.jpn_module_lang == 'zh' else meaning
        template = '<b>{}</b>\n\n訓讀: {}\n音讀: {}\n意思: {}' if self.jpn_module_lang == 'zh' \
            else '<b>{}</b>\n\nkunyomi: {}\nonyomi: {}\nmeaning: {}'
        data['text'] = template.format(args, kunyomi, onyomi, meaning)
        btn_lst = [[{'text': '查看例子' if self.jpn_module_lang == 'zh' else 'View examples',
                     'callback_data': '/kanji {}'.format(args)}]]
        data['reply_markup'] = {'inline_keyboard': btn_lst}
