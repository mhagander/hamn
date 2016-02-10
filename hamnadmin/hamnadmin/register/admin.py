from django.contrib import admin
from django import forms
from django.conf import settings

from hamnadmin.register.models import *

class BlogAdmin(admin.ModelAdmin):
	list_display = ['user', 'approved', 'name', 'feedurl', 'authorfilter', ]
	ordering = ['approved', 'name', ] #meh, multiple ordering not supported

	def change_view(self, request, object_id, extra_context=None):
		blog = Blog(pk=object_id)
		my_context = {
			'posts': blog.posts.all()[:10],
		}
		return super(BlogAdmin, self).change_view(request, object_id, extra_context=my_context)

class PostAdmin(admin.ModelAdmin):
	list_display = ['dat', 'title', 'hidden', 'feed']

admin.site.register(Team)
admin.site.register(Blog, BlogAdmin)
admin.site.register(Post, PostAdmin)
admin.site.register(AggregatorLog)
