import json
from types import SimpleNamespace

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
        #avoid TypeError: 'JsonObject' object is not subscriptable
        return JsonObject()     

class JsonUtil():
    @staticmethod
    def to_json_obj(data):
        if isinstance(data, dict):
            data = json.dumps(data)
        return json.loads(data, object_hook=lambda d: JsonObject(**d))

class NumberUtil():
    @staticmethod
    def is_float(s):
        try: 
            float(s)
            return True
        except ValueError:
            return False
