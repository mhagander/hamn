from django.contrib import admin
from django import forms
from django.core.mail import send_mail
from django.conf import settings

from hamnadmin.register.models import *

class BlogAdminForm(forms.ModelForm):
	class Meta:
		model = Blog
		exclude = []

	def clean_approved(self):
		if self.cleaned_data['approved'] != self.instance.approved:
			# Approved flag has changed, send an email
			if self.cleaned_data.has_key('name'):
				name = self.cleaned_data['name']
			else:
				name = "<empty>"
			send_mail('A planet blog has been %s' % (
				self.cleaned_data['approved'] and 'approved' or 'de-approved',
				),
				"The blog %s (for user %s, userid %s) has been %s." % (
					self.cleaned_data['feedurl'],
					name,
					self.cleaned_data['userid'],
					self.cleaned_data['approved'] and 'approved' or 'de-approved',
				), 'webmaster@postgresql.org', [settings.NOTIFYADDR])
		return self.cleaned_data['approved']

class BlogAdmin(admin.ModelAdmin):
	list_display = ['userid', 'approved', 'name', 'feedurl', 'authorfilter', ]
	ordering = ['approved', 'name', ] #meh, multiple ordering not supported
	form = BlogAdminForm

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
