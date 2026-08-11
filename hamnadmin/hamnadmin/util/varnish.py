from django.conf import settings

import requests


def xkey(key):
    "Add a specific xkey to the page"
    def _xkey(fn):
        def __xkey(request, *_args, **_kwargs):
            resp = fn(request, *_args, **_kwargs)
            if 'xkey' in resp:
                resp['xkey'] += ' ' + key
            else:
                resp['xkey'] = key
            return resp
        return __xkey
    return _xkey


def purge_url(url):
    if not settings.VARNISH_URL:
        print("Not purging {0}".format(url))
    else:
        try:
            r = requests.get(settings.VARNISH_URL, headers={
                'X-Purge': '^' + url,
            })
            if r.status_code != 200:
                raise Exception("Invalid response code %s" % r.status_code)
        except Exception as e:
            raise Exception("Failed to purge '{0}': {1}'".format(url, e))


def purge_xkey(xkey):
    if not settings.VARNISH_URL:
        print("Not purging xkey {0}".format(xkey))
    else:
        try:
            r = requests.get(settings.VARNISH_URL, headers={
                'X-Purge-Key': xkey,
            })
            if r.status_code != 200:
                raise Exception("Invalid response code %s" % r.status_code)
        except Exception as e:
            raise Exception("Failed to purge xkey '{0}': {1}'".format(xkey, e))
