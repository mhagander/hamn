#!/usr/bin/env python
# vim: ai ts=4 sts=4 sw=4
"""PostgreSQL Planet Aggregator

This file contains the functions to generate short
URLs and tweets from what's currently in the database.

Copyright (C) 2009 PostgreSQL Global Development Group
"""

# Post links to articles on twitter

import psycopg2
import twitter
import urllib
import simplejson as json
import ConfigParser


class PostToTwitter:
	def __init__(self, cfg):
		self.username=cfg.get('twitter','account')
		self.passwd=cfg.get('twitter','password')

		if cfg.has_option('tr.im','account'):
			self.trimuser = cfg.get('tr.im','account')
			self.trimpassword = cfg.get('tr.im','password')

		self.db = psycopg2.connect(c.get('planet','db'))

		# Only set up the connection to twitter when we know we're going to
		# post something.
		self._twitter = None

	@property
	def twitter(self):
		if not self._twitter:
			self._twitter=twitter.Api(username=self.username, password=self.passwd)
		return self._twitter


	def Run(self):
		c = self.db.cursor()
		c.execute("""SELECT posts.id, posts.title, posts.link, posts.shortlink, feeds.name, feeds.twitteruser
			     FROM planet.posts INNER JOIN planet.feeds ON planet.posts.feed=planet.feeds.id
			     WHERE approved AND NOT (twittered OR hidden) ORDER BY dat""")
		for post in c.fetchall():
			if post[3] and len(post[3])>1:
				short = post[3]
			else:
				# No short-link exists, so create one. We need the short-link
				# to twitter, and we store it separately in the database
				# in case it's needed.
				try:
					short = self.shortlink(post[2])
				except Exception, e:
					print "Failed to shorten URL %s: %s" % (post[2], e)
					continue

				c.execute("UPDATE planet.posts SET shortlink=%(short)s WHERE id=%(id)s", {
					'short': short,
					'id': post[0],
				})
				self.db.commit()

			# Set up the string to twitter
			if post[5] and len(post[5])>1:
				# Twitter username registered
				msg = "%s (@%s): %s %s" % (
					post[4],
					post[5],
					self.trimpost(post[1],len(post[4])+len(post[5])+len(short)+7),
					short,
				)
			else:
				msg = "%s: %s %s" % (
					post[4],
					self.trimpost(post[1],len(post[4])+len(short)+3),
					short,
				)

			# Now post it to twitter
			try:
				status = self.twitter.PostUpdate(msg)
			except Exception, e:
				print "Error posting to twitter: %s" % e
				# We'll just try again with the next one
				continue

			# Flag this item as posted
			c.execute("UPDATE planet.posts SET twittered='t' WHERE id=%(id)s", { 'id': post[0] })
			self.db.commit()

			print "Twittered: %s" % msg


	# Trim a post to the length required by twitter, so we don't fail to post
	# if a title is really long. Assume other parts of the string to be
	# posted are <otherlen> characters.
	def trimpost(self, txt, otherlen):
		if len(txt) + otherlen < 140:
			return txt
		return "%s..." % (txt[:(140-otherlen-3)])


	# Trim an URL using http://tr.im
	def shortlink(self, url):
		try:
			if self.trimuser:
				data = urllib.urlencode(dict(url=url, username=self.trimuser, password=self.trimpassword))
			else:
				data = urllib.urlencode(dict(url=url, ))
			encodedurl="http://api.tr.im/v1/trim_url.json?"+data
			instream=urllib.urlopen(encodedurl)
			ret=instream.read()
			instream.close()
		except Exception, e:
			raise "Failed in call to tr.im API: %s" % e

		if len(ret)==0:
			raise "tr.im returned blank!"

		try:
			trim = json.loads(ret)
			return trim['url']
		except Exception, e:
			raise "Failed to JSON parse tr.im response: %s" % e


if __name__=="__main__":
	c = ConfigParser.ConfigParser()
	c.read('planet.ini')
	PostToTwitter(c).Run()

