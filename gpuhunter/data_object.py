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

    def load(self):
        with open(os.path.join(DATA_DIR, self.data_file), "r", encoding="utf-8") as f:
            data = json.load(f)
            self.__dict__.update(data)


class Config(DataObjectMixin):
    token = None
