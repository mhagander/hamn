from django.http import HttpResponse, HttpResponseRedirect
from django.template import RequestContext
from django.shortcuts import render_to_response, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.conf import settings
from django.core.mail import send_mail
from django.db import transaction

from planetadmin.register.models import *
from planetadmin.exceptions import pExcept

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
	}, context_instance=RequestContext(request))

@login_required
@transaction.commit_on_success
def new(request):
	if not request.method== 'POST':
		raise pExcept('must be POST')
	feedurl = request.POST['feedurl']
	try: 
		user = request.POST['userid']
	except: 
		user = request.user.username
	authorfilter  = request.POST['authorfilter']
	if not len(feedurl) > 1:
		raise pExcept('must include blog url!')

	# See if we can find the blog already
	try:
		blog = Blog.objects.get(userid=userid)
	except:
		blog = None

	if blog:
		if blog.userid:
			raise pExcept("User %s has already registered blog %s." % (blog.userid, blog.feedurl))
		# Rest of this is not really useful, but will be modified so that a single user can have multiple blogs in the future
		# Found a match, so we're going to register this blog
		# For safety reasons, we're going to require approval before we do it as well :-P
		if not settings.NOTIFYADDR:
			raise pExcept('Notify address not specified, cannot complete')
		blog.userid = request.user.username
		blog.feedurl = feedurl
		blog.authorfilter = authorfilter
		blog.approved = False
		AuditEntry(request.user.username, 'Requested blog attachment for %s' % blog.feedurl).save()
		send_mail('New blog assignment', """
The user '%s' has requested the attachment of the blog at
%s
to his/her account. 

So, head off to the admin interface and approve or reject this!
""" % (blog.userid, blog.feedurl), 'webmaster@postgresql.org', [settings.NOTIFYADDR])
		blog.save()
		return HttpResponse('The blog has been attached to your account. For security reasons, it has been disapproved until a moderator has approved this connection.')

	# TODO: add support for 'feed://' urls
	if not feedurl.startswith('http://'):
		raise pExcept('Only http served blogs are accepted!')

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
	if issuperuser(request.user):
		blog.userid = request.POST['userid'] or request.user.username
		# Try to guess who's name should go on this blog, default to the current
		# users name if we can't find it in the feed.
		blog.name = request.user.first_name
		try:
			e = feed.entries[0]
			blog.name = e.author_detail.name or request.user.first_name
		except:
			pass
	else:
		blog.userid = request.user.username
		blog.name = request.user.first_name

	blog.feedurl = feedurl
	blog.authorfilter = authorfilter
	blog.blogurl = lnk
	blog.approved = False
	send_mail('New blog assignment', """
The user '%s' has requested the blog at
%s (name %s)
is added to Planet PostgreSQL!

So, head off to the admin interface and approve or reject this!
""" % (blog.userid, blog.feedurl, blog.name), 'webmaster@postgresql.org', [settings.NOTIFYADDR])

	blog.save()
	AuditEntry(request.user.username, 'Added blog %s' % blog.feedurl).save()
	return HttpResponseRedirect('..')

@login_required
@transaction.commit_on_success
def delete(request, id):
	blog = get_object_or_404(Blog, id=id)
	if not request.user.is_superuser:
		if not blog.userid == request.user.username:
			raise pError("You can only delete your own feeds! Don't try to hack!")
	send_mail('Blog deleted', """
The user '%s' has deleted the blog at
%s (name %s)
""" % (blog.userid, blog.feedurl, blog.name), 'webmaster@postgresql.org', [settings.NOTIFYADDR])
	blog.delete()
	AuditEntry(request.user.username, 'Deleted blog %s' % blog.feedurl).save()
	return HttpResponseRedirect('../..')

@login_required
@transaction.commit_on_success
def modifyauthorfilter(request, id):
	blog = get_object_or_404(Blog, id=id)
	if not request.user.is_superuser:
		if not blog.userid == request.user.username:
			raise Exception("You can only update your own author filter! Don't try to hack!")
	blog.authorfilter = request.POST['authorfilter']
	blog.save()
	AuditEntry(request.user.username, 'Changed author filter of blog %s' % blog.feedurl).save()
	return HttpResponseRedirect('../..')

@user_passes_test(issuperuser)
@transaction.commit_on_success
def modify(request, id):
	blog = get_object_or_404(Blog, id=id)
	blog.name = request.POST['blogname']
	blog.save()
	AuditEntry(request.user.username, 'Changed name of blog %s' % blog.feedurl).save()
	return HttpResponseRedirect('../..')
	
@user_passes_test(issuperuser)
@transaction.commit_on_success
def approve(request, id):
	blog = get_object_or_404(Blog, id=id)
	blog.approved = True
	blog.save()
	AuditEntry(request.user.username, 'Approved blog %s' % blog.feedurl).save()
	return HttpResponseRedirect('../..')

@user_passes_test(issuperuser)
@transaction.commit_on_success
def unapprove(request, id):
	blog = get_object_or_404(Blog, id=id)
	blog.approved = False
	blog.save()
	AuditEntry(request.user.username, 'Unapproved blog %s' % blog.feedurl).save()
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

@user_passes_test(issuperuser)
@transaction.commit_on_success
def undiscover(request, id):
	blog = get_object_or_404(Blog, id=id)
	blog.blogurl = ''
	blog.save()
	AuditEntry(request.user.username, 'Undiscovered blog %s' % blog.feedurl).save()
	return HttpResponseRedirect('../..')

@user_passes_test(issuperuser)
@transaction.commit_on_success
def detach(request, id):
	blog = get_object_or_404(Blog, id=id)
	olduid = blog.userid
	blog.userid = None
	blog.save()
	AuditEntry(request.user.username, 'Detached blog %s from %s' % (blog.feedurl, olduid)).save()
	return HttpResponseRedirect('../..')

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
