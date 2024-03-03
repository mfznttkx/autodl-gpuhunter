import json


def json_dumps(obj, **kwargs):
    kwargs.setdefault("ensure_ascii", False)
    return json.dumps(obj, **kwargs)


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
