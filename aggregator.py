#!/usr/bin/env python
"""PostgreSQL Planet Aggregator

This file contains the functions to suck down RSS/Atom feeds 
(using feedparser) and store the results in a PostgreSQL database.

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
		self.authorfilter = None
		socket.setdefaulttimeout(20)
		
	def Update(self):
		feeds = self.db.cursor()
		feeds.execute('SELECT id,feedurl,name,lastget,authorfilter FROM planet.feeds')
		for feed in feeds.fetchall():
			try:
				self.ParseFeed(feed)
			except Exception, e:
				print "Exception when parsing feed '%s': %s" % (feed[1], e)
				self.db.rollback()
			self.db.commit()

	def ParseFeed(self, feedinfo):
		#print "Loading feed %s" % (feedinfo[1])
		parsestart = datetime.datetime.now()
		feed = feedparser.parse(feedinfo[1], modified=feedinfo[3].timetuple())

		if feed.status == 304:
			# not changed
			return
		if feed.status != 200:
			# not ok!
			print "Feed %s status %s" % (feedinfo[1], feed.status)
			return

		self.authorfilter = feedinfo[4]

		for entry in feed.entries:
			if not self.matches_filter(entry):
				continue
				
			# Grab the entry. At least atom feeds from wordpress store what we
			# want in entry.content[0].value and *also* has a summary that's
			# much shorter. Other blog software store what we want in the summary
			# attribute. So let's just try one after another until we hit something.
			try:
				txt = entry.content[0].value
			except:
				txt = ''
			if txt == '' and entry.has_key('summary'):
				txt = entry.summary
			if txt == '':
				print "Failed to get text for entry at %s" % entry.link
				continue

			if entry.has_key('guidislink'):
				guidisperma = entry.guidislink
			else:
				guidisperma = True
			self.StoreEntry(feedinfo[0], entry.id, entry.date, entry.link, guidisperma, entry.title, txt)
		self.db.cursor().execute("UPDATE planet.feeds SET lastget=COALESCE((SELECT max(dat) FROM planet.posts WHERE planet.posts.feed=planet.feeds.id),'2000-01-01') WHERE planet.feeds.id=%(feed)s", {'feed': feedinfo[0]})
		#self.db.cursor().execute('UPDATE planet.feeds SET lastget=%(lg)s WHERE id=%(feed)s', {'lg':parsestart, 'feed': feedinfo[0]})

	def matches_filter(self, entry):
		# For now, we only match against self.authorfilter. In the future,
		# there may be more filters.
		if self.authorfilter:
			# Match against an author filter
			
			if entry.has_key('author_detail'):
				return entry.author_detail.name == self.authorfilter
			else: 
				return False

		# No filters, always return true
		return True

	def StoreEntry(self, feedid, guid, date, link, guidisperma, title, txt):
		c = self.db.cursor()
		c.execute("SELECT id FROM planet.posts WHERE feed=%(feed)s AND guid=%(guid)s", {'feed':feedid, 'guid':guid})
		if c.rowcount > 0:
			return
		print "Store entry %s from feed %s" % (guid, feedid)
		c.execute("INSERT INTO planet.posts (feed,guid,link,guidisperma,dat,title,txt) VALUES (%(feed)s,%(guid)s,%(link)s,%(guidisperma)s,%(date)s,%(title)s,%(txt)s)",
			{'feed': feedid,
			 'guid': guid,
			 'link': link,
			 'guidisperma': guidisperma,
			 'date': date,
			 'title': title,
			 'txt': txt})
		self.stored += 1

if __name__=="__main__":
	c = ConfigParser.ConfigParser()
	c.read('planet.ini')
	Aggregator(psycopg2.connect(c.get('planet','db'))).Update()
