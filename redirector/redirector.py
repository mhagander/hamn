#!/usr/bin/env python3
"""PostgreSQL Planet Aggregator

This is a FastCGI implementation of the planet URL redirector.

Accepts URLs like /p/<shorturl> and sends a redirect to the proper
URL for the post requested.

Copyright (C) 2011 PostgreSQL Global Development Group
"""

import configparser
import psycopg2

# Simple map used to shorten id values to URLs
_urlvalmap = ['0', '1', '2', '3', '4', '5', '6', '7', '8', '9', 'a', 'b', 'c', 'd', 'e', 'f', 'g', 'h', 'i', 'j', 'k', 'l', 'm', 'n', 'o', 'p', 'q', 'r', 's', 't', 'u', 'v', 'w', 'x', 'y', 'z', 'A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J', 'K', 'L', 'M', 'N', 'O', 'P', 'Q', 'R', 'S', 'T', 'U', 'V', 'W', 'X', 'Y', 'Z', '-', '_']

connstr = ""


def iddecode(idstr):
    idval = 0
    for c in idstr:
        idval *= 64
        idval += _urlvalmap.index(c)
    return idval


def application(environ, start_response):
    try:
        # If we have a querystring, get rid of it. This can (presumably)
        # happen with some click-tracking systems.
        if '?' in environ['REQUEST_URI']:
            uri = environ['REQUEST_URI'].split('?')[0]
        else:
            uri = environ['REQUEST_URI']

        # Start by getting the id from the request
        id = iddecode(uri.split('/')[-1])

        # Let's figure out where this URL should be

        # Since we cache heavily with varnish in front of this, we don't
        # bother with any connection pooling.
        conn = psycopg2.connect(connstr)
        c = conn.cursor()
        c.execute("SELECT link FROM posts WHERE id=%(id)s", {
            'id': id
        })
        r = c.fetchall()

        conn.close()

        if len(r) != 1:
            start_response('404 Not Found', [
                ('Content-type', 'text/plain'),
            ])
            return [b"Link not found\n"]

        # We have a link, return a redirect to it
        start_response('301 Moved Permanently', [
            ('Content-type', 'text/html'),
            ('Location', r[0][0]),
            ('X-Planet', str(id))
        ])
        return [
            b"<html>\n<head>\n<title>postgr.es</title>\n</head>\n<body>\n",
            b"<a href=\"%s\">moved here</a>\n" % r[0][0].encode('utf8'),
            b"</body>\n</html>\n"
        ]
    except Exception as ex:
        start_response('500 Internal Server Error', [
            ('Content-type', 'text/plain')
        ])

        return [
            "An internal server error occured\n",
            str(ex)
        ]


c = configparser.ConfigParser()
c.read('redir.ini')
connstr = c.get('planet', 'db')
