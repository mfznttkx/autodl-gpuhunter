import datetime
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


def time_of_day(d, t):
    if isinstance(d, datetime.date):
        return datetime.datetime.combine(d, t)
    elif isinstance(d, datetime.datetime):
        return d.replace(hour=t.hour, minute=t.minute, second=t.second, microsecond=t.microsecond)
    else:
        raise ValueError('Unsupported time type')


def end_of_day(d):
    return time_of_day(d, datetime.time(hour=23, minute=59, second=59, microsecond=999999))


def begin_of_day(d):
    return time_of_day(d, datetime.time(hour=0, minute=0, second=0, microsecond=0))
