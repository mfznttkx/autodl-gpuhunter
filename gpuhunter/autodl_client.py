import requests

from gpuhunter.utils import url_set_params
from main import logger


class RequestError(Exception):
    pass


class AutodlClient:
    def __init__(self, **kwargs):
        self.api_host = "https://api.autodl.com"
        self.token = None

        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)
        self._conf = kwargs

    def get_region_gpu_types(self, region_sign_list, **kwargs):
        """
        :param region_sign_list: ["beijing-A", "beijing-B", "beijing-D", "beijing-E"]
        :param kwargs:
        :return: [
            {
                "RTX 4090": {
                    "idle_gpu_num": 3,
                    "total_gpu_num": 2686
                }
            },
            {
                "RTX 3090": {
                    "idle_gpu_num": 0,
                    "total_gpu_num": 444
                }
            },
        ],
        """
        api = "/api/v1/machine/region/gpu_type"
        body = {
            **kwargs,
            "region_sign_list": region_sign_list,
        }
        return self.request(api, body=body)

    def request(self, api_url, params=None, method="POST", body=None):
        url = f"{self.api_host}{api_url}"
        if params:
            url = url_set_params(url, **params)
        headers = {
            "Authorization": self.token,
            "Content-Type": "application/json"
        }
        logger.debug(url)
        logger.debug(method)
        logger.debug(body)
        response = requests.request(method, url, json=body, headers=headers)
        json = response.json()
        if json["code"] != "Success":
            logger.error(json)
            raise RequestError(json["msg"])
        else:
            logger.debug(json["data"])
            return json["data"]
