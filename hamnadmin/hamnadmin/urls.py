from django.conf.urls import *

# Uncomment the next two lines to enable the admin:
# from django.contrib import admin
# admin.autodiscover()
from hamnadmin.register.feeds import PostFeed

urlpatterns = patterns('',
    (r'^$', 'hamnadmin.register.views.planet_home'),
    (r'^add.html$', 'hamnadmin.register.views.planet_add'),
    (r'^feeds.html$', 'hamnadmin.register.views.planet_feeds'),

    (r'^rss20(?P<type>_short)?\.xml$', PostFeed()),
    (r'^register/', include('hamnadmin.register.urls')),
)
