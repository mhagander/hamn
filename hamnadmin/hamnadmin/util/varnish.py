from django.conf import settings

import requests


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


def purge_root_and_feeds():
    purge_url('/(|rss20.*)$')
