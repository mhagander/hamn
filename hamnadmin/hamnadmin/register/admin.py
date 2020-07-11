from django.contrib import admin

from hamnadmin.register.models import Blog, Team, Post, AggregatorLog


class TeamAdmin(admin.ModelAdmin):
    list_display = ['name', 'manager', 'teamurl']

class BlogAdmin(admin.ModelAdmin):
    list_display = ['user', 'approved', 'name', 'feedurl', 'authorfilter', ]
    ordering = ['approved', 'name', ] #meh, multiple ordering not supported
    search_fields = ['user__username', 'name', 'feedurl']

    def change_view(self, request, object_id, extra_context=None):
        blog = Blog(pk=object_id)
        my_context = {
            'posts': blog.posts.all()[:10],
        }
        return super(BlogAdmin, self).change_view(request, object_id, extra_context=my_context)

class PostAdmin(admin.ModelAdmin):
    list_display = ['dat', 'title', 'hidden', 'feed']
    search_fields = ['title', 'feed__name', 'feed__feedurl']

class AggregatorLogAdmin(admin.ModelAdmin):
    list_display = ['ts', 'success', 'feed', 'info']

admin.site.register(Team, TeamAdmin)
admin.site.register(Blog, BlogAdmin)
admin.site.register(Post, PostAdmin)
admin.site.register(AggregatorLog, AggregatorLogAdmin)
