import json
import math
from types import SimpleNamespace


class ArrayUtil:
    @staticmethod
    def reshape(lst, row=None, col=None):
        length = len(lst)
        if row is None and col is None:
            row = math.ceil(math.sqrt(length))
            col = math.floor(math.sqrt(length))
        elif row is None:
            row = math.ceil(length / col)
        elif col is None:
            col = math.ceil(length / row)
        return [lst[i * col:(i + 1) * col] for i in range(0, row)]


class JsonObject(SimpleNamespace):
    def __str__(self):
        if len(self.__dict__) > 0:
            return str(self.__dict__)
        return ''

    def __getattribute__(self, attr):
        try:
            return SimpleNamespace.__getattribute__(self, attr)
        except AttributeError:
            return JsonObject()

    def __len__(self):
        return len(self.__dict__)

    def __getitem__(self, key):
        # avoid TypeError: 'JsonObject' object is not subscriptable
        return JsonObject()     


class JsonUtil:
    @staticmethod
    def to_json_obj(data):
        if isinstance(data, dict):
            data = json.dumps(data)
        return json.loads(data, object_hook=lambda d: JsonObject(**d))


class NumberUtil:
    @staticmethod
    def is_float(s):
        try: 
            float(s)
            return True
        except (ValueError, TypeError):
            return False

    @staticmethod
    def format_num(num):
        num = str(num).replace(',', '')
        if not(NumberUtil.is_float(num)):
            return ''
        num = float(num)
        if num > 1000000000:
            return '{:,.3f}B'.format(num/1000000000)
        elif num > 1000000:
            return '{:,.3f}M'.format(num/1000000)
        return str(num)

    @staticmethod
    def format_num_chi(num):
        num = str(num).replace(',', '')
        if not(NumberUtil.is_float(num)):
            return ''
        num = float(num)
        if num > 100000000:
            return '{:,.3f}億'.format(num/100000000)
        elif num > 10000:
            return '{:,.3f}萬'.format(num/10000)
        return str(num)
