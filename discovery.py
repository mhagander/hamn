#!/usr/bin/env python
"""PostgreSQL Planet Aggregator

This file contains the functions to suck down RSS/Atom feeds 
(using feedparser), determining the actual blog URL (for the
HTML posts), and update the database with them.

Copyright (C) 2008 PostgreSQL Global Development Group
"""

import psycopg2
import feedparser
import datetime
import socket
import ConfigParser

class Aggregator:
	def __init__(self, db):
		self.db = db
		self.stored = 0
		socket.setdefaulttimeout(20)
		
	def Update(self):
		feeds = self.db.cursor()
		feeds.execute("SELECT id,feedurl,name,blogurl FROM planet.feeds WHERE blogurl='' AND feedurl NOT LIKE '%planet%'")
		for feed in feeds.fetchall():
			self.DiscoverFeed(feed)
		self.db.commit()

	def DiscoverFeed(self, feedinfo):
		feed = feedparser.parse(feedinfo[1])

		if feed.status != 200:
			# not ok!
			print "Feed %s status %s" % (feedinfo[1], feed.status)
			return

		try:
			if feed.feed.link:
				print "Setting feed for %s to %s" % (feedinfo[2], feed.feed.link)
				c = self.db.cursor()
				c.execute("UPDATE planet.feeds SET blogurl='%s' WHERE id=%i" % (feed.feed.link, feedinfo[0]))
		except:
			print "Exception when processing feed for %s" % (feedinfo[2])
			print feed

if __name__=="__main__":
	c = ConfigParser.ConfigParser()
	c.read('planet.ini')
	Aggregator(psycopg2.connect(c.get('planet','db'))).Update()
