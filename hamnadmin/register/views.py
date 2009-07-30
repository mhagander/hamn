from django.http import HttpResponse, HttpResponseRedirect
from django.template import RequestContext
from django.shortcuts import render_to_response, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.conf import settings
from django.core.mail import send_mail
from django.db import transaction
from django.db.models import Q

from hamnadmin.register.models import *
from hamnadmin.exceptions import pExcept

import socket
import feedparser

def issuperuser(user):
	return user.is_authenticated() and user.is_superuser

@login_required
def root(request):
	if request.user.is_superuser:
		blogs = Blog.objects.all()
	else:
		blogs = Blog.objects.filter(userid=request.user.username)
	return render_to_response('index.html',{
		'blogs': blogs,
		'teams': Team.objects.all(),
	}, context_instance=RequestContext(request))

@login_required
@transaction.commit_on_success
def new(request):
	if not request.method== 'POST':
		raise pExcept('must be POST')
	feedurl = request.POST['feedurl']
	user = request.user.username
	authorfilter  = request.POST['authorfilter']
	if not len(feedurl) > 1:
		raise pExcept('must include blog url!')

	# TODO: add support for 'feed://' urls
	if not feedurl.startswith('http://'):
		raise pExcept('Only http served blogs are accepted!')

	# See if this blog is already registered
	try:
		blog = Blog.objects.get(
			Q(feedurl=feedurl),
			Q(authorfilter=authorfilter)
		)
		raise pExcept('This blog is already registered.')
	except Blog.DoesNotExist:
		# This is what we expect to happen.. :-)
		pass

	# Attempting to join a team?
	if int(request.POST['team']) != -1:
		print "team: %s" % request.POST['team']
		if not (request.POST.has_key('ok_team') and request.POST['ok_team'] == 'yesitsfine'):
			raise pExcept('You must confirm that the owner of the team knows about you joining it.')
		try:
			team = Team.objects.get(pk=int(request.POST['team']))
		except:
			raise pExcept('Failed to get team information!')
	else:
		team = None

	# Attempting to register a new blog. First let's see that we can download it
	socket.setdefaulttimeout(20)
	try:
		feed = feedparser.parse(feedurl)
		status = feed.status
		lnk = feed.feed.link
		l = len(feed.entries)
		if l < 1:
			raise pExcept('Blog feed contains no entries.')

	except Exception, e:
		raise pExcept('Failed to download blog feed')
	if not status == 200:
		raise pExcept('Attempt to download blog feed returned status %s.' % (status))
	
	if not settings.NOTIFYADDR:
		raise pExcept('Notify address not specified, cannot complete')

	blog = Blog()
	blog.userid = request.user.username
	blog.name = request.user.first_name

	blog.feedurl = feedurl
	blog.authorfilter = authorfilter
	blog.blogurl = lnk
	blog.approved = False
	if team:
		blog.team = team
	send_mail('New blog assignment', """
The user '%s' has requested the blog at
%s (name %s)
is added to Planet PostgreSQL!

So, head off to the admin interface and approve or reject this!
http://planet.postgresql.org/register/admin/register/blog/
""" % (blog.userid, blog.feedurl, blog.name), 'webmaster@postgresql.org', [settings.NOTIFYADDR])

	blog.save()
	AuditEntry(request.user.username, 'Added blog %s' % blog.feedurl).save()
	return HttpResponseRedirect('..')

@login_required
@transaction.commit_on_success
def delete(request, id):
	blog = get_object_or_404(Blog, id=id)
	if not blog.userid == request.user.username:
		raise pError("You can only delete your own feeds! Don't try to hack!")
	send_mail('Blog deleted', """
The user '%s' has deleted the blog at
%s (name %s)
""" % (blog.userid, blog.feedurl, blog.name), 'webmaster@postgresql.org', [settings.NOTIFYADDR])
	blog.delete()
	AuditEntry(request.user.username, 'Deleted blog %s' % blog.feedurl).save()
	return HttpResponseRedirect('../..')

@user_passes_test(issuperuser)
@transaction.commit_on_success
def discover(request, id):
	blog = get_object_or_404(Blog, id=id)

	# Attempt to run the discover
	socket.setdefaulttimeout(20)
	try:
		feed = feedparser.parse(blog.feedurl)
		if not blog.blogurl == feed.feed.link:
			blog.blogurl = feed.feed.link
			blog.save()
			AuditEntry(request.user.username, 'Discovered metadata for %s' % blog.feedurl).save()
	except Exception, e:
		return HttpResponse('Failed to discover metadata: %s' % (e))

	return HttpResponseRedirect('../..')

@login_required
def logview(request, id):
	blog = get_object_or_404(Blog, id=id)
	if not blog.userid == request.user.username and not request.user.is_superuser:
		return HttpResponse("You can't view the log for somebody elses blog!")
		
	logentries = AggregatorLog.objects.filter(feed=blog)[:50]
	
	return render_to_response('aggregatorlog.html', {
		'entries': logentries,
	}, context_instance=RequestContext(request))

@login_required
@transaction.commit_on_success
def blogposts(request, id):
	blog = get_object_or_404(Blog, id=id)
	if not blog.userid == request.user.username and not request.user.is_superuser:
		return HttpResponse("You can't view/edit somebody elses blog!")
	
	posts = Post.objects.filter(feed=blog)

	return render_to_response('blogposts.html',{
		'posts': posts,
	}, context_instance=RequestContext(request))

def __getvalidblogpost(request, blogid, postid):
	blog = get_object_or_404(Blog, id=blogid)
	post = get_object_or_404(Post, id=postid)
	if not blog.userid == request.user.username and not request.user.is_superuser:
		raise pExcept("You can't view/edit somebody elses blog!")
	if not post.feed.id == blog.id:
		raise pExcept("Blog does not match post")
	return post

def __setposthide(request, blogid, postid, status):
	post = __getvalidblogpost(request, blogid, postid)
	post.hidden = status
	post.save()
	AuditEntry(request.user.username, 'Set post %s on blog %s visibility to %s' % (postid, blogid, status)).save()
	return HttpResponseRedirect('../..')

@login_required
@transaction.commit_on_success
def blogpost_hide(request, blogid, postid):
	return __setposthide(request, blogid, postid, True)

@login_required
@transaction.commit_on_success
def blogpost_unhide(request, blogid, postid):
	return __setposthide(request, blogid, postid, False)

@login_required
@transaction.commit_on_success
def blogpost_delete(request, blogid, postid):
	post = __getvalidblogpost(request, blogid, postid)

	post.delete()
	AuditEntry(request.user.username, 'Deleted post %s from blog %s' % (postid, blogid)).save()
	return HttpResponseRedirect('../..')
