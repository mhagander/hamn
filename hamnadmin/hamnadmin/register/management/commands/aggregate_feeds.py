from gevent.threadpool import ThreadPool
import gevent

from django.core.management.base import BaseCommand
from django.db import transaction
from django.db.models import Q, Exists, OuterRef
from django.conf import settings

from datetime import datetime

from hamnadmin.register.models import Blog, Post, AggregatorLog
from hamnadmin.util.aggregate import FeedFetcher, ParserGotRedirect
from hamnadmin.mailqueue.util import send_simple_mail
from hamnadmin.util.varnish import purge_root_and_feeds


class BreakoutException(Exception):
    pass


class Command(BaseCommand):
    help = 'Aggregate one or more feeds'

    def add_arguments(self, parser):
        parser.add_argument('--id', type=int, help="Fetch just one feed specified by id")
        parser.add_argument('-d', '--debug', action='store_true', help="Enable debug mode, don't save anything")
        parser.add_argument('-f', '--full', action='store_true', help="Fetch full feed, regardless of last fetch date")
        parser.add_argument('-p', '--parallelism', type=int, default=10, help="Number of parallell requests")

    def trace(self, msg):
        if self.verbose:
            self.stdout.write(msg)

    def handle(self, *args, **options):
        self.verbose = options['verbosity'] > 1
        self.debug = options['debug']
        if self.debug:
            self.verbose = True
        self.full = options['full']

        if options['id']:
            feeds = Blog.objects.filter(pk=options['id'])
        else:
            # Fetch all feeds - that are not archived. We do fetch feeds that are not approved,
            # to make sure they work.
            feeds = Blog.objects.filter(archived=False)
        feeds = feeds.annotate(
            has_entries=Exists(Post.objects.filter(feed=OuterRef("pk"), hidden=False)),
        )

        # Fan out the fetching itself
        fetchers = [FeedFetcher(f, self.trace) for f in feeds]
        num = len(fetchers)
        pool = ThreadPool(options['parallelism'])
        pr = pool.map_async(self._fetch_one_feed, fetchers)
        while not pr.ready():
            gevent.sleep(1)
            self.trace("Fetching feeds (%s/%s done), please wait..." % (num - pool.task_queue.unfinished_tasks, num))

        total_entries = 0
        # Fetching was async, but results processing will be sync. Don't want to deal with
        # multithreaded database connections and such complications.
        try:
            with transaction.atomic():
                for feed, results in pr.get():
                    if isinstance(results, ParserGotRedirect):
                        # Received a redirect. If this is a redirect for exactly the same URL just
                        # from http to https, special case this and allow it. For any other redirect,
                        # we don't follow it since it might no longer be a properly filtered feed
                        # for example.
                        if results.url == feed.feedurl:
                            # Redirect to itself! Should never happen, of course.
                            AggregatorLog(feed=feed, success=False,
                                          info="Feed returned redirect loop to itself!").save()
                        elif results.url == feed.feedurl.replace('http://', 'https://'):
                            # OK, update it!
                            AggregatorLog(feed=feed, success=True,
                                          info="Feed returned redirect to https, updating registration").save()
                            send_simple_mail(
                                settings.EMAIL_SENDER,
                                feed.user.email,
                                "Your blog at Planet PostgreSQL redirected",
                                "The blog aggregator at Planet PostgreSQL has picked up a redirect for your blog.\nOld URL: {0}\nNew URL: {1}\n\nThe database has been updated, and new entries will be fetched from the secure URL in the future.\n".format(feed.feedurl, results.url),
                                sendername="Planet PostgreSQL",
                                receivername="{0} {1}".format(feed.user.first_name, feed.user.last_name),
                            )
                            send_simple_mail(
                                settings.EMAIL_SENDER,
                                settings.NOTIFICATION_RECEIVER,
                                "Blog redirect detected on Planet PostgreSQL",
                                "The blog at {0} by {1}\nis returning a redirect to a https version of itself.\n\nThe database has automatically been updated, and will start fetching using https in the future,\n\n".format(feed.feedurl, feed.user),
                                sendername="Planet PostgreSQL",
                                receivername="Planet PostgreSQL Moderators",
                            )
                            feed.feedurl = results.url
                            feed.save(update_fields=['feedurl'])
                        else:
                            AggregatorLog(feed=feed, success=False,
                                          info="Feed returned redirect (http 301)").save()
                    elif isinstance(results, Exception):
                        AggregatorLog(feed=feed,
                                      success=False,
                                      info=results).save()
                    else:
                        if feed.approved:
                            had_entries = True
                        else:
                            had_entries = feed.has_entries
                        entries = 0
                        titles = []
                        ids = []

                        # Flag this as a successful get, even if there were no new entries
                        feed.lastsuccess = datetime.now()
                        feed.save(update_fields=['lastsuccess'])

                        # If the blog URL changed, update it as requested
                        # Do this here so that the new blogurl is used for emails below.
                        if getattr(feed, 'new_blogurl', None):
                            self.trace("URL changed for %s from '%s' to '%s'" % (feed.feedurl, feed.blogurl, feed.new_blogurl))
                            send_simple_mail(
                                settings.EMAIL_SENDER,
                                settings.NOTIFICATION_RECEIVER,
                                "A blog url changed on Planet PostgreSQL",
                                "When checking the blog at {0} by {1}\nthe blog URL was updated to:\n{2}\n(from previous value {3})\nNo change in approval status has been made.\n\nTo moderate this or other feeds: https://planet.postgresql.org/register/moderate/\n\n".format(feed.feedurl, feed.user, feed.new_blogurl, feed.blogurl),
                                sendername="Planet PostgreSQL",
                                receivername="Planet PostgreSQL Moderators",
                            )
                            send_simple_mail(
                                settings.EMAIL_SENDER,
                                feed.user.email,
                                "URL of your blog at Planet PostgreSQL updated",
                                "The blog aggregator at Planet PostgreSQL has automatically updated the URL of your blog\nwith the feed at {0} to:\n{1} (from {2})\n\nThis value is retrieved from the feed itself, so if it is not correct,\nthe contents of the feed needs to be corrected.\nIf you have any further questions, please contact planet@postgresql.org\n".format(
                                    feed.feedurl,
                                    feed.new_blogurl,
                                    feed.blogurl,
                                ),
                                sendername="Planet PostgreSQL",
                                receivername="{0} {1}".format(feed.user.first_name, feed.user.last_name),
                            )
                            feed.blogurl = feed.new_blogurl
                            feed.save(update_fields=['blogurl'])

                        for entry in results:
                            self.trace("Found entry at %s" % entry.link)
                            # Entry is a post, but we need to check if it's already there. Check
                            # is done on guid. Some blogs use http and https in the guid, and
                            # also change between them depending on how the blog is fetched,
                            # so check for those two explicitly.
                            if 'http://' in entry.guid:
                                alternateguid = entry.guid.replace('http://', 'https://')
                            elif 'https://' in entry.guid:
                                alternateguid = entry.guid.replace('https://', 'http://')
                            else:
                                alternateguid = None
                            # We check if this entry has been syndicated on any *other* blog as well,
                            # so we don't accidentally post something more than once.
                            if not Post.objects.filter(Q(guid=entry.guid) | Q(guid=alternateguid)).exists():
                                self.trace("Saving entry at %s" % entry.link)
                                entry.save()
                                entry.update_shortlink()
                                AggregatorLog(feed=feed,
                                              success=True,
                                              info="Fetched entry at '%s'" % entry.link).save()
                                entries += 1
                                titles.append(entry.title)
                                ids.append(entry.pk)
                                total_entries += 1
                            else:
                                self.trace("Skipping entry: %s" % entry.link)

                        if entries > 0 and feed.approved:
                            # If we picked "too many" entries, this might indicate a misconfigured blog that
                            # stopped doing it's filtering correctly.
                            if entries > settings.MAX_SAFE_ENTRIES_PER_FETCH:
                                self.trace("{0} new entries for {1}, >{2}, hiding".format(
                                    entries, feed.feedurl, settings.MAX_SAFE_ENTRIES_PER_FETCH))
                                Post.objects.filter(id__in=ids).update(hidden=True)
                                # Email a notification that they were picked up
                                send_simple_mail(
                                    settings.EMAIL_SENDER,
                                    feed.user.email,
                                    "Many posts found at your blog at Planet PostgreSQL",
                                    "The blog aggregator at Planet PostgreSQL has just picked up the following\nposts from your blog at {0}:\n\n{1}\n\nSince this is a large number of posts, they have been fetched\nand marked as hidden, to avoid possible duplicates.\n\nPlease go to https://planet.postgresql.org/register/edit/{2}\nand confirm (by unhiding) which of these should be posted.\n\nThank you!\n\n".format(
                                        feed.blogurl,
                                        "\n".join(["* " + t for t in titles]),
                                        feed.id),
                                    sendername="Planet PostgreSQL",
                                    receivername="{0} {1}".format(feed.user.first_name, feed.user.last_name),
                                )
                                send_simple_mail(
                                    settings.EMAIL_SENDER,
                                    settings.NOTIFICATION_RECEIVER,
                                    "Excessive posts from feed on Planet PostgreSQL",
                                    "The blog at {0} by {1}\nreceived {2} new posts in a single fetch.\nAs this may be incorrect, the posts have been marked as hidden.\nThe author may individually mark them as visible depending on\nprevious posts, and has been sent a notification about this.".format(feed.feedurl, feed.user, len(ids)),
                                    sendername="Planet PostgreSQL",
                                    receivername="Planet PostgreSQL Moderators",
                                )
                            else:
                                # Email a notification that they were picked up
                                send_simple_mail(
                                    settings.EMAIL_SENDER,
                                    feed.user.email,
                                    "Posts found at your blog at Planet PostgreSQL",
                                    "The blog aggregator at Planet PostgreSQL has just picked up the following\nposts from your blog at {0}:\n\n{1}\n\nIf these entries are correct, you don't have to do anything.\nIf any entry should not be there, head over to\n\nhttps://planet.postgresql.org/register/edit/{2}/\n\nand click the 'Hide' button for those entries as soon\nas possible.\n\nThank you!\n\n".format(
                                        feed.blogurl,
                                        "\n".join(["* " + t for t in titles]),
                                        feed.id),
                                    sendername="Planet PostgreSQL",
                                    receivername="{0} {1}".format(feed.user.first_name, feed.user.last_name),
                                )

                        if entries > 0 and not had_entries:
                            # Entries showed up on a blog that was previously empty
                            send_simple_mail(
                                settings.EMAIL_SENDER,
                                settings.NOTIFICATION_RECEIVER,
                                "A blog was added to Planet PostgreSQL",
                                "The blog at {0} by {1}\nwas added to Planet PostgreSQL, and has now received entries.\n\nTo moderate: https://planet.postgresql.org/register/moderate/\n\n".format(feed.feedurl, feed.user),
                                sendername="Planet PostgreSQL",
                                receivername="Planet PostgreSQL Moderators",
                            )

                if self.debug:
                    # Roll back transaction without error
                    raise BreakoutException()
        except BreakoutException:
            self.stderr.write("Rolling back all changes")
            pass

        if total_entries > 0 and not self.debug:
            purge_root_and_feeds()

    def _fetch_one_feed(self, fetcher):
        if self.full:
            self.trace("Fetching %s" % fetcher.feed.feedurl)
            since = None
        else:
            since = fetcher.feed.lastget
            self.trace("Fetching %s since %s" % (fetcher.feed.feedurl, since))
        try:
            entries = list(fetcher.parse(since))
        except ParserGotRedirect as e:
            return (fetcher.feed, e)
        except Exception as e:
            self.stderr.write("Failed to fetch '%s': %s" % (fetcher.feed.feedurl, e))
            return (fetcher.feed, e)
        return (fetcher.feed, entries)
