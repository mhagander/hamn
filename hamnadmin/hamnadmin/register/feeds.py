from django.contrib.syndication.views import Feed

from hamnadmin.util.html import TruncateAndClean

from .models import Post


class PostFeed(Feed):
    title = 'Planet PostgreSQL'
    link = 'https://planet.postgresql.org'
    description = 'Planet PostgreSQL'
    generator = 'Planet PostgreSQL'

    def feed_url(self, type=None):
        if type == "_short":
            return 'https://planet.postgresql.org/rss20_short.xml'
        return 'https://planet.postgresql.org/rss20.xml'

    def get_object(self, request, type=None):
        return type

    def items(self, type):
        qs = Post.objects.filter(feed__approved=True, hidden=False).order_by('-dat')
        if type == "_short":
            qs = qs.extra(select={'short': 1})
        return qs[:30]

    def item_title(self, item):
        return "{0}: {1}".format(item.feed.name, item.title)

    def item_link(self, item):
        if not item.shortlink:
            # If not cached, calculate one
            return item._get_shortlink()
        return item.shortlink

    def item_pubdate(self, item):
        return item.dat

    def item_description(self, item):
        if hasattr(item, 'short'):
            try:
                return TruncateAndClean(item.txt)
            except Exception:
                return "Unable to clean HTML"
        else:
            return item.txt

    def __call__(self, request, *args, **kwargs):
        r = super().__call__(request, *args, **kwargs)
        r['xkey'] = 'index'
        return r
