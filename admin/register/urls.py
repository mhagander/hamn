from django.conf.urls.defaults import *
from django.contrib.auth.views import login, logout, logout_then_login

# Uncomment the next two lines to enable the admin:
# from django.contrib import admin
# admin.autodiscover()

urlpatterns = patterns('',
    (r'^$', 'admin.register.views.root'),
    (r'^new/$', 'admin.register.views.new'),
    (r'^approve/(\d+)/$', 'admin.register.views.approve'),
    (r'^unapprove/(\d+)/$', 'admin.register.views.unapprove'),
    (r'^discover/(\d+)/$', 'admin.register.views.discover'),
    (r'^undiscover/(\d+)/$', 'admin.register.views.undiscover'),
    (r'^detach/(\d+)/$', 'admin.register.views.detach'),
    (r'^delete/(\d+)/$', 'admin.register.views.delete'),
    (r'^modify/(\d+)/$', 'admin.register.views.modify'),
    (r'^modifyauthorfilter/(\d+)/$', 'admin.register.views.modifyauthorfilter'),

    (r'^log/(\d+)/$','admin.register.views.logview'),
    (r'^blogposts/(\d+)/$', 'admin.register.views.blogposts'),
    (r'^blogposts/(\d+)/hide/(\d+)/$', 'admin.register.views.blogpost_hide'),
    (r'^blogposts/(\d+)/unhide/(\d+)/$', 'admin.register.views.blogpost_unhide'),
    (r'^blogposts/(\d+)/delete/(\d+)/$', 'admin.register.views.blogpost_delete'),

    (r'^login/$', login),
    (r'^logout/$', logout_then_login, {'login_url':'/'}),
)
