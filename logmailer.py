#!/usr/bin/env python
# vim: ai ts=4 sts=4 sw=4
"""PostgreSQL Planet Aggregator

This file contains the functions to email a report of failed fetches
by reading the aggregator log table in the database.

Current version just sends a single summary report. A future enhancement
could be to send reports directly to individual blog owners.

Copyright (C) 2009 PostgreSQL Global Development Group
"""

import psycopg2
import smtplib
import email.Message
import ConfigParser

class LogChecker(object):
	def __init__(self, cfg, db):
		self.cfg = cfg
		self.db = db
		
	def Check(self):
		c = self.db.cursor()
		c.execute("""SELECT ts,name,info FROM planet.aggregatorlog
	INNER JOIN planet.feeds ON feed=feeds.id 
	WHERE success='f' AND ts > CURRENT_TIMESTAMP-'24 hours'::interval
	ORDER BY name,ts""")
		if c.rowcount > 0:
			s = """
One or more of the blogs fetched in the past 24 hours caused an error
as listed below.

"""
			last = ""
			for r in c:
				if not last == r[1]:
					last = r[1]
					s += "\n"
				s += "%s  %-20s  %s\n" % (r[0].strftime("%Y%m%d %H:%M:%S"), r[1][:20], r[2])
			
			s += "\n\n"

			toAddr = self.cfg.get('notify','mailto')
			fromAddr = self.cfg.get('notify','mailfrom')
			
			msg = email.Message.Message()
			msg['To'] = toAddr
			msg['From'] = fromAddr
			msg['Subject'] = 'Planet PostgreSQL error summary'
			msg.set_payload(s)
			
			
			smtp = smtplib.SMTP('127.0.0.1')
			smtp.sendmail(fromAddr, toAddr, msg.as_string())
			smtp.quit()
		
			
if __name__=="__main__":
	c = ConfigParser.ConfigParser()
	c.read('planet.ini')
	LogChecker(c, psycopg2.connect(c.get('planet','db'))).Check()

