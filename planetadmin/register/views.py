from django.http import HttpResponse, HttpResponseRedirect
from django.template import RequestContext
from django.shortcuts import render_to_response, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.conf import settings
from django.core.mail import send_mail

from planetadmin.register.models import *

import socket
import feedparser

def issuperuser(user):
	return user.is_authenticated() and user.is_superuser

class pExcept(Exception):
	pass

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
def new(request):
	if not request.method== 'POST':
		raise Exception('must be POST')
	feedurl = request.POST['feedurl']
	if not len(feedurl) > 1:
		raise Exception('must include blog url!')

	# See if we can find the blog already
	try:
		blog = Blog.objects.get(feedurl=feedurl)
	except:
		blog = None

	if blog:
		if blog.userid:
			return HttpResponse("Specified blog is already registered to account '%s'" % (blog.userid))
		# Found a match, so we're going to register this blog
		# For safety reasons, we're going to require approval before we do it as well :-P
		if not settings.NOTIFYADDR:
			raise Exception('Notify address not specified, cannot complete')
		blog.userid = request.user.username
		blog.approved = False
		send_mail('New blog assignment', """
The user '%s' has requested the attachment of the blog at
%s
to his/her account. 

So, head off to the admin interface and approve or reject this!
""" % (blog.userid, blog.feedurl), 'webmaster@postgresql.org', [settings.NOTIFYADDR])
		blog.save()
		return HttpResponse('The blog has been attached to your account. For security reasons, it has been disapproved until a moderator has approved this connection.')

	if not feedurl.startswith('http://'):
		return HttpResponse('Only http served blogs are accepted!')

	# Attempting to register a new blog. First let's see that we can download it
	socket.setdefaulttimeout(20)
	try:
		feed = feedparser.parse(feedurl)
		status = feed.status
		lnk = feed.feed.link
		l = len(feed.entries)
		if l < 1:
			return HttpResponse('Blog feed contains no entries.')
	except Exception, e:
		print e
		return HttpResponse('Failed to download blog feed')
	if not status == 200:
		return HttpResponse('Attempt to download blog feed returned status %s.' % (status))
	
	if not settings.NOTIFYADDR:
		raise Exception('Notify address not specified, cannot complete')

	blog = Blog()
	blog.name = request.user.first_name
	if request.user.is_superuser:
		blog.userid = request.POST['userid']
	else:
		blog.userid= request.user.username
	blog.feedurl = feedurl
	blog.blogurl = lnk
	blog.approved = False
	send_mail('New blog assignment', """
The user '%s' has requested the blog at
%s
is added to Planet PostgreSQL!

So, head off to the admin interface and approve or reject this!
""" % (blog.userid, blog.feedurl), 'webmaster@postgresql.org', [settings.NOTIFYADDR])

	blog.save()
	return HttpResponseRedirect('..')

@login_required
def delete(request, id):
	blog = get_object_or_404(Blog, id=id)
	if not request.user.is_superuser:
		if not blog.userid == request.user.username:
			return HttpResponse("You can only delete your own feeds! Don't try to hack!")
	blog.delete()
	return HttpResponseRedirect('../..')

@user_passes_test(issuperuser)
def modify(request, id):
	blog = get_object_or_404(Blog, id=id)
	blog.name = request.POST['blogname']
	blog.save()
	return HttpResponseRedirect('../..')
	
@user_passes_test(issuperuser)
def approve(request, id):
	blog = get_object_or_404(Blog, id=id)
	blog.approved = True
	blog.save()
	return HttpResponseRedirect('../..')

@user_passes_test(issuperuser)
def unapprove(request, id):
	blog = get_object_or_404(Blog, id=id)
	blog.approved = False
	blog.save()
	return HttpResponseRedirect('../..')

@user_passes_test(issuperuser)
def discover(request, id):
	blog = get_object_or_404(Blog, id=id)

	# Attempt to run the discover
	socket.setdefaulttimeout(20)
	try:
		feed = feedparser.parse(blog.feedurl)
		if not blog.blogurl == feed.feed.link:
			blog.blogurl = feed.feed.link
			blog.save()
	except Exception, e:
		return HttpResponse('Failed to discover metadata: %s' % (e))

	return HttpResponseRedirect('../..')

@user_passes_test(issuperuser)
def undiscover(request, id):
	blog = get_object_or_404(Blog, id=id)
	blog.blogurl = ''
	blog.save()
	return HttpResponseRedirect('../..')

@user_passes_test(issuperuser)
def detach(request, id):
	blog = get_object_or_404(Blog, id=id)
	blog.userid = None
	blog.save()
	return HttpResponseRedirect('../..')

@login_required
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
	try:
		post = __getvalidblogpost(request, blogid, postid)
	except pExcept, e:
		return HttpResponse(e)
	post.hidden = status
	post.save()
	return HttpResponseRedirect('../..')

@login_required
def blogpost_hide(request, blogid, postid):
	return __setposthide(request, blogid, postid, True)

@login_required
def blogpost_unhide(request, blogid, postid):
	return __setposthide(request, blogid, postid, False)

@login_required
def blogpost_delete(request, blogid, postid):
	try:
		post = __getvalidblogpost(request, blogid, postid)
	except pExcept, e:
		return HttpResponse(e)

	post.delete()
	return HttpResponseRedirect('../..')
