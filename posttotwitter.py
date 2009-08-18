#!/usr/bin/env python

# python rss reader -> twitter post
import feedparser, pickle, os, sys, twitter, urllib, simplejson as json

class RSS2Twitter:
	def __init__(self, filename, url, username, passwd):
		self.filename=filename
		self.url=url
		self.username=username
		self.passwd=passwd
		self.twApi=twitter.Api(username=self.username, password=self.passwd)

		if os.path.exists(self.filename):
			self.itemsDB = pickle.load(file(filename, 'r+b'))
		else:
			self.itemsDB = {} 

	def getLatestFeedItems(self, items = 10):
		feed=feedparser.parse(self.url);
		it=feed["items"]
		it_ret=it[0:items]
		return it_ret

	def twitIt(self, items):
		oldItems=pItems=0
		items.sort(reverse=True)
		for it in items:
			if self.itemPublished(it) == None:
				trim = json.loads(self.trim(it["link"]))
				txt=it["title"] +" "+trim["url"]
				# print txt
				try: 
					status = self.twApi.PostUpdate(txt)
				except IOError, e:
					raise e
				pItems=pItems+1
		# print "Total items: ", len(items)
		# print "published: ",pItems
		# print "old stuff: ",len(items) - pItems

	def itemPublished (self, item):
		if self.itemsDB.has_key(item["link"]) == True:
			return True
		else:
			self.itemsDB[item["link"]]=item["title"]
			pickle.dump(self.itemsDB, file(self.filename, 'w+b'))
		return None

	def trim(self, url):
		try:
			data = urllib.urlencode(dict(url=url, source="RSS2Twit"))
			encodedurl="http://tr.im/api/trim_url.json?"+data
			instream=urllib.urlopen(encodedurl)
			ret=instream.read()
			instream.close()
			if len(ret)==0:
				return url
			return ret
		except IOError, e:
			raise "urllib error."

	def tiny(self, url):
		try:
			data = urllib.urlencode(dict(url=url, source="RSS2Twit"))
			encodedurl="http://www.tinyurl.com/api-create.php?"+data
			instream=urllib.urlopen(encodedurl)
			ret=instream.read()
			instream.close()
			if len(ret)==0:
				return url
			return ret
		except IOError, e:
			raise "urllib error."

if __name__ == "__main__":
	# run it like python rss2twitter.py oi.dat (oi.dat is the posted item db)
	# update username and passwd with your twitter account data, surrounding them with quotes.
	url="http://planet.postgresql.org/rss20_short.xml"
	r2t=RSS2Twitter(sys.argv[1], url, 'planetpostgres', 'pl4n3t.pg')
	its=r2t.getLatestFeedItems()
	r2t.twitIt(its)
