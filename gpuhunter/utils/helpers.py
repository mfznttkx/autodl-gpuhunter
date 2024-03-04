import json


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


def snake_case(name):
    import re
    name = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', name)
    name = re.sub('__([A-Z])', r'_\1', name)
    name = re.sub('([a-z0-9])([A-Z])', r'\1_\2', name)
    name = re.sub(r'[.\-\s]+', r'_', name)
    name = name.strip('_').lower()
    return name


def camel_case(name):
    name = snake_case(name)
    name = ''.join(word.title() for word in name.split('_'))
    return name
