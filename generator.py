#!/usr/bin/env python
"""PostgreSQL Planet Aggregator

This file contains the functions to generate output RSS and
HTML data from what's currently in the database.

Copyright (C) 2008 PostgreSQL Global Development Group
"""

import psycopg2
import PyRSS2Gen
import datetime
import sys
from HTMLParser import HTMLParser
from planethtml import PlanetHtml

class Generator:
	def __init__(self,db):
		self.db = db

	def Generate(self):
		rss = PyRSS2Gen.RSS2(
			title = 'Planet PostgreSQL',
			link = 'http://planet.postgresql.org',
			description = 'Planet PostgreSQL',
			generator = 'Planet PostgreSQL',
			lastBuildDate = datetime.datetime.utcnow())
		html = PlanetHtml()

		c = self.db.cursor()
		c.execute("SET TIMEZONE=GMT")
		c.execute("SELECT guid,link,dat,title,txt,name,blogurl,guidisperma FROM planet.posts INNER JOIN planet.feeds ON planet.feeds.id=planet.posts.feed ORDER BY dat DESC LIMIT 30")
		for post in c.fetchall():
			desc = self.TruncateAndCleanDescription(post[4], post[3])
			rss.items.append(PyRSS2Gen.RSSItem(
				title=post[5] + ': ' + post[3],
				link=post[1],
				guid=PyRSS2Gen.Guid(post[0],post[7]),
				pubDate=post[2],
				description=desc))
			html.AddItem(post[0], post[1], post[2], post[3], post[5], post[6], desc)

		c.execute("SELECT name,blogurl,feedurl FROM planet.feeds ORDER BY name")
		for feed in c.fetchall():
			html.AddFeed(feed[0], feed[1], feed[2])

		rss.write_xml(open("www/rss20.xml","w"), encoding='utf-8')
		html.WriteFile("www/index.html")

	def TruncateAndCleanDescription(self, txt, title):
		ht = HtmlTruncator(1024, title)
		ht.feed(txt)
		out = ht.GetText()

		# Remove initial <br /> tags
		while out.startswith('<br'):
			out = out[out.find('>')+1:]

		return out

class HtmlTruncator(HTMLParser):
	def __init__(self, maxlen, title = None):
		HTMLParser.__init__(self)
		self.len = 0
		self.maxlen = maxlen
		self.fulltxt = ''
		self.trunctxt = ''
		self.tagstack = []
		self.skiprest = False
		self.title = title
	
	def feed(self, txt):
		txt = txt.lstrip()
		self.fulltxt += txt
		HTMLParser.feed(self, txt)

	def handle_startendtag(self, tag, attrs):
		if self.skiprest: return
		self.trunctxt += self.get_starttag_text()
	
	def handle_starttag(self, tag, attrs):
		if self.skiprest: return
		self.trunctxt += "<" + tag
		self.trunctxt += (' '.join([(' %s="%s"' % (k,v)) for k,v in attrs]))
		self.trunctxt += ">"
		self.tagstack.append(tag)

	def handle_endtag(self, tag):
		if self.skiprest: return
		self.trunctxt += "</" + tag + ">"
		self.tagstack.pop()

	def handle_entityref(self, ref):
		self.len += 1
		if self.skiprest: return
		self.trunctxt += "&" + ref + ";"

	def handle_data(self, data):
		self.len += len(data)
		if self.skiprest: return
		self.trunctxt += data
		if self.len > self.maxlen:
			# Passed max length, so truncate text as close to the limit as possible
			self.trunctxt = self.trunctxt[0:len(self.trunctxt)-(self.len-self.maxlen)]
			# Terminate at whitespace if possible, max 12 chars back
			for i in range(len(self.trunctxt)-1, len(self.trunctxt)-12, -1):
				if self.trunctxt[i].isspace():
					self.trunctxt = self.trunctxt[0:i] + " [...]"
					break

			# Now append any tags that weren't properly closed
			self.tagstack.reverse()
			for tag in self.tagstack:
				self.trunctxt += "</" + tag + ">"
			self.skiprest = True

	def GetText(self):
		if self.len > self.maxlen:
			return self.trunctxt
		else:
			return self.fulltxt

if __name__=="__main__":
	Generator(psycopg2.connect('dbname=planetpg host=/tmp')).Generate()
