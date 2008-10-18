#!/usr/bin/env python
"""PostgreSQL Planet Aggregator

This file contains the functions to generate HTML format output.
It's a fairly ugly hack compared to using a real template 
system, but...

Copyright (C) 2008 PostgreSQL Global Development Group
"""

import datetime

class PlanetHtml:
	def __init__(self):
		self.items = []
		self.feeds = []
		self.str = """<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Strict//EN"
    "http://www.w3.org/TR/xhtml1/DTD/xhtml1-strict.dtd">
<html xmlns="http://www.w3.org/1999/xhtml" lang="en" xml:lang="en" dir="ltr">
 <head>
  <title>Planet PostgreSQL</title>
  <meta http-equiv="Content-Type" content="text/xhtml; charset=utf-8" />
  <link rel="shortcut icon" href="/favicon.ico" />
  <link rel="alternate" type="application/rss+xml" title="Planet PostgreSQL" href="http://planet.postgresql.org/rss20.xml" />
  <style type="text/css" media="screen" title="Normal Text">@import url("css/planet.css");</style>
 </head>
 <body>
  <div align="center">
  <div id="planetHeader">
   <div class="fl"><img src="http://www.postgresql.org/layout/images/hdr_left.png" border="0" alt="PostgreSQL" /></div>
   <div class="fr"><img width="210" height="80" src="http://www.postgresql.org/layout/images/hdr_right.png" alt="The world's most advanced open source database" /></div>
   <div class="cb"></div>
  </div>
  <div id="planetMain">
"""

	def AddItem(self,guid,link,dat,title,author,blogurl,txt):
		self.items.append((guid,link,dat,title,author,blogurl,txt))

	def AddFeed(self,name,blogurl,feedurl):
		self.feeds.append((name,blogurl,feedurl))

	def BuildPosts(self):
		self.str += """   <div id="planetLeft">"""
		lastdate = None
		for post in self.items:
			if post[6].endswith('[...]'):
				txt = post[6][:len(post[6])-4] + """<a href="%s">continue reading...</a>]""" % (post[1])
			else:
				txt = post[6]
			
			if lastdate == None or lastdate != post[2].date():
				self.str += """
    <div class="planetNewDate">%s</div>""" % (post[2].date())
				lastdate = post[2].date()
    
			if post[5]:
				posterstr = """<a class="author" href="%s">%s</a>""" % (post[5], post[4])
			else:
				posterstr = post[4]

			self.str += """
    <div class="planetPost">
     <div class="planetPostTitle"><a href="%s">%s</a></div>
     <div class="planetPostAuthor">
      <div class="ppa_top">&nbsp;</div>
      <p>Posted by %s on <span class="date">%s at %s</span></p>
      <div class="ppa_bottom">&nbsp;</div>
      </div>
     <div class="planetPostContent">%s</div>
     <div class="cb"></div>
    </div>""" % (post[1], post[3], posterstr, post[2].date(), post[2].time(), txt)

		self.str += """   </div>"""

	def BuildRight(self):
		self.str += """   <div id="planetRight">
<div class="planetRightTitle">Subscriptions</div>
<ul>"""
		for feed in self.feeds:
			self.str += "<li>"
			if feed[1] != '':
				self.str += """<a href="%s">%s</a>""" % (feed[1], feed[0])
			else:
				self.str += feed[0]
			self.str += """
<a href="%s"><img border="0" src="http://www.postgresql.org/layout/images/ico_rss.png" /></a></li>""" % (feed[2]) 
		self.str += """   </ul>
    <div class="planetRightTitle">Feeds</div>
    <ul>
     <li><a href="rss20.xml">Planet PostgreSQL</a>  <a href="rss20.xml"><img border="0" src="http://www.postgresql.org/layout/images/ico_rss.png"></a></li>
    </ul>
   </div>
"""
	def WriteFile(self,filename):
		self.BuildPosts()
		self.BuildRight()
		self.str += """
  </div>
  </div>
 </div>
</body>
</html>
"""
		f = open(filename,"w")
		f.write(self.str)
		f.close()
