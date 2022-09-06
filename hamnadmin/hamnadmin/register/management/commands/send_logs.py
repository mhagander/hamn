from django.core.management.base import BaseCommand
from django.db import transaction
from django.db.models import Count, Max
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
                num=Count("aggregatorlog__id"),
                last=Max("aggregatorlog__ts"),
            ).filter(num__gt=THRESHOLD).order_by():
                if feed.lastsuccess and feed.lastsuccess > feed.last:
                    success_str = "\nNote that there has been a successful fetch at\n{}, which is more recent than any errors.\n".format(feed.lastsuccess)
                else:
                    success_str = ""

                # We assume this is only run once a day, so just generate one email
                send_simple_mail(
                    settings.EMAIL_SENDER,
                    feed.user.email,
                    "Errors retrieving your feed for Planet PostgreSQL",
                    """Your blog aggregated to Planet PostgreSQL with feed URL

{0}

has failed {1} times in the past 24 hours. To view the details of
the failures, please go to

https://planet.postgresql.org/register/edit/{2}/

using your normal PostgreSQL community login. From this page you
will be able to see what the errors were, so that you can correct
them.
{3}
If this is a blog that is no longer active, please go to the same
page linked above, and click the button to Archive the blog. That
will prevent Planet PostgreSQL from trying to fetch new entries,
and also stop these messages from being sent.

A message like this will be sent once a day as long as your blog
is generating more than {4} errors per day.

""".
                    format(
                        feed.feedurl,
                        feed.num,
                        feed.id,
                        success_str,
                        THRESHOLD),
                    sendername="Planet PostgreSQL",
                    receivername="{0} {1}".format(feed.user.first_name, feed.user.last_name),
                )
