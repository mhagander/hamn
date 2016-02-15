from django.http import HttpResponse, HttpResponseRedirect
from django.template import RequestContext
from django.shortcuts import render_to_response, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.conf import settings
from django.core.mail import send_mail
from django.db import transaction
from django.db.models import Q, Count, Max
from django.contrib import messages

from hamnadmin.register.models import *
from hamnadmin.mailqueue.util import send_simple_mail
from hamnadmin.util.varnish import purge_url, purge_root_and_feeds

import socket
import datetime
import feedparser

from forms import BlogEditForm, ModerateRejectForm

# Public planet
def planet_home(request):
	statdate = datetime.datetime.now() - datetime.timedelta(days=61)
	posts = Post.objects.filter(hidden=False, feed__approved=True).order_by('-dat')[:30]
	topposters = Blog.objects.filter(approved=True, excludestats=False, posts__hidden=False, posts__dat__gt=statdate).annotate(numposts=Count('posts__id')).order_by('-numposts')[:10]
	topteams = Team.objects.filter(blog__approved=True, blog__excludestats=False, blog__posts__hidden=False, blog__posts__dat__gt=statdate).annotate(numposts=Count('blog__posts__id')).order_by('-numposts')[:10]
	return render_to_response('index.tmpl', {
		'posts': posts,
		'topposters': topposters,
		'topteams': topteams,
	}, context_instance=RequestContext(request))


def planet_feeds(request):
	return render_to_response('feeds.tmpl', {
		'feeds': Blog.objects.filter(approved=True, archived=False),
		'teams': Team.objects.filter(blog__approved=True).distinct().order_by('name'),
	}, context_instance=RequestContext(request))

def planet_add(request):
	return render_to_response('add.tmpl', {
	}, context_instance=RequestContext(request))



# Registration interface (login and all)
def issuperuser(user):
	return user.is_authenticated() and user.is_superuser

@login_required
def root(request):
	if request.user.is_superuser and request.GET.has_key('admin') and request.GET['admin'] == '1':
		blogs = Blog.objects.all().order_by('archived', 'approved', 'name')
	else:
		blogs = Blog.objects.filter(user=request.user).order_by('archived', 'approved', 'name')
	return render_to_response('index.html',{
		'blogs': blogs,
		'teams': Team.objects.filter(manager=request.user).order_by('name'),
		'title': 'Your blogs',
	}, context_instance=RequestContext(request))

@login_required
@transaction.atomic
def edit(request, id=None):
	if id:
		if request.user.is_superuser:
			blog = get_object_or_404(Blog, id=id)
		else:
			blog = get_object_or_404(Blog, id=id, user=request.user)
	else:
		blog = Blog(user=request.user, name = u"{0} {1}".format(request.user.first_name, request.user.last_name))

	if request.method == 'POST':
		saved_url = blog.feedurl
		saved_filter = blog.authorfilter
		saved_team = blog.team
		form = BlogEditForm(request, data=request.POST, instance=blog)
		if form.is_valid():
			if id:
				# This is an existing one. If we change the URL of the blog, it needs to be
				# de-moderated if it was previously approved.
				if blog.approved:
					if saved_url != form.cleaned_data['feedurl'] or saved_filter != form.cleaned_data['authorfilter']:
						obj = form.save()
						obj.approved = False
						obj.save()

						send_simple_mail(settings.EMAIL_SENDER,
										 settings.NOTIFICATION_RECEIVER,
										 "A blog was edited on Planet PostgreSQL",
										 u"The blog at {0}\nwas edited by {1} in a way that needs new moderation.\n\nTo moderate: https://planet.postgresql.org/register/moderate/\n\n".format(blog.feedurl, blog.user),
										 sendername="Planet PostgreSQL",
										 receivername="Planet PostgreSQL Moderators",
									 )

						messages.warning(request, "Blog has been resubmitted for moderation, and is temporarily disabled.")

						purge_root_and_feeds()
						purge_url('/feeds.html')

						return HttpResponseRedirect("/register/edit/{0}/".format(obj.id))

			obj = form.save()

			if obj.team and obj.team != saved_team:
				# We allow anybody to join a team by default, and will just send a notice
				# so the team manager can undo it.
				send_simple_mail(settings.EMAIL_SENDER,
								 obj.team.manager.email,
								 "A blog joined your team on Planet PostgreSQL",
								 u"The blog at {0} by {1} {2}\nhas been added to yor team {3} on Planet PostgreSQL\n\nIf this is correct, you do not need to do anything.\n\nIf this is incorrect, please go to\n\nhttps://planet.postgresql.org/register/\n\nand click the button to remove the blog from your team.\nWe apologize if this causes work for you.\n\n".format(
									 obj.feedurl,
									 obj.user.first_name, obj.user.last_name,
									 obj.team.name),
								 sendername="Planet PostgreSQL",
								 receivername=u"{0} {1}".format(obj.team.manager.first_name, obj.team.manager.last_name),
								 )

			return HttpResponseRedirect("/register/edit/{0}/".format(obj.id))
	else:
		form =  BlogEditForm(request, instance=blog)

	return render_to_response('edit.html', {
		'new': id is None,
		'form': form,
		'blog': blog,
		'log': AggregatorLog.objects.filter(feed=blog).order_by('-ts')[:30],
		'posts': Post.objects.filter(feed=blog).order_by('-dat')[:10],
		'title': 'Edit blog: %s' % blog.name,
	}, RequestContext(request))

@login_required
@transaction.atomic
def delete(request, id):
	if request.user.is_superuser:
		blog = get_object_or_404(Blog, id=id)
	else:
		blog = get_object_or_404(Blog, id=id, user=request.user)

	send_simple_mail(settings.EMAIL_SENDER,
					 settings.NOTIFICATION_RECEIVER,
					 "A blog was deleted on Planet PostgreSQL",
					 u"The blog at {0} by {1}\nwas deleted by {2}\n\n".format(blog.feedurl, blog.name, request.user.username),
					 sendername="Planet PostgreSQL",
					 receivername="Planet PostgreSQL Moderators",
	)
	blog.delete()
	messages.info(request, "Blog deleted.")
	purge_root_and_feeds()
	purge_url('/feeds.html')
	return HttpResponseRedirect("/register/")

@login_required
@transaction.atomic
def archive(request, id):
	if request.user.is_superuser:
		blog = get_object_or_404(Blog, id=id)
	else:
		blog = get_object_or_404(Blog, id=id, user=request.user)

	send_simple_mail(settings.EMAIL_SENDER,
					 settings.NOTIFICATION_RECEIVER,
					 "A blog was archived on Planet PostgreSQL",
					 u"The blog at {0} by {1}\nwas archived by {2}\n\n".format(blog.feedurl, blog.name, request.user.username),
					 sendername="Planet PostgreSQL",
					 receivername="Planet PostgreSQL Moderators",
	)
	blog.archived = True
	blog.save()
	messages.info(request, "Blog archived.")
	return HttpResponseRedirect("/register/")

@login_required
@transaction.atomic
def remove_from_team(request, teamid, blogid):
	team = get_object_or_404(Team, id=teamid, manager=request.user)
	blog = get_object_or_404(Blog, id=blogid)

	if blog.team != team:
		messages.error(request, "The blog at {0} does not (any more?) belong to the team {1}!".format(
			blog.feedurl,
			team.name))
		return HttpResponseRedirect("/register/")

	blog.team = None
	blog.save()

	send_simple_mail(settings.EMAIL_SENDER,
					 settings.NOTIFICATION_RECEIVER,
					 "A blog was removed from a team on Planet PostgreSQL",
					 u"The blog at {0} by {1} {2}\nwas removed from team {3} by {4}.\n".format(
						 blog.feedurl, blog.user.first_name, blog.user.last_name, team.name, request.user.username),
					 sendername="Planet PostgreSQL",
					 receivername="Planet PostgreSQL Moderators",
					 )

	send_simple_mail(settings.EMAIL_SENDER,
					 blog.user.email,
					 "Your blog on Planet PostgreSQL was removed from the team",
					 u"Your blog at {0} has been removed\nfrom the team {1} on Planet PostgreSQL.\n\nIf you believe this to be in error, please contact\nthe team administrator.\n\n".format(blog.feedurl, team.name),
					 sendername="Planet PostgreSQL",
					 receivername=u"{0} {1}".format(blog.user.first_name, blog.user.last_name),
					 )

	messages.info(request, "Blog {0} removed from team {1}".format(blog.feedurl, team.name))
	return HttpResponseRedirect("/register/")

def __getvalidblogpost(request, blogid, postid):
	blog = get_object_or_404(Blog, id=blogid)
	post = get_object_or_404(Post, id=postid)
	if not blog.user == request.user and not request.user.is_superuser:
		raise Exception("You can't view/edit somebody elses blog!")
	if not post.feed.id == blog.id:
		raise Exception("Blog does not match post")
	return post

def __setposthide(request, blogid, postid, status):
	post = __getvalidblogpost(request, blogid, postid)
	post.hidden = status
	post.save()
	AuditEntry(request.user.username, 'Set post %s on blog %s visibility to %s' % (postid, blogid, status)).save()
	messages.info(request, 'Set post "%s" to %s' % (post.title, status and "hidden" or "visible"), extra_tags="top")
	purge_root_and_feeds()
	return HttpResponseRedirect("/register/edit/{0}/".format(blogid))

@login_required
@transaction.atomic
def blogpost_hide(request, blogid, postid):
	return __setposthide(request, blogid, postid, True)

@login_required
@transaction.atomic
def blogpost_unhide(request, blogid, postid):
	return __setposthide(request, blogid, postid, False)

@login_required
@transaction.atomic
def blogpost_delete(request, blogid, postid):
	post = __getvalidblogpost(request, blogid, postid)
	title = post.title

	# Update the feed last fetched date to be just before this entry, so that we end up
	# re-fetching it if necessary.
	post.feed.lastget = post.dat - timedelta(minutes=1)
	post.feed.save()

	# Now actually delete it
	post.delete()
	AuditEntry(request.user.username, 'Deleted post %s from blog %s' % (postid, blogid)).save()
	messages.info(request, 'Deleted post "%s". It will be reloaded on the next scheduled crawl.' % title)
	purge_root_and_feeds()
	return HttpResponseRedirect("/register/edit/{0}/".format(blogid))

# Moderation
@login_required
@user_passes_test(issuperuser)
def moderate(request):
	return render_to_response('moderate.html',{
		'blogs': Blog.objects.filter(approved=False).annotate(oldest=Max('posts__dat')).order_by('oldest'),
		'title': 'Moderation',
	}, context_instance=RequestContext(request))

@login_required
@user_passes_test(issuperuser)
@transaction.atomic
def moderate_reject(request, blogid):
	blog = get_object_or_404(Blog, id=blogid)

	if request.method == "POST":
		form = ModerateRejectForm(data=request.POST)
		if form.is_valid():
			# Ok, actually reject this blog.
			# Always send moderator mail
			send_simple_mail(settings.EMAIL_SENDER,
							 settings.NOTIFICATION_RECEIVER,
							 "A blog was rejected on Planet PostgreSQL",
							 u"The blog at {0} by {1} {2}\nwas marked as rejected by {3}. The message given was:\n\n{4}\n\n".format(blog.feedurl, blog.user.first_name, blog.user.last_name, request.user.username, form.cleaned_data['message']),
							 sendername="Planet PostgreSQL",
							 receivername="Planet PostgreSQL Moderators",
							 )
			messages.info(request, u"Blog {0} rejected, notification sent to moderators".format(blog.feedurl))
			if not form.cleaned_data['modsonly']:
				send_simple_mail(settings.EMAIL_SENDER,
								 blog.user.email,
								 "Your blog submission to Planet PostgreSQL",
								 u"The blog at {0} that you submitted to Planet PostgreSQL has\nunfortunately been rejected. The reason given was:\n\n{1}\n\n".format(blog.feedurl, form.cleaned_data['message']),
								 sendername="Planet PostgreSQL",
								 receivername = u"{0} {1}".format(blog.user.first_name, blog.user.last_name),
								 )
				messages.info(request, u"Blog {0} rejected, notification sent to blog owner".format(blog.feedurl))

			blog.delete()
			return HttpResponseRedirect("/register/moderate/")
	else:
		form = ModerateRejectForm()

	return render_to_response('moderate_reject.html', {
		'form': form,
		'blog': blog,
		'title': 'Reject blog',
	}, RequestContext(request))

@login_required
@user_passes_test(issuperuser)
@transaction.atomic
def moderate_approve(request, blogid):
	blog = get_object_or_404(Blog, id=blogid)

	send_simple_mail(settings.EMAIL_SENDER,
					 settings.NOTIFICATION_RECEIVER,
					 "A blog was approved on Planet PostgreSQL",
					 u"The blog at {0} by {1} {2}\nwas marked as approved by {3}.\n\n".format(blog.feedurl, blog.user.first_name, blog.user.last_name, request.user.username),
					 sendername="Planet PostgreSQL",
					 receivername="Planet PostgreSQL Moderators",
	)

	send_simple_mail(settings.EMAIL_SENDER,
					 blog.user.email,
					 "Your blog submission to Planet PostgreSQL",
					 u"The blog at {0} that you submitted to Planet PostgreSQL has\nbeen approved.\n\n".format(blog.feedurl),
					 sendername="Planet PostgreSQL",
					 receivername = u"{0} {1}".format(blog.user.first_name, blog.user.last_name),
	)

	blog.approved = True
	blog.save()

	AuditEntry(request.user.username, 'Approved blog %s at %s' % (blog.id, blog.feedurl)).save()

	messages.info(request, u"Blog {0} approved, notification sent to moderators and owner.".format(blog.feedurl))

	purge_root_and_feeds()
	purge_url('/feeds.html')

	return HttpResponseRedirect("/register/moderate/")
