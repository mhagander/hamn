from django.conf.urls.defaults import *
from django.contrib.auth.views import login, logout, logout_then_login

# Uncomment the next two lines to enable the admin:
# from django.contrib import admin
# admin.autodiscover()

urlpatterns = patterns('',
    (r'^$', 'planetadmin.register.views.root'),
    (r'^new/$', 'planetadmin.register.views.new'),
    (r'^approve/(\d+)/$', 'planetadmin.register.views.approve'),
    (r'^unapprove/(\d+)/$', 'planetadmin.register.views.unapprove'),
    (r'^discover/(\d+)/$', 'planetadmin.register.views.discover'),
    (r'^undiscover/(\d+)/$', 'planetadmin.register.views.undiscover'),
    (r'^detach/(\d+)/$', 'planetadmin.register.views.detach'),
    (r'^delete/(\d+)/$', 'planetadmin.register.views.delete'),
    (r'^modify/(\d+)/$', 'planetadmin.register.views.modify'),

    (r'^blogposts/(\d+)/$', 'planetadmin.register.views.blogposts'),
    (r'^blogposts/(\d+)/hide/(\d+)/$', 'planetadmin.register.views.blogpost_hide'),
    (r'^blogposts/(\d+)/unhide/(\d+)/$', 'planetadmin.register.views.blogpost_unhide'),
    (r'^blogposts/(\d+)/delete/(\d+)/$', 'planetadmin.register.views.blogpost_delete'),

    (r'^login/$', login),
    (r'^logout/$', logout_then_login, {'login_url':'/'}),
)
