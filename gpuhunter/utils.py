import json
import os.path

from constants import DATA_DIR


def json_dumps(obj, *args, **kwargs):
    kwargs.setdefault("ensure_ascii", False)
    return json.dumps(obj, *args, **kwargs)


def url_set_params(url, **params):
    import urllib.parse as urlparse
    from urllib.parse import urlencode

    pr = urlparse.urlparse(url)
    query = dict(urlparse.parse_qsl(pr.query))
    for name, value in params.items():
        if value is not None:
            if type(value) in (str, int, float):
                query[name] = value
            else:
                query[name] = json_dumps(value)
    prlist = list(pr)
    prlist[4] = urlencode(query)
    return urlparse.ParseResult(*prlist).geturl()


def save_data(filename, data):
    with open(os.path.join(DATA_DIR, filename), "w", encoding="utf-8") as f:
        json_dumps(data, f)


def load_data(filename):
    with open(os.path.join(DATA_DIR, filename), "w", encoding="utf-8") as f:
        return json.load(f)
