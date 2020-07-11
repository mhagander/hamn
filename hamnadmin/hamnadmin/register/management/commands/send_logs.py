from django.core.management.base import BaseCommand
from django.db import transaction
from django.db.models import Count
from django.conf import settings

from datetime import datetime, timedelta

from hamnadmin.mailqueue.util import send_simple_mail
from hamnadmin.register.models import Blog

# Number of errors in the past 24 hours to trigger email
THRESHOLD = 20


class Command(BaseCommand):
    help = "Send planet aggregation logs to blog owners"

    def handle(self, *args, **options):
        with transaction.atomic():
            for feed in Blog.objects.filter(
                    archived=False,
                    aggregatorlog__success=False,
                    aggregatorlog__ts__gt=datetime.now() - timedelta(days=1),
            ).annotate(
                num=Count("aggregatorlog__id")
            ).filter(num__gt=THRESHOLD).order_by():
                # We assume this is only run once a day, so just generate one email
                send_simple_mail(
                    settings.EMAIL_SENDER,
                    feed.user.email,
                    "Errors retreiving your feed for Planet PostgreSQL",
                    """Your blog aggregated to Planet PostgreSQL with feed URL

{0}

has failed {1} times in the past 24 hours. To view the details of
the failures, please go to

https://planet.postgresql.org/register/edit/{2}/

using your normal PostgreSQL community login. From this page you
will be able to see what the errors were, so that you can correct
them.

If this is a blog that is no longer active, please go to the same
page linked above, and click the button to Archive the blog. That
will prevent Planet PostgreSQL from trying to fetch new entries,
and also stop these messages from being sent.

A message like this will be sent once a day as long as your blog
is generating more than {3} errors per day.

""".
                    format(
                        feed.feedurl,
                        feed.num,
                        feed.id,
                        THRESHOLD),
                    sendername="Planet PostgreSQL",
                    receivername="{0} {1}".format(feed.user.first_name, feed.user.last_name),
                )
