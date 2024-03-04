import requests

from gpuhunter.utils.helpers import url_set_params
from main import logger


class RequestError(Exception):
    pass


class AutodlClient:
    def __init__(self, **kwargs):
        self.api_host = "https://api.autodl.com"
        self.backend_host = "https://fe-config-backend.autodl.com"
        self.token = None
        self.__dict__.update(kwargs)
        self._conf = kwargs

    def get_regions(self, **kwargs):
        """
        :return: [
            {
              "region_sign": [
                "west-B",
                "west-C"
              ],
              "region_name": "西北B区",
              "data_center": "westDC3",
              "visible": "all",
              "used_for": "all",
              "setting": {
                "clone_instance": true
              },
              "clone_instance": true,
              "tag_name": "",
              "tag_color": "#FF0000"
            }
        ]
        """
        api = "https://fe-config-backend.autodl.com/api/v1/autodl/region/tag"
        params = {
            **kwargs,
        }
        return self.request(api, params=params, method="GET")

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
        url = api_url if api_url.startswith("https://") else f"{self.api_host}{api_url}"
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
        if json["code"] not in ["Success", "OK"]:
            logger.error(json)
            raise RequestError(json["msg"])
        else:
            logger.debug(json["data"])
            return json["data"]


def get_default():
    from gpuhunter.data_object import Config
    config = Config()
    config.load()
    client = AutodlClient(
        token=config.token
    )
    return client


autodl_client = get_default()
