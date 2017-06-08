from django.conf import settings
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

if settings.DEBUG:
    # noinspection PyBroadException
    try:
        import debug_toolbar
        urlpatterns = [
            url(r'^__debug__/', include(debug_toolbar.urls)),
        ] + urlpatterns
    except:
        pass
