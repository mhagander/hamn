#!/usr/bin/env python3
# vim: ai ts=4 sts=4 sw=4
"""PostgreSQL Planet Aggregator

This file contains simpler wrapper for getting the oauth credentials
to set up the twitter access.

Copyright (C) 2010 PostgreSQL Global Development Group
"""

import sys
import cgi
import configparser
import requests_oauthlib

cfg = configparser.ConfigParser()
cfg.read('planet.ini')

if not cfg.has_option('twitter', 'consumer') or not cfg.has_option('twitter', 'consumersecret'):
	print("Before you can run this, you need to register an application at")
	print("developer.twitter.com and put the consumer and consumersecret values")
	print("in the [twitter] section of planet.ini.")
	sys.exit(1)

oauth = requests_oauthlib.OAuth1Session(cfg.get('twitter', 'consumer'), cfg.get('twitter', 'consumersecret'))
fetch_response = oauth.fetch_request_token('https://api.twitter.com/oauth/request_token')
auth_url = oauth.authorization_url('https://api.twitter.com/oauth/authorize')

print("Please go to {0} and log in".format(auth_url))
pin = input('Enter the PIN received here:')

oauth2 = requests_oauthlib.OAuth1Session(cfg.get('twitter', 'consumer'),
										 cfg.get('twitter', 'consumersecret'),
										 fetch_response.get('oauth_token'),
										 fetch_response.get('oauth_token_secret'),
										 verifier=pin)
tokens = oauth2.fetch_access_token('https://api.twitter.com/oauth/access_token')


print("Access token received.")
print("Register the following two valuesi n planet.ini under [twitter]:")
print("token={0}".format(tokens.get('oauth_token')))
print("secret={0}".format(tokens.get('oauth_token_secret')))



