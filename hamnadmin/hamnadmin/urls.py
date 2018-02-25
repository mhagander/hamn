from django.conf.urls import url, include

import hamnadmin.register.views
from hamnadmin.register.feeds import PostFeed

urlpatterns = [
    url(r'^$', hamnadmin.register.views.planet_home),
    url(r'^add.html$', hamnadmin.register.views.planet_add),
    url(r'^feeds.html$', hamnadmin.register.views.planet_feeds),

    url(r'^rss20(?P<type>_short)?\.xml$', PostFeed()),
    url(r'^register/', include('hamnadmin.register.urls')),
]
