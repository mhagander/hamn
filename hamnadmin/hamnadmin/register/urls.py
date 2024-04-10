from django.urls import re_path

import hamnadmin.register.views
import hamnadmin.auth

# Uncomment the next two lines to enable the admin:
from django.contrib import admin
admin.autodiscover()

urlpatterns = [
    re_path(r'^$', hamnadmin.register.views.root),
    re_path(r'^new/$', hamnadmin.register.views.edit),
    re_path(r'^edit/(?P<id>\d+)/$', hamnadmin.register.views.edit),
    re_path(r'^delete/(?P<id>\d+)/$', hamnadmin.register.views.delete),
    re_path(r'^archive/(?P<id>\d+)/$', hamnadmin.register.views.archive),
    re_path(r'^teamremove/(?P<teamid>\d+)/(?P<blogid>\d+)/$', hamnadmin.register.views.remove_from_team),

    re_path(r'^blogposts/(\d+)/hide/(\d+)/$', hamnadmin.register.views.blogpost_hide),
    re_path(r'^blogposts/(\d+)/unhide/(\d+)/$', hamnadmin.register.views.blogpost_unhide),
    re_path(r'^blogposts/(\d+)/delete/(\d+)/$', hamnadmin.register.views.blogpost_delete),

    re_path(r'^moderate/$', hamnadmin.register.views.moderate),
    re_path(r'^moderate/reject/(\d+)/$', hamnadmin.register.views.moderate_reject),
    re_path(r'^moderate/approve/(\d+)/$', hamnadmin.register.views.moderate_approve),
    re_path(r'^login/$', hamnadmin.auth.login),
    re_path(r'^auth_receive/$', hamnadmin.auth.auth_receive),
    re_path(r'^auth_api/$', hamnadmin.auth.auth_api),
    re_path(r'^logout/$', hamnadmin.auth.logout),

    re_path(r'^admin/', admin.site.urls),
]
