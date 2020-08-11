from django.conf.urls import url, include

import hamnadmin.register.views
import hamnadmin.auth

# Uncomment the next two lines to enable the admin:
from django.contrib import admin
admin.autodiscover()

urlpatterns = [
    url(r'^$', hamnadmin.register.views.root),
    url(r'^new/$', hamnadmin.register.views.edit),
    url(r'^edit/(?P<id>\d+)/$', hamnadmin.register.views.edit),
    url(r'^delete/(?P<id>\d+)/$', hamnadmin.register.views.delete),
    url(r'^archive/(?P<id>\d+)/$', hamnadmin.register.views.archive),
    url(r'^teamremove/(?P<teamid>\d+)/(?P<blogid>\d+)/$', hamnadmin.register.views.remove_from_team),

    url(r'^blogposts/(\d+)/hide/(\d+)/$', hamnadmin.register.views.blogpost_hide),
    url(r'^blogposts/(\d+)/unhide/(\d+)/$', hamnadmin.register.views.blogpost_unhide),
    url(r'^blogposts/(\d+)/delete/(\d+)/$', hamnadmin.register.views.blogpost_delete),

    url(r'^moderate/$', hamnadmin.register.views.moderate),
    url(r'^moderate/reject/(\d+)/$', hamnadmin.register.views.moderate_reject),
    url(r'^moderate/approve/(\d+)/$', hamnadmin.register.views.moderate_approve),
    url(r'^login/$', hamnadmin.auth.login),
    url(r'^auth_receive/$', hamnadmin.auth.auth_receive),
    url(r'^auth_api/$', hamnadmin.auth.auth_api),
    url(r'^logout/$', hamnadmin.auth.logout),

    url(r'^admin/', admin.site.urls),
]
