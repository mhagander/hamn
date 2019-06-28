#!/usr/bin/env python3
# vim: ai ts=4 sts=4 sw=4
"""PostgreSQL Planet Aggregator

This file contains the functions to synchronize the list
of twitter handles with a list on the twitter account.

Copyright (C) 2009-2019 PostgreSQL Global Development Group
"""

import psycopg2
import psycopg2.extensions
import configparser
from twitterclient import TwitterClient

class SyncTwitter(TwitterClient):
	def __init__(self, cfg):
		TwitterClient.__init__(self, cfg)

		psycopg2.extensions.register_type(psycopg2.extensions.UNICODE)
		self.db = psycopg2.connect(cfg.get('planet','db'))

	def Run(self):
		# Get list of handles that should be on the list
		curs = self.db.cursor()
		curs.execute("SELECT DISTINCT lower(twitteruser) FROM feeds WHERE approved AND NOT (twitteruser IS NULL OR twitteruser='') ORDER BY lower(twitteruser)");
		expected = set([r[0].replace('@','') for r in curs.fetchall()])

		# Get list of current screen names the list is following
		current = set(self.list_subscribers())

		# Start by deleting, then adding the new ones
		for s in current.difference(expected):
			# We don't care about the return code and just keep running if it
			# fails, since we will try again later.
			self.remove_subscriber(s)
		for s in expected.difference(current):
			# If we fail to add a subscriber, stop trying
			if not self.add_subscriber(s):
				# Most likely it's things like it doesn't exist or we don't have permissions
				# to follow it.
				print("Failed to add twitter subscriber {0}, removing from feed record".format(s))

				# To be on the safe side, store the old twitter username. In case the twitter APIs
				# go bonkers on us and we end up removing too much.
				curs.execute("UPDATE feeds SET oldtwitteruser=twitteruser, twitteruser='' WHERE lower(twitteruser)=%(twitter)s", {
					'twitter': s,
				})
		self.db.commit()


if __name__=="__main__":
	c = configparser.ConfigParser()
	c.read('planet.ini')
	SyncTwitter(c).Run()
