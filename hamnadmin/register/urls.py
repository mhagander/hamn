from django.conf.urls.defaults import *
from django.contrib.auth.views import login, logout, logout_then_login

# Uncomment the next two lines to enable the admin:
# from django.contrib import admin
# hamnadmin.autodiscover()

urlpatterns = patterns('',
    (r'^$', 'hamnadmin.register.views.root'),
    (r'^new/$', 'hamnadmin.register.views.new'),
    (r'^approve/(\d+)/$', 'hamnadmin.register.views.approve'),
    (r'^unapprove/(\d+)/$', 'hamnadmin.register.views.unapprove'),
    (r'^discover/(\d+)/$', 'hamnadmin.register.views.discover'),
    (r'^undiscover/(\d+)/$', 'hamnadmin.register.views.undiscover'),
    (r'^detach/(\d+)/$', 'hamnadmin.register.views.detach'),
    (r'^delete/(\d+)/$', 'hamnadmin.register.views.delete'),
    (r'^modify/(\d+)/$', 'hamnadmin.register.views.modify'),
    (r'^modifyauthorfilter/(\d+)/$', 'hamnadmin.register.views.modifyauthorfilter'),

    (r'^log/(\d+)/$','hamnadmin.register.views.logview'),
    (r'^blogposts/(\d+)/$', 'hamnadmin.register.views.blogposts'),
    (r'^blogposts/(\d+)/hide/(\d+)/$', 'hamnadmin.register.views.blogpost_hide'),
    (r'^blogposts/(\d+)/unhide/(\d+)/$', 'hamnadmin.register.views.blogpost_unhide'),
    (r'^blogposts/(\d+)/delete/(\d+)/$', 'hamnadmin.register.views.blogpost_delete'),

    (r'^login/$', login),
    (r'^logout/$', logout_then_login, {'login_url':'/'}),
)
