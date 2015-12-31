from django.conf.urls import *

# Uncomment the next two lines to enable the admin:
from django.contrib import admin
admin.autodiscover()

urlpatterns = patterns('',
    (r'^$', 'hamnadmin.register.views.root'),
    (r'^new/$', 'hamnadmin.register.views.new'),
    (r'^discover/(\d+)/$', 'hamnadmin.register.views.discover'),
    (r'^delete/(\d+)/$', 'hamnadmin.register.views.delete'),
    (r'^reset/(\d+)/$', 'hamnadmin.register.views.reset'),

    (r'^log/(\d+)/$','hamnadmin.register.views.logview'),
    (r'^blogposts/(\d+)/$', 'hamnadmin.register.views.blogposts'),
    (r'^blogposts/(\d+)/hide/(\d+)/$', 'hamnadmin.register.views.blogpost_hide'),
    (r'^blogposts/(\d+)/unhide/(\d+)/$', 'hamnadmin.register.views.blogpost_unhide'),
    (r'^blogposts/(\d+)/delete/(\d+)/$', 'hamnadmin.register.views.blogpost_delete'),

    (r'^login/$', 'hamnadmin.auth.login'),
    (r'^auth_receive/$', 'hamnadmin.auth.auth_receive'),
    (r'^logout/$', 'hamnadmin.auth.logout'),

    (r'^admin/', include(admin.site.urls)),
)
