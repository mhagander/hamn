#!/usr/bin/env python
# vim: ai ts=4 sts=4 sw=4
"""PostgreSQL Planet Aggregator

This file contains the functions to generate short
URLs and tweets from what's currently in the database.

Copyright (C) 2009-2010 PostgreSQL Global Development Group
"""

# Post links to articles on twitter

import psycopg2
import psycopg2.extensions
import urllib
import simplejson as json
import ConfigParser
from twitterclient import TwitterClient


class PostToTwitter(TwitterClient):
	def __init__(self, cfg):
		TwitterClient.__init__(self, cfg)

		if cfg.has_option('bit.ly','account'):
			self.bitlyuser = cfg.get('bit.ly','account')
			self.bitlykey = cfg.get('bit.ly','apikey')

		psycopg2.extensions.register_type(psycopg2.extensions.UNICODE)
		self.db = psycopg2.connect(c.get('planet','db'))


	def do_post(self, msg):
		"""
		Actually make a post to twitter!
		"""
		ret_dict =self.twitter_request('statuses/update.json', 'POST', {
				'status': msg,
				})

		if ret_dict.has_key('created_at'):
			return
		if ret_dict.has_key('error'):
			raise Exception("Could not post to twitter: %s" % ret_dict['error'])
		raise Exception("Unparseable response from twitter: %s" % ret)

	def Run(self):
		c = self.db.cursor()
		c.execute("""SELECT posts.id, posts.title, posts.link, posts.shortlink, feeds.name, feeds.twitteruser
			     FROM planet.posts INNER JOIN planet.feeds ON planet.posts.feed=planet.feeds.id
			     WHERE approved AND age(dat) < '7 days' AND NOT (twittered OR hidden) ORDER BY dat""")
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
				msg = unicode("%s (@%s): %s %s") % (
					post[4],
					post[5],
					self.trimpost(post[1],len(post[4])+len(post[5])+len(short)+7),
					short,
				)
			else:
				msg = unicode("%s: %s %s") % (
					post[4],
					self.trimpost(post[1],len(post[4])+len(short)+3),
					short,
				)

			# Now post it to twitter
			try:
				self.do_post(msg)
			except Exception, e:
				print "Error posting to twitter (post %s): %s" % (post[0], e)
				# We'll just try again with the next one
				continue

			# Flag this item as posted
			c.execute("UPDATE planet.posts SET twittered='t' WHERE id=%(id)s", { 'id': post[0] })
			self.db.commit()

			print unicode("Twittered: %s" % msg).encode('utf8')


	# Trim a post to the length required by twitter, so we don't fail to post
	# if a title is really long. Assume other parts of the string to be
	# posted are <otherlen> characters.
	def trimpost(self, txt, otherlen):
		if len(txt) + otherlen < 140:
			return txt
		return "%s..." % (txt[:(140-otherlen-3)])


	# Trim an URL using http://bit.ly
	def shortlink(self, url):
		try:
			if self.bitlyuser:
				data = urllib.urlencode(dict(longUrl=url, domain='bit.ly', login=self.bitlyuser, apiKey=self.bitlykey))
			else:
				data = urllib.urlencode(dict(longUrl=url, ))
			encodedurl="http://api.bit.ly/v3/shorten?format=json&"+data
			instream=urllib.urlopen(encodedurl)
			ret=instream.read()
			instream.close()
		except Exception, e:
			raise Exception("Failed in call to bit.ly API: %s" % e)

		if len(ret)==0:
			raise "bit.ly returned blank!"

		try:
			trim = json.loads(ret)
			if not trim['status_txt'] == "OK":
				raise Exception("bit.ly status: %s" % trim['status_txt'])
			return trim['data']['url']
		except Exception, e:
			raise Exception("Failed to JSON parse tr.im response: %s" % e)


if __name__=="__main__":
	c = ConfigParser.ConfigParser()
	c.read('planet.ini')
	PostToTwitter(c).Run()

