from django import forms
from django.contrib import messages
from django.core.validators import MinLengthValidator

from models import Blog

from hamnadmin.util.aggregate import FeedFetcher

class BlogEditForm(forms.ModelForm):
	class Meta:
		model = Blog
		fields = ('feedurl', 'team', 'twitteruser', 'authorfilter')

	def __init__(self, request, *args, **kwargs):
		self.request = request
		super(BlogEditForm, self).__init__(*args, **kwargs)
		for f in self.fields.values():
			f.widget.attrs['class'] = 'form-control'

		if kwargs['instance'].approved:
			self.fields['feedurl'].help_text="Note that changing the feed URL will disable the blog pending new moderation"
			self.fields['authorfilter'].help_text="Note that changing the author filter will disable the blog pending new moderation"


	def clean(self):
		tracemessages = []
		def _trace(msg):
			tracemessages.append(msg)

		# Create a fake instance to pass down. We'll just throw it away
		feedobj = Blog(feedurl=self.cleaned_data['feedurl'], authorfilter=self.cleaned_data['authorfilter'])
		fetcher = FeedFetcher(feedobj, _trace)
		try:
			entries = list(fetcher.parse())
		except Exception, e:
			raise forms.ValidationError("Failed to retreive and parse feed: %s" % e)
		if len(entries) == 0:
			for m in tracemessages:
				messages.info(self.request, m)
			raise forms.ValidationError("No entries found in blog. You cannot submit a blog until it contains entries.")

		return self.cleaned_data

	def clean_twitteruser(self):
		if self.cleaned_data['twitteruser'].startswith('@'):
			return self.cleaned_data['twitteruser'][1:]
		else:
			return self.cleaned_data['twitteruser']

class ModerateRejectForm(forms.Form):
	message = forms.CharField(min_length=30, required=True, widget=forms.Textarea)
	modsonly = forms.BooleanField(required=False, label="Moderators only", help_text="Should message be sent only to moderators, and not to the submitter (for spam submissions mainly)")

	def __init__(self, *args, **kwargs):
		super(ModerateRejectForm, self).__init__(*args, **kwargs)
		for f in self.fields.values():
			f.widget.attrs['class'] = 'form-control'
