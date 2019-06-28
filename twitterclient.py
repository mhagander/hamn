#!/usr/bin/env python3
# vim: ai ts=4 sts=4 sw=4
"""PostgreSQL Planet Aggregator

This file contains a base class for twitter integration
scripts.

Copyright (C) 2009-2019 PostgreSQL Global Development Group
"""
import requests_oauthlib

class TwitterClient(object):
	"""
	Base class representing a twitter client, implementing all those twitter
	API calls that are in use.
	Does not attempt to be a complete twitter client, just to fill the needs
	for the planet software.
	"""

	def __init__(self, cfg):
		"""
		Initialize the instance. The parameter cfg is a ConfigParser object
		that has loaded the planet.ini file.
		"""
		self.twittername = cfg.get('twitter', 'account')
		self.twitterlist = cfg.get('twitter', 'listname')

		self.tw = requests_oauthlib.OAuth1Session(cfg.get('twitter', 'consumer'),
												  cfg.get('twitter', 'consumersecret'),
												  cfg.get('twitter', 'token'),
												  cfg.get('twitter', 'secret'))

		self.twitter_api = 'https://api.twitter.com/1.1/'

	def list_subscribers(self):
		# Eek. It seems subscribers are paged even if we don't ask for it
		# Thus, we need to loop with multiple requests
		cursor=-1
		handles = []
		while cursor != 0:
			response = self.tw.get('{0}lists/members.json'.format(self.twitter_api), params={
				'owner_screen_name': self.twittername,
				'slug': self.twitterlist,
				'cursor': cursor,
				})
			if response.status_code != 200:
				print(response.json())
				raise Exception("Received status {0} when listing users".format(response.status_code))
			j = response.json()
			handles.extend([x['screen_name'].lower() for x in j['users']])
			cursor = j['next_cursor']

		return handles

	def remove_subscriber(self, name):
		print("Removing twitter user %s from list." % name)
		r = self.tw.post('{0}lists/members/destroy.json'.format(self.twitter_api), data={
			'owner_screen_name': self.twittername,
			'slug': self.twitterlist,
			'screen_name': name,
		})
		if r.status_code != 200:
			try:
				err = r.json()['errors'][0]['message']
			except:
				err = 'Response does not contain error messages with json'
			print("Failed to remove subscriber {0}: {1}".format(name, err))
			return False
		return True

	def add_subscriber(self, name):
		print("Adding twitter user %s to list." % name)
		r = self.tw.post('{0}lists/members/create.json'.format(self.twitter_api), data={
			'owner_screen_name': self.twittername,
			'slug': self.twitterlist,
			'screen_name': name,
		})
		if r.status_code != 200:
			try:
				err = r.json()['errors'][0]['message']
			except:
				err = 'Response does not contain error messages with json'
			print("Failed to add subscriber {0}: {1}".format(name, err))
			return False
		return True
