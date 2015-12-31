#!/usr/bin/env python
"""PostgreSQL Planet Aggregator

This is a FastCGI implementation of the planet URL redirector.

Accepts URLs like /p/<shorturl> and sends a redirect to the proper
URL for the post requested.

Copyright (C) 2011 PostgreSQL Global Development Group
"""

import ConfigParser
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
		# Start by getting the id from the request
		id = iddecode(environ['PATH_INFO'].split('/')[-1])

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
			return ["Link not found\n"]

		# We have a link, return a redirect to it
		start_response('301 Moved Permanently', [
				('Content-type', 'text/html'),
				('Location', r[0][0]),
				('X-Planet', str(id))
				])
		return [
			"<html>\n<head>\n<title>postgr.es</title>\n</head>\n<body>\n",
			"<a href=\"%s\">moved here</a>\n" % r[0][0],
			"</body>\n</html>\n"
			]
	except Exception, ex:
		start_response('500 Internal Server Error', [
				('Content-type', 'text/plain')
				])

		return [
			"An internal server error occured\n",
			str(ex)
			]


c = ConfigParser.ConfigParser()
c.read('redir.ini')
connstr = c.get('planet', 'db')
