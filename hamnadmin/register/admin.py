from django.contrib import admin
from hamnadmin.register.models import *

class BlogAdmin(admin.ModelAdmin):
	list_display = ['approved', 'userid', 'name', 'feedurl', 'authorfilter', ]
	ordering = ['approved', 'name', ] #meh, multiple ordering not supported

admin.site.register(Team)
admin.site.register(Blog, BlogAdmin)
admin.site.register(Post)
