#!/usr/bin/env python
"""Planet PostgreSQL - list synchronizer

This file contains the functions to synchronize the list of subscribers
to planet with those of a majordomo mailinglist.

Copyright (C) 2008 PostgreSQL Global Development Group
"""

import ConfigParser
import re
import psycopg2
import httplib
from urllib import urlopen, urlencode

class MajordomoInterface:
	"""
	Simple interface wrapping some majordomo commands through screenscraping
	the mj_wwwadm interface.
	"""

	def __init__(self, confp):
		self.mjhost = confp.get('list', 'server')
		self.listname = confp.get('list', 'listname')
		self.listpwd = confp.get('list', 'password')

	def fetch_current_subscribers(self):
		"""
		Fetch the current list of subscribers by calling out to the majordomo server
		and screenscrape the result of the 'who-short' command.
		"""

		f = urlopen("https://%s/mj/mj_wwwadm?passw=%s&list=%s&func=who-short" %
			(self.mjhost, self.listpwd, self.listname))
		s = f.read()
		f.close()

		# Ugly screen-scraping regexp hack
		resub = re.compile('list administration<br>\s+</p>\s+<pre>([^<]+)</pre>')
		m = resub.findall(s)
		if len(m) != 1:
			if s.find("<!-- Majordomo who_none format file -->") > 0:
				# Nobody on the list yet
				return set()
			raise Exception("Could not find list of subscribers")

		return set([a for a in re.split('[\s\n]+',m[0]) if a])

	def RemoveSubscribers(self, remove_subscribers):
		"""
		Remove the specified subscribers from the list.
		"""

		victims = "\r\n".join(remove_subscribers)
		self.__PostMajordomoForm({
			'func': 'unsubscribe-farewell',
			'victims': victims
		})

	def AddSubscribers(self, add_subscribers):
		"""
		Add the specified subscribers to the list.
		"""

		victims = "\r\n".join(add_subscribers)
		self.__PostMajordomoForm({
			'func': 'subscribe-set-welcome',
			'victims': victims
		})
	
	def __PostMajordomoForm(self, varset):
		"""
		Post a fake form to the majordomo mj_wwwadm interface with whatever
		variables are specified. Add the listname and password on top of what's
		already in the set of variables.
		"""

		var = varset
		var.update({
			'list': self.listname,
			'passw': self.listpwd
		})
		body = urlencode(var)

		h = httplib.HTTPS(self.mjhost)
		h.putrequest('POST', '/mj/mj_wwwadm')
		h.putheader('host', self.mjhost)
		h.putheader('content-type','application/x-www-form-urlencoded')
		h.putheader('content-length', str(len(body)))
		h.endheaders()
		h.send(body)
		errcode, errmsg, headers = h.getreply()
		if errcode != 200:
			print "ERROR: Form returned code %i, message %s" % (errcode, errmsg)
			print h.file.read()
			raise Exception("Aborting")


class Synchronizer:
	"""
	Perform the synchronization between the planet database and the
	majordomo list.
	"""

	def __init__(self, c, db):
		self.db = db
		self.mj = MajordomoInterface(c)

	def sync(self):
		self.subscribers = self.mj.fetch_current_subscribers()
		self.fetch_expected_subscribers()
		self.diff_subscribers()
		self.apply_subscriber_diff()

	def diff_subscribers(self):
		"""
		Generate a list of differences between the current and expected subscribers,
		so we know what to modify.
		"""

		self.remove_subscribers = self.subscribers.difference(self.expected)
		self.add_subscribers = self.expected.difference(self.subscribers)

	def apply_subscriber_diff(self):
		"""
		If there are any changes to subscribers to be made (subscribe or unsubscribe),
		send these commands to the majordomo admin interface using a http POST
		operation with a faked form.
		"""

		if len(self.remove_subscribers):
			self.mj.RemoveSubscribers(self.remove_subscribers)
			print "Removed %i subscribers" % len(self.remove_subscribers)
		if len(self.add_subscribers):
			self.mj.AddSubscribers(self.add_subscribers)
			print "Added %i subscribers" % len(self.add_subscribers)


	def fetch_expected_subscribers(self):
		"""
		Fetch the list of addresses that *should* be subscribed to the list by
		looking in the database.
		"""

		curs = self.db.cursor()
		curs.execute("""
SELECT email FROM admin.auth_user 
INNER JOIN planet.feeds ON admin.auth_user.username=planet.feeds.userid 
WHERE planet.feeds.approved
""")
		self.expected = set([r[0] for r in curs.fetchall()])



if __name__=="__main__":
	c = ConfigParser.ConfigParser()
	c.read('planet.ini')

	Synchronizer(c, psycopg2.connect(c.get('planet','db'))).sync()

