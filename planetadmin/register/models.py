from django.db import models
from django.contrib.auth.models import User
from datetime import datetime

class Blog(models.Model):
	feedurl = models.CharField(max_length=255, blank=False)
	name = models.CharField(max_length=255, blank=False)
	blogurl = models.CharField(max_length=255, blank=False)
	lastget = models.DateTimeField(default='2000-01-01')
	userid = models.CharField(max_length=255, blank=False)
	approved = models.BooleanField()
	authorfilter = models.CharField(max_length=255,default='')

	def __str__(self):
		return self.feedurl

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
	feed = models.ForeignKey(Blog,db_column='feed')
	guid = models.CharField(max_length=255)
	link = models.CharField(max_length=255)
	txt = models.CharField(max_length=255)
	dat = models.DateTimeField()
	title = models.CharField(max_length=255)
	guidisperma = models.BooleanField()
	hidden = models.BooleanField()

	def __str__(self):
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

	def __str__(self):
		return "%s (%s): %s" % (self.logtime, self.user, self.logtxt)

	class Meta:
		db_table = 'planetadmin\".\"auditlog'
		ordering = ['logtime']
		
class AggregatorLog(models.Model):
	ts = models.DateTimeField()
	feed = models.ForeignKey(Blog, db_column='feed')
	success = models.BooleanField()
	info = models.TextField()
	
	class Meta:
		db_table = 'planet\".\"aggregatorlog'
		ordering = ['-ts']

