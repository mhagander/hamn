from django.urls import re_path, include

import hamnadmin.register.views
from hamnadmin.register.feeds import PostFeed

urlpatterns = [
    re_path(r'^$', hamnadmin.register.views.planet_home),
    re_path(r'^add.html$', hamnadmin.register.views.planet_add),
    re_path(r'^feeds.html$', hamnadmin.register.views.planet_feeds),

    re_path(r'^rss20(?P<type>_short)?\.xml$', PostFeed()),
    re_path(r'^register/', include('hamnadmin.register.urls')),
]
