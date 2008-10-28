#!/usr/bin/env python
"""PostgreSQL Planet Aggregator

This file contains helper classes used to store the data when
"communicating" with the templates to generate HTML output.

Copyright (C) 2008 PostgreSQL Global Development Group
"""

import datetime
import urllib

# Yes, a global function (!)
# Hmm. We only quote the ampersand here, since it's a HTML escape that
# shows up in URLs quote often.
def quoteurl(str):
	return str.replace('&','&amp;')

class PlanetPost:
	def __init__(self, guid,link,dat,title,author,blogurl,txt):
		self.guid = guid
		self.link = link
		self.dat = dat
		self.posttitle = title
		self.author = author
		self._blogurl = blogurl
		self.txt = txt


	def _get_blogurl(self):
		return quoteurl(self._blogurl)
	blogurl = property(_get_blogurl)

	def _get_datetime(self):
		return self.dat.strftime("%Y-%m-%d at %H:%M:%S")
	datetime = property(_get_datetime)

	def _get_contents(self):
		if self.txt.endswith("[...]"):
			self.txt = '%s<p>[<a href="%s">continue reading</a>]</p>' % (self.txt[:len(self.txt)-5], self.link)
		return self.txt
	contents = property(_get_contents)

	def _get_title(self):
		return self.posttitle
	title = property(_get_title)

class PlanetFeed:
	def __init__(self,name,blogurl,feedurl):
		self.name = name
		self._blogurl = blogurl
		self._feedurl = feedurl

	def _get_blogurl(self):
		return quoteurl(self._blogurl)
	blogurl = property(_get_blogurl)

	def _get_feedurl(self):
		return quoteurl(self._feedurl)
	feedurl = property(_get_feedurl)

