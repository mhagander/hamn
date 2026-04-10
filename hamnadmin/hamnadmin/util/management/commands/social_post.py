#!/usr/bin/env python3
#
# Script to post previously unposted posts to social media providers
#
#

from django.core.management.base import BaseCommand, CommandError
from django.db import connection
from django.conf import settings

from datetime import datetime, timedelta
import time

from hamnadmin.register.models import Post
from hamnadmin.util.socialposter import get_all_providers


allproviders, allprovidernames = get_all_providers(settings)

# Simple map used to shorten id values to URLs
_urlvalmap = ['0', '1', '2', '3', '4', '5', '6', '7', '8', '9', 'a', 'b', 'c', 'd', 'e', 'f', 'g', 'h', 'i', 'j', 'k', 'l', 'm', 'n', 'o', 'p', 'q', 'r', 's', 't', 'u', 'v', 'w', 'x', 'y', 'z', 'A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J', 'K', 'L', 'M', 'N', 'O', 'P', 'Q', 'R', 'S', 'T', 'U', 'V', 'W', 'X', 'Y', 'Z', '-', '_']


class Command(BaseCommand):
    help = 'Post to social media'

    def handle(self, *args, **options):
        curs = connection.cursor()
        curs.execute("SELECT pg_try_advisory_lock(81587342)")
        if not curs.fetchall()[0][0]:
            raise CommandError("Failed to get advisory lock, existing social_post process stuck?")

        posts = Post.objects.select_related('feed').only('id', 'title', 'link', 'shortlink', 'feed__name').filter(feed__approved=True, dat__gt=datetime.now() - timedelta(days=7)).exclude(postedto__has_keys=allprovidernames).order_by('dat')

        for post in posts:
            if not post.shortlink:
                # No short-link exists, so create one. We need the short-link
                # to post, and we store it separately in the database
                # in case it's needed.
                try:
                    post.shortlink = self.shortid(p.id)
                except Exception as e:
                    print("Failed to shorten URL %s: %s" % (post.link, e))
                    continue

                post.save(update_fields=['shortlink'])

            # Set up the string to post.
            while True:
                msg = "{}: {}\n\n{}\n\n#postgresql".format(post.feed.name, post.title, post.shortlink)
                # 299 is bluesky limit, and we'll just apply that to everything, and add 5 as a bonus
                if len(msg) < 295:
                    break
                post.title = post.title[:-(len(msg) - 295) - 1]

            msg = "%s: %s %s" % (
                post.feed.name,
                self.trimpost(post.txt, len(post.title) + len(post.feed.name) + len(post.shortlink) + 3),
                post.shortlink,
            )

            # Post to all socials
            for provider in allproviders:
                if provider.name not in post.postedto:
                    postid = provider.post(msg)
                    if postid is not None:
                        post.postedto[provider.name] = postid
                        post.save(update_fields=['postedto'])

    # Trim an URL using https://postgr.es
    def shortid(self, id):
        s = ""
        while id > 0:
            s = _urlvalmap[id % 64] + s
            id /= 64
        return "https://postgr.es/p/%s" % s
