#!/usr/bin/env python3
# vim: ai ts=4 sts=4 sw=4
"""PostgreSQL Planet Aggregator

This file contains the functions to generate short
URLs and tweets from what's currently in the database.

Copyright (C) 2009-2019 PostgreSQL Global Development Group
"""

# Post links to articles on twitter

import psycopg2
import psycopg2.extensions
import simplejson as json
import configparser
from twitterclient import TwitterClient


# Simple map used to shorten id values to URLs
_urlvalmap = ['0', '1', '2', '3', '4', '5', '6', '7', '8', '9', 'a', 'b', 'c', 'd', 'e', 'f', 'g', 'h', 'i', 'j', 'k', 'l', 'm', 'n', 'o', 'p', 'q', 'r', 's', 't', 'u', 'v', 'w', 'x', 'y', 'z', 'A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J', 'K', 'L', 'M', 'N', 'O', 'P', 'Q', 'R', 'S', 'T', 'U', 'V', 'W', 'X', 'Y', 'Z', '-', '_']

class PostToTwitter(TwitterClient):
	def __init__(self, cfg):
		TwitterClient.__init__(self, cfg)

		psycopg2.extensions.register_type(psycopg2.extensions.UNICODE)
		self.db = psycopg2.connect(c.get('planet','db'))


	def do_post(self, msg):
		"""
		Actually make a post to twitter!
		"""
		r = self.tw.post('{0}statuses/update.json'.format(self.twitter_api), data={
			'status': msg,
		})
		if r.status_code != 200:
			raise Exception("Could not post to twitter, status code {0}".format(r.status_code))

	def Run(self):
		c = self.db.cursor()
		c.execute("""SELECT posts.id, posts.title, posts.link, posts.shortlink, feeds.name, feeds.twitteruser
			     FROM posts INNER JOIN feeds ON posts.feed=feeds.id
			     WHERE approved AND age(dat) < '7 days' AND NOT (twittered OR hidden) ORDER BY dat""")
		for post in c.fetchall():
			if post[3] and len(post[3])>1:
				short = post[3]
			else:
				# No short-link exists, so create one. We need the short-link
				# to twitter, and we store it separately in the database
				# in case it's needed.
				try:
					short = self.shortid(post[0])
				except Exception as e:
					print("Failed to shorten URL %s: %s" % (post[2], e))
					continue

				c.execute("UPDATE posts SET shortlink=%(short)s WHERE id=%(id)s", {
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
				self.do_post(msg)
			except Exception as e:
				print("Error posting to twitter (post %s): %s" % (post[0], e))
				# We'll just try again with the next one
				continue

			# Flag this item as posted
			c.execute("UPDATE posts SET twittered='t' WHERE id=%(id)s", { 'id': post[0] })
			self.db.commit()

			print("Twittered: %s" % msg)


	# Trim a post to the length required by twitter, so we don't fail to post
	# if a title is really long. Assume other parts of the string to be
	# posted are <otherlen> characters.
	def trimpost(self, txt, otherlen):
		if len(txt) + otherlen < 140:
			return txt
		return "%s..." % (txt[:(140-otherlen-3)])


	# Trim an URL using https://postgr.es
	def shortid(self, id):
		s = ""
		while id > 0:
			s = _urlvalmap[id % 64] + s
			id /= 64
		return "https://postgr.es/p/%s" % s



if __name__=="__main__":
	c = configparser.ConfigParser()
	c.read('planet.ini')
	PostToTwitter(c).Run()

