import logging
import requests

logger = logging.getLogger('FxStock')

class HttpService():
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
