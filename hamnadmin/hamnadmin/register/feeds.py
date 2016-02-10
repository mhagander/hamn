from django.contrib.syndication.views import Feed

from hamnadmin.util.html import TruncateAndClean

from models import Post

class PostFeed(Feed):
	title = 'Planet PostgreSQL'
	link = 'http://planet.postgresql.org'
	feed_url = 'http://planet.postgresql.org/rss20.xml'
	description = 'Planet PostgreSQL'
	generator = 'Planet PostgreSQL'

	def get_object(self, request, type=None):
		return type

	def items(self, type):
		qs = Post.objects.filter(feed__approved=True, hidden=False).order_by('-dat')
		if type == "_short":
			qs = qs.extra(select = {'short': 1})
		return qs[:30]

	def item_title(self, item):
		return item.title

	def item_link(self, item):
		if not item.shortlink:
			# If not cached, calculate one
			return item._get_shortlink()
		return item.shortlink

	def item_pubdate(self, item):
		return item.dat

	def item_description(self, item):
		if hasattr(item, 'short'):
			return TruncateAndClean(item.txt)
		else:
			return item.txt
