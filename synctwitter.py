#!/usr/bin/env python
# vim: ai ts=4 sts=4 sw=4
"""PostgreSQL Planet Aggregator

This file contains the functions to synchronize the list
of twitter handles with a list on the twitter account.

Copyright (C) 2009-2010 PostgreSQL Global Development Group
"""

import psycopg2
import psycopg2.extensions
import ConfigParser
from twitterclient import TwitterClient

class SyncTwitter(TwitterClient):
	def __init__(self, cfg):
		TwitterClient.__init__(self, cfg)

		psycopg2.extensions.register_type(psycopg2.extensions.UNICODE)
		self.db = psycopg2.connect(c.get('planet','db'))

	def Run(self):
		# Get list of handles that should be on the list
		curs = self.db.cursor()
		curs.execute("SELECT DISTINCT lower(twitteruser) FROM planet.feeds WHERE NOT (twitteruser IS NULL OR twitteruser='') ORDER BY twitteruser");
		expected = set([r[0].replace('@','') for r in curs.fetchall()])

		# Get list of current screen names the list is following
		current = set(self.list_subscribers())

		# Start by deleting, then adding the new ones
		map(self.remove_subscriber, current.difference(expected))
		map(self.add_subscriber, expected.difference(current))


if __name__=="__main__":
	c = ConfigParser.ConfigParser()
	c.read('planet.ini')
	SyncTwitter(c).Run()
