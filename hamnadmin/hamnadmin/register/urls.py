from django.conf.urls import *

# Uncomment the next two lines to enable the admin:
from django.contrib import admin
admin.autodiscover()

urlpatterns = patterns('',
    (r'^$', 'hamnadmin.register.views.root'),
    (r'^new/$', 'hamnadmin.register.views.edit'),
    (r'^edit/(?P<id>\d+)/$', 'hamnadmin.register.views.edit'),
    (r'^delete/(?P<id>\d+)/$', 'hamnadmin.register.views.delete'),

    (r'^blogposts/(\d+)/hide/(\d+)/$', 'hamnadmin.register.views.blogpost_hide'),
    (r'^blogposts/(\d+)/unhide/(\d+)/$', 'hamnadmin.register.views.blogpost_unhide'),
    (r'^blogposts/(\d+)/delete/(\d+)/$', 'hamnadmin.register.views.blogpost_delete'),

    (r'^moderate/$', 'hamnadmin.register.views.moderate'),
    (r'^moderate/reject/(\d+)/$', 'hamnadmin.register.views.moderate_reject'),
    (r'^moderate/approve/(\d+)/$', 'hamnadmin.register.views.moderate_approve'),
    (r'^login/$', 'hamnadmin.auth.login'),
    (r'^auth_receive/$', 'hamnadmin.auth.auth_receive'),
    (r'^logout/$', 'hamnadmin.auth.logout'),

    (r'^admin/', include(admin.site.urls)),
)
