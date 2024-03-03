from gpuhunter.utils import save_data, load_data


class DataObjectMixin:
    data_file = None

    def __init__(self, **kwargs):
        self.__dict__.update(kwargs)

    def to_dict(self):
        return self.__dict__

    def save(self):
        save_data(self.data_file, self.to_dict())

    def load(self):
        return load_data(self.data_file)


class Config(DataObjectMixin):
    data_file = "config.json"

    def __init__(self, **kwargs):
        self.token = None
        super().__init__(**kwargs)
