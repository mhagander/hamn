from django.db import models
from django.contrib.auth.models import User
from datetime import datetime, timedelta

from hamnadmin.util.shortlink import urlvalmap

class Team(models.Model):
	teamurl = models.CharField(max_length=255, blank=False)
	name = models.CharField(max_length=255, blank=False)
	manager = models.ForeignKey(User, null=True, blank=True)

	def __unicode__(self):
		return "%s (%s)" % (self.name, self.teamurl)

	class Meta:
		db_table = 'teams'

	class Admin:
		pass

class Blog(models.Model):
	feedurl = models.CharField(max_length=255, blank=False)
	name = models.CharField(max_length=255, blank=False)
	blogurl = models.CharField(max_length=255, blank=False)
	lastget = models.DateTimeField(default=datetime(2000,1,1))
	user = models.ForeignKey(User, null=False, blank=False)
	approved = models.BooleanField(default=False)
	archived = models.BooleanField(default=False)
	authorfilter = models.CharField(max_length=255,default='',blank=True)
	team = models.ForeignKey(Team,db_column='team', blank=True, null=True)
	twitteruser = models.CharField(max_length=255, default='', blank=True)
	excludestats = models.BooleanField(null=False, blank=False, default=False)

	def __unicode__(self):
		return "%s (%s)" % (self.name, self.feedurl)

	@property
	def email(self):
		return self.user.email

	@property
	def recent_failures(self):
		return self.aggregatorlog_set.filter(success=False, ts__gt=datetime.now()-timedelta(days=1)).count()

	@property
	def has_entries(self):
		return self.posts.filter(hidden=False).exists()

	@property
	def latestentry(self):
		try:
			return self.posts.filter(hidden=False)[0]
		except:
			return None

	@property
	def recent_entries(self):
		return self.posts.order_by('-dat')[:10]

	class Meta:
		db_table = 'feeds'
		ordering = ['approved','name']

	class Admin:
		pass

class Post(models.Model):
	feed = models.ForeignKey(Blog,db_column='feed',related_name='posts')
	guid = models.CharField(max_length=255)
	link = models.CharField(max_length=255)
	txt = models.TextField()
	dat = models.DateTimeField()
	title = models.CharField(max_length=255)
	guidisperma = models.BooleanField(default=False)
	hidden = models.BooleanField(default=False)
	twittered = models.BooleanField(default=False)
	shortlink = models.CharField(max_length=255)

	def __unicode__(self):
		return self.title

	class Meta:
		db_table = 'posts'
		ordering = ['-dat']
		unique_together = [
			('id', 'guid'),
		]

	class Admin:
		pass

	def update_shortlink(self):
		self.shortlink = self._get_shortlink()
		self.save()

	def _get_shortlink(self):
		s = ""
		i = self.id
		while i > 0:
			s = urlvalmap[i % 64] + s
			i /= 64
		return "https://postgr.es/p/%s" % s

class AuditEntry(models.Model):
	logtime = models.DateTimeField(default=datetime.now)
	user = models.CharField(max_length=32)
	logtxt = models.CharField(max_length=1024)

	def __init__(self, username, txt):
		super(AuditEntry, self).__init__()
		self.user = username
		self.logtxt = txt

	def __unicode__(self):
		return "%s (%s): %s" % (self.logtime, self.user, self.logtxt)

	class Meta:
		db_table = 'auditlog'
		ordering = ['logtime']
		
class AggregatorLog(models.Model):
	ts = models.DateTimeField(auto_now=True)
	feed = models.ForeignKey(Blog, db_column='feed')
	success = models.BooleanField()
	info = models.TextField()
	
	class Meta:
		db_table = 'aggregatorlog'
		ordering = ['-ts']

	def __unicode__(self):
		return "Log entry for %s (%s)" % (self.feed.name, self.ts)
