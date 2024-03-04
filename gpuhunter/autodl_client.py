import time

import requests

from gpuhunter.utils.helpers import url_set_params
from main import logger

INSTANCE_RUNNING_STATUSES = ["creating", "starting", "running", "re_initializing"]


class RequestError(Exception):
    pass


class AutodlClient:
    def __init__(self, **kwargs):
        self.api_host = "https://api.autodl.com"
        self.backend_host = "https://fe-config-backend.autodl.com"
        self.token = None
        self.__dict__.update(kwargs)
        self._conf = kwargs

    def list_instance(self, status=None, **kwargs):
        """
        :param status: creating | starting | running | re_initializing | ...
        :return: [
          {
            "machine_id": "eaf141be95",
            "machine_alias": "091机",
            "region_sign": "west-X",
            "region_name": "西北企业区",
            "disk_expand_available": 2040109465600,
            "highest_cuda_version": "12.2",
            "status": "shutdown",
            ...
            "image": "hub.kce.ksyun.com/autodl-image/miniconda:cuda11.8-cudnn8-devel-ubuntu22.04-py310",
            "private_image_uuid": "",
            "reproduction_uuid": "comfyanonymous/ComfyUI/ComfyUI-SDXL09-12NewVersion-bobo-animatediff:v5",
            "reproduction_id": 471,
            "timed_shutdown_at": {
              "Time": "0001-01-01T00:00:00Z",
              "Valid": false
            },
            ...
          },
        ]
        """
        api = "/api/v1/instance"
        body = {
            "page_index": 1,
            "page_size": 100,
            "status": status if isinstance(status, (list, tuple)) else [status] if status else [],
            **kwargs,
        }
        page_index = 1
        while True:
            body['page_index'] = page_index
            data = self.request(api, body=body)
            for item in data['list']:
                yield item
            page_index += 1
            if page_index > data['max_page']:
                break
            time.sleep(0.2)

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

    def get_machine_list(self, region_sign_list, gpu_type_name, gpu_idle_num=1, **kwargs):
        """
        获取 GPU 主机列表，使用 list[0]["gpu_order_num"] 判断是否可可租。
        :param region_sign_list: ["beijing-A", "beijing-B"]
        :param gpu_type_name: ["RTX 4090", "RTX 3090"]
        :param gpu_idle_num:
        :return: {
          "machine_id": "2dd949a4cf",
          "machine_name": "agent-116-172-66-240",
          "machine_alias": "063机",
          ...
          "region_name": "西北B区",
          "region_sign": "west-B",
          "gpu_name": "RTX 4090",
          "gpu_order_num": 0,
          ...
          "highest_cuda_version": "12.2",
          "cpu_per_gpu": 22,
          "mem_per_gpu": 96636764160,
          "payg": true,
          "payg_price": 2720,
          "max_data_disk_expand_size": 2147483648000,
        }
        """
        api = "/api/v1/user/machine/list"
        body = {
            "charge_type": "payg",
            "page_index": 1,
            "page_size": 10,
            "gpu_idle_num": gpu_idle_num,
            "region_sign_list": region_sign_list,
            "gpu_type_name": gpu_type_name if isinstance(gpu_type_name, (list, tuple)) else [gpu_type_name],
            **kwargs,
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


def get_default_client():
    from gpuhunter.data_object import Config
    config = Config()
    config.load()
    client = AutodlClient(
        token=config.token
    )
    return client


def get_available_machines(region_sign_list, gpu_type_name, gpu_idle_num=1, **kwargs):
    return [
        mch
        for mch in autodl_client.get_machine_list(region_sign_list, gpu_type_name, gpu_idle_num, **kwargs)
        if mch["gpu_idle_num"] >= gpu_idle_num and mch["gpu_order_num"] >= gpu_idle_num
    ]


def get_running_instances(region_names=None, gpu_type_names=None, image=None, private_image_uuid=None,
                          reproduction_uuid=None, reproduction_id=None):
    def match(inst):
        return (region_names is None or inst["region_name"] in region_names) \
            and (gpu_type_names is None or inst["snapshot_gpu_alias_name"] in gpu_type_names) \
            and (image is None or inst["image"] == image) \
            and (private_image_uuid is None or inst["private_image_uuid"] == private_image_uuid) \
            and (reproduction_uuid is None or inst["reproduction_uuid"] == reproduction_uuid) \
            and (reproduction_id is None or inst["reproduction_id"] == reproduction_id)

    return [
        inst
        for inst in autodl_client.list_instance(INSTANCE_RUNNING_STATUSES)
        if match(inst)
    ]


autodl_client = get_default_client()
