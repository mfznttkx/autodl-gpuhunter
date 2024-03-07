import json
import os

from gpuhunter.utils.helpers import snake_case
from main import DATA_DIR


class DataObjectMixin:
    def __init__(self, **kwargs):
        self.__dict__.update(kwargs)

    @property
    def data_file(self):
        return f"{snake_case(self.__class__.__name__)}.json"

    def to_dict(self):
        return self.__dict__

    def save(self):
        with open(os.path.join(DATA_DIR, self.data_file), "w", encoding="utf-8") as f:
            json.dump(self.to_dict(), f, ensure_ascii=False, indent=2)
        return self

    def load(self):
        with open(os.path.join(DATA_DIR, self.data_file), "r", encoding="utf-8") as f:
            data = json.load(f)
            self.__dict__.update(data)
        return self

    def update(self):
        self.fetch()
        self.save()
        return self

    def fetch(self, **kwargs):
        pass


class Config(DataObjectMixin):
    token = None
    region_names = []
    gpu_type_names = []
    gpu_idle_num = 1
    instance_num = 1
    base_image_labels = ("", "", "", "")
    shared_image_keyword = ""
    shared_image_username_keyword = ""
    shared_image_version = ""
    private_image_uuid = ""
    private_image_name = ""
    expand_data_disk = 0
    clone_instance_uuid = ""
    copy_data_disk_after_clone = False
    keep_src_user_service_address_after_clone = True
    shutdown_instance_after_hours = 0
    shutdown_instance_today = True
    shutdown_hunter_after_finished = True
    retry_interval_minutes = 10
    mail_notify = False
    mail_receipt = ""
    mail_sender = ""
    mail_smtp_host = ""
    mail_smtp_port = 465
    mail_smtp_username = ""
    mail_smtp_password = ""


class RegionList(DataObjectMixin):
    list = None

    def fetch(self):
        from gpuhunter.autodl_client import autodl_client
        self.list = []
        for r in autodl_client.get_regions():
            self.list.append({
                **r,
                "gpu_types": [
                    {
                        "gpu_type": next(iter(g.keys())),
                        **next(iter(g.values())),
                    }
                    for g in autodl_client.get_region_gpu_types(r["region_sign"])
                ]
            })

    def get_gpu_stats(self, region_names=None):
        gpu_stats = []
        filtered = [r for r in self.list if not region_names or r["region_name"] in region_names]
        for r in filtered:
            for g in r["gpu_types"]:
                if existed := next((e for e in gpu_stats if e["gpu_type"] == g["gpu_type"]), None):
                    existed["idle_gpu_num"] += g["idle_gpu_num"]
                    existed["total_gpu_num"] += g["total_gpu_num"]
                else:
                    gpu_stats.append({**g})
        return gpu_stats

    def get_region_stats(self, gpu_types=None):
        region_stats = []
        for r in self.list:
            filtered = [g for g in r["gpu_types"] if not gpu_types or g["gpu_type"] in gpu_types]
            region_stats.append({
                "region_name": r["region_name"],
                "idle_gpu_num": sum(g["idle_gpu_num"] for g in filtered),
                "total_gpu_num": sum(g["total_gpu_num"] for g in filtered),
            })
        return region_stats
