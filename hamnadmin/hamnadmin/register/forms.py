from django import forms
from django.contrib import messages
from django.conf import settings

from .models import Blog

from hamnadmin.util.aggregate import FeedFetcher, ParserGotRedirect

import requests
import requests_oauthlib


class BlogEditForm(forms.ModelForm):
    class Meta:
        model = Blog
        fields = ('feedurl', 'team', 'authorfilter')

    def __init__(self, request, *args, **kwargs):
        self.request = request
        super(BlogEditForm, self).__init__(*args, **kwargs)
        for f in self.fields.values():
            f.widget.attrs['class'] = 'form-control'

        if kwargs['instance'].approved:
            self.fields['feedurl'].help_text = "Note that changing the feed URL will disable the blog pending new moderation"
            self.fields['authorfilter'].help_text = "Note that changing the author filter will disable the blog pending new moderation"

    def clean(self):
        tracemessages = []

        def _trace(msg):
            tracemessages.append(msg)

        if 'feedurl' not in self.cleaned_data:
            # No feedurl present means error already thrown
            return self.cleaned_data

        # Create a fake instance to pass down. We'll just throw it away
        feedobj = Blog(feedurl=self.cleaned_data.get('feedurl', None), authorfilter=self.cleaned_data['authorfilter'])
        fetcher = FeedFetcher(feedobj, _trace, False)
        try:
            entries = list(fetcher.parse())
        except ParserGotRedirect:
            raise forms.ValidationError("This URL returns a permanent redirect")
        except Exception as e:
            raise forms.ValidationError("Failed to retrieve and parse feed: %s" % e)
        if len(entries) == 0:
            for m in tracemessages:
                messages.info(self.request, m)
            raise forms.ValidationError("No entries found in blog. You cannot submit a blog until it contains entries.")

        return self.cleaned_data


class ModerateRejectForm(forms.Form):
    message = forms.CharField(min_length=30, required=True, widget=forms.Textarea, help_text="Enter a reason for the blog rejection.")
    modsonly = forms.BooleanField(required=False, label="Moderators only?", help_text="Should message be sent only to moderators, and not to the submitter (for spam submissions mainly)?")

    def __init__(self, *args, **kwargs):
        super(ModerateRejectForm, self).__init__(*args, **kwargs)
        for f in self.fields.values():
            if isinstance(f.widget, forms.widgets.CheckboxInput):
                f.widget.attrs['class'] = 'form-check-input'
            else:
                f.widget.attrs['class'] = 'form-control'
