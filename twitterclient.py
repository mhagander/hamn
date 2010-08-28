#!/usr/bin/env python
# vim: ai ts=4 sts=4 sw=4
"""PostgreSQL Planet Aggregator

This file contains a base class for twitter integration
scripts.

Copyright (C) 2009-2010 PostgreSQL Global Development Group
"""
import oauth2 as oauth
import simplejson as json
import time
import urllib

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
		self.oauth_token = oauth.Token(cfg.get('twitter', 'token'), cfg.get('twitter', 'secret'))
		self.oauth_consumer = oauth.Consumer(cfg.get('twitter', 'consumer'), cfg.get('twitter', 'consumersecret'))

	def twitter_request(self, apicall, method='GET', ext_params=None):
		params = {
			'oauth_version': "1.0",
			'oauth_nonce': oauth.generate_nonce(),
			'oauth_timestamp': int(time.time()),
			'oauth_token': self.oauth_token.key,
			'oauth_consumer_key': self.oauth_consumer.key,
			}
		if ext_params:
			params.update(ext_params)

		url = "https://api.twitter.com/1/%s" % apicall

		req = oauth.Request(method=method,
							url=url,
							parameters=params)
		req.sign_request(oauth.SignatureMethod_HMAC_SHA1(), self.oauth_consumer, self.oauth_token)
		if method=='GET':
			instream = urllib.urlopen(req.to_url())
		else:
			instream=urllib.urlopen(url, req.to_postdata())

		# Make the actual call to twitter
		ret=instream.read()
		instream.close()
		return json.loads(ret)

	def list_subscribers(self):
		response = self.twitter_request('%s/subscribers/members.json' % self.twittername)
		return [x['screen_name'] for x in response['users']]

	def remove_subscriber(self, name):
		print "Removing twitter user %s from list." % name
		self.twitter_request('%s/subscribers/members.json' % self.twittername,'POST', {
				'id': name,
				'_method': 'DELETE',
				})

	def add_subscriber(self, name):
		print "Adding twitter user %s to list." % name
		self.twitter_request('%s/subscribers/members.json' % self.twittername, 'POST', {
				'id': name,
				})
