from django.db import models
from django.contrib.auth.models import User
from datetime import datetime

class Team(models.Model):
	teamurl = models.CharField(max_length=255, blank=False)
	name = models.CharField(max_length=255, blank=False)

	def __unicode__(self):
		return "%s (%s)" % (self.name, self.teamurl)

	class Meta:
		db_table = 'planet\".\"teams'

	class Admin:
		pass

class Blog(models.Model):
	feedurl = models.CharField(max_length=255, blank=False)
	name = models.CharField(max_length=255, blank=False)
	blogurl = models.CharField(max_length=255, blank=False)
	lastget = models.DateTimeField(default=datetime(2000,1,1))
	userid = models.CharField(max_length=255, blank=False)
	approved = models.BooleanField()
	authorfilter = models.CharField(max_length=255,default='',blank=True)
	team = models.ForeignKey(Team,db_column='team', blank=True, null=True)

	def __unicode__(self):
		return "%s (%s)" % (self.name, self.feedurl)

	@property
	def email(self):
		u = User.objects.get(username=self.userid)
		return u.email

	class Meta:
		db_table = 'planet\".\"feeds'
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
	guidisperma = models.BooleanField()
	hidden = models.BooleanField()
	twittered = models.BooleanField()
	shortlink = models.TextField()

	def __unicode__(self):
		return self.title

	class Meta:
		db_table = 'planet\".\"posts'
		ordering = ['-dat']

	class Admin:
		pass


class AuditEntry(models.Model):
	logtime = models.DateTimeField(default=datetime.now)
	user = models.CharField(max_length=32)
	logtxt = models.CharField(max_length=1024)

	def __init__(self, userid, txt):
		super(AuditEntry, self).__init__()
		self.user = userid
		self.logtxt = txt

	def __unicode__(self):
		return "%s (%s): %s" % (self.logtime, self.user, self.logtxt)

	class Meta:
		db_table = 'admin\".\"auditlog'
		ordering = ['logtime']
		
class AggregatorLog(models.Model):
	ts = models.DateTimeField(auto_now=True)
	feed = models.ForeignKey(Blog, db_column='feed')
	success = models.BooleanField()
	info = models.TextField()
	
	class Meta:
		db_table = 'planet\".\"aggregatorlog'
		ordering = ['-ts']

	def __unicode__(self):
		return "Log entry (%s)" % self.ts
