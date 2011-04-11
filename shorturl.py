#!/usr/bin/env python

import sys

# Simple map used to shorten id values to URLs
_urlvalmap = ['0', '1', '2', '3', '4', '5', '6', '7', '8', '9', 'a', 'b', 'c', 'd', 'e', 'f', 'g', 'h', 'i', 'j', 'k', 'l', 'm', 'n', 'o', 'p', 'q', 'r', 's', 't', 'u', 'v', 'w', 'x', 'y', 'z', 'A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J', 'K', 'L', 'M', 'N', 'O', 'P', 'Q', 'R', 'S', 'T', 'U', 'V', 'W', 'X', 'Y', 'Z', '-', '_']

def shortid(id):
	s = ""
	while id > 0:
		s = _urlvalmap[id % 64] + s
		id /= 64
	return "http://postgr.es/p/%s" % s


if len(sys.argv) != 2:
	print "Usage: shorturl.py <id>"
	sys.exit(1)

id = int(sys.argv[1])

print "%s -> %s" % (id, shortid(id))
