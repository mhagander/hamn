#!/usr/bin/env python
"""PostgreSQL Planet Aggregator

This file contains the functions to generate output RSS and
HTML data from what's currently in the database.

Copyright (C) 2008 PostgreSQL Global Development Group
"""

import psycopg2
import psycopg2.extensions
import PyRSS2Gen
import ConfigParser 
import datetime
import os.path
import sys
import tidy
import urllib
from django.template import Context
from django.template.loader import get_template
from django.conf import settings
from HTMLParser import HTMLParser
from planethtml import *

class Generator:
	def __init__(self,db):
		self.db = db
		self.tidyopts = dict(   drop_proprietary_attributes=1,
					alt_text='',
					hide_comments=1,
					output_xhtml=1,
					show_body_only=1,
					clean=1,
					char_encoding='utf8',
					)
		self.items = []
		self.feeds = []
		self.staticfiles = ['policy','add']

		settings.configure(
			TEMPLATE_DIRS=('template',),
		)

	def Generate(self):
		rss = PyRSS2Gen.RSS2(
			title = 'Planet PostgreSQL',
			link = 'http://planet.postgresql.org',
			description = 'Planet PostgreSQL',
			generator = 'Planet PostgreSQL',
			lastBuildDate = datetime.datetime.utcnow())
		rssshort = PyRSS2Gen.RSS2(
			title = 'Planet PostgreSQL (short)',
			link = 'http://planet.postgresql.org',
			description = 'Planet PostgreSQL (short)',
			generator = 'Planet PostgreSQL',
			lastBuildDate = datetime.datetime.utcnow())

		psycopg2.extensions.register_type(psycopg2.extensions.UNICODE)
		self.db.set_client_encoding('UTF8')
		c = self.db.cursor()
		c.execute("SET TIMEZONE=GMT")
		c.execute("SELECT guid,link,dat,title,txt,planet.feeds.name,blogurl,guidisperma,planet.teams.name,planet.teams.teamurl FROM planet.posts INNER JOIN planet.feeds ON planet.feeds.id=planet.posts.feed LEFT JOIN planet.teams ON planet.feeds.team = planet.teams.id WHERE planet.feeds.approved AND NOT planet.posts.hidden ORDER BY dat DESC LIMIT 30")
		for post in c.fetchall():
			desc = self.TruncateAndCleanDescription(post[4])
			rss.items.append(PyRSS2Gen.RSSItem(
				title=post[5] + ': ' + post[3],
				link=post[1],
				guid=PyRSS2Gen.Guid(post[0],post[7]),
				pubDate=post[2],
				description=post[4]))
			rssshort.items.append(PyRSS2Gen.RSSItem(
				title=post[5] + ': ' + post[3],
				link=post[1],
				guid=PyRSS2Gen.Guid(post[0],post[7]),
				pubDate=post[2],
				description=desc))
			self.items.append(PlanetPost(post[0], post[1], post[2], post[3], post[5], post[6], desc, post[8], post[9]))

		c.execute("SELECT name,blogurl,feedurl FROM planet.feeds WHERE approved ORDER BY name")
		for feed in c.fetchall():
			self.feeds.append(PlanetFeed(feed[0], feed[1], feed[2]))

		rss.write_xml(open("www/rss20.xml","w"), encoding='utf-8')
		rssshort.write_xml(open("www/rss20_short.xml","w"), encoding='utf-8')

		self.WriteFromTemplate('index.tmpl', 'www/index.html')
		for staticfile in self.staticfiles:
			self.UpdateStaticFile(staticfile)

	def WriteFromTemplate(self, templatename, outputname):
		tmpl = get_template(templatename)
		f = open(outputname, "w")
		f.write(tmpl.render(Context({
			'feeds': self.feeds,
			'posts': self.items,
		})).encode('utf-8'))
		f.close()

	def UpdateStaticFile(self, filename):
		if not os.path.exists("www/%s.html" % (filename)) or \
			os.path.getmtime("www/%s.html" % (filename)) < os.path.getmtime("template/%s.tmpl" % (filename)):
			print "Updating %s.html" % (filename)
			self.WriteFromTemplate("%s.tmpl" % (filename), "www/%s.html" % (filename))
		

	def TruncateAndCleanDescription(self, txt):
		# First apply Tidy
		txt = unicode(str(tidy.parseString(txt.encode('utf-8'), **self.tidyopts)),'utf8')

		# Then truncate as necessary
		ht = HtmlTruncator(4096)
		ht.feed(txt)
		out = ht.GetText()

		# Remove initial <br /> tags
		while out.startswith('<br'):
			out = out[out.find('>')+1:]

		return out

class HtmlTruncator(HTMLParser):
	def __init__(self, maxlen):
		HTMLParser.__init__(self)
		self.len = 0
		self.maxlen = maxlen
		self.fulltxt = ''
		self.trunctxt = ''
		self.tagstack = []
		self.skiprest = False
	
	def feed(self, txt):
		txt = txt.lstrip()
		self.fulltxt += txt
		HTMLParser.feed(self, txt)

	def handle_startendtag(self, tag, attrs):
		if self.skiprest: return
		self.trunctxt += self.get_starttag_text()
	
	def quoteurl(self, str):
		p = str.split(":",2)
		return p[0] + ":" + urllib.quote(p[1])

	def cleanhref(self, attrs):
		if attrs[0] == 'href':
			return 'href', self.quoteurl(attrs[1])
		return attrs

	def handle_starttag(self, tag, attrs):
		if self.skiprest: return
		self.trunctxt += "<" + tag
		self.trunctxt += (' '.join([(' %s="%s"' % (k,v)) for k,v in map(self.cleanhref, attrs)]))
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

			# Now append any tags that weren't properly closed
			self.tagstack.reverse()
			for tag in self.tagstack:
				self.trunctxt += "</" + tag + ">"
			self.skiprest = True

			# Finally, append the continuation chars
			self.trunctxt += "[...]"

	def GetText(self):
		if self.len > self.maxlen:
			return self.trunctxt
		else:
			return self.fulltxt

if __name__=="__main__":
	c = ConfigParser.ConfigParser()
	c.read('planet.ini')
	Generator(psycopg2.connect(c.get('planet','db'))).Generate()
