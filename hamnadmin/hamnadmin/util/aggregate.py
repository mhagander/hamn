#!/usr/bin/env python3

import datetime
import socket

from vendor.feedparser import feedparser

from hamnadmin.register.models import Post


class ParserGotRedirect(Exception):
    def __init__(self, url):
        self.url = url
        super(Exception, self).__init__()


class FeedFetcher(object):
    def __init__(self, feed, tracefunc=None, update=True):
        self.feed = feed
        self.tracefunc = tracefunc
        self.update = update
        self.newest_entry_date = None

    def _trace(self, msg):
        if self.tracefunc:
            self.tracefunc(msg)

    def parse(self, fetchsince=None):
        # If we can't get a socket connection to complete in 10 seconds,
        # give up on that feed.
        socket.setdefaulttimeout(10)

        if fetchsince:
            parser = feedparser.parse(self.feed.feedurl, modified=fetchsince.timetuple())
        else:
            parser = feedparser.parse(self.feed.feedurl)

        if not hasattr(parser, 'status'):
            # bozo_excpetion can seemingly be set when there is no error as well,
            # so make sure we only check if we didn't get a status.
            if hasattr(parser, 'bozo_exception'):
                raise Exception('Feed load error %s' % parser.bozo_exception)
            raise Exception('Feed load error with no exception!')

        if parser.status == 304:
            # Not modified
            return

        if parser.status == 301 and hasattr(parser, 'href'):
            # Permanent redirect. Bubble this up with an exception and let the caller
            # handle it.
            raise ParserGotRedirect(parser.href)

        if parser.status != 200:
            raise Exception('Feed returned status %s' % parser.status)

        self._trace("Fetched %s, status %s" % (self.feed.feedurl, parser.status))

        try:
            if self.feed.blogurl == '':
                self.feed.blogurl = parser.feed.link
            elif self.feed.blogurl != parser.feed.link:
                self.feed.new_blogurl = parser.feed.link
        except Exception:
            pass

        for entry in parser.entries:
            if not self.matches_filter(entry):
                self._trace("Entry %s does not match filter, skipped" % entry.link)
                continue

            # Grab the entry. At least atom feeds from wordpress store what we
            # want in entry.content[0].value and *also* has a summary that's
            # much shorter.
            # We therefor check all available texts, and just pick the one that
            # is longest.
            txtalts = []
            try:
                txtalts.append(entry.content[0].value)
            except Exception:
                pass
            if 'summary' in entry:
                txtalts.append(entry.summary)

            # Select the longest text
            txt = max(txtalts, key=len)
            if txt == '':
                self._trace("Entry %s has no contents" % entry.link)
                continue

            dat = None
            if hasattr(entry, 'published_parsed'):
                dat = datetime.datetime(*(entry.published_parsed[0:6]))
            elif hasattr(entry, 'updated_parsed'):
                dat = datetime.datetime(*(entry.updated_parsed[0:6]))
            else:
                self._trace("Failed to get date for entry %s (keys %s)" % (entry.link, list(entry.keys())))
                continue

            if dat > datetime.datetime.now():
                dat = datetime.datetime.now()

            if self.newest_entry_date:
                if dat > self.newest_entry_date:
                    self.newest_entry_date = dat
            else:
                self.newest_entry_date = dat

            yield Post(feed=self.feed,
                       guid=entry.id,
                       link=entry.link,
                       txt=txt,
                       dat=dat,
                       title=entry.title,
                       )

        # Check if we got back a Last-Modified time
        if hasattr(parser, 'modified_parsed') and parser['modified_parsed']:
            # Last-Modified header retrieved. If we did receive it, we will
            # trust the content (assuming we can parse it)
            d = datetime.datetime(*parser['modified_parsed'][:6])
            if (d - datetime.datetime.now()).days > 5:
                # Except if it's ridiculously long in the future, we'll set it
                # to right now instead, to deal with buggy blog software. We
                # currently define rediculously long as 5 days
                d = datetime.datetime.now()

            if self.update:
                self.feed.lastget = d
                self.feed.save(update_fields=['lastget'])
        else:
            # We didn't get a Last-Modified time, so set it to the entry date
            # for the latest entry in this feed.
            if self.newest_entry_date and self.update:
                self.feed.lastget = self.newest_entry_date
                self.feed.save(update_fields=['lastget'])

    def matches_filter(self, entry):
        # For now, we only match against self.feed.authorfilter. In the future,
        # there may be more filters.
        if self.feed.authorfilter:
            # Match against an author filter

            if 'author_detail' in entry:
                return entry.author_detail.name == self.feed.authorfilter
            elif 'author' in entry:
                return entry.author == self.feed.authorfilter
            else:
                return False

        # No filters, always return true
        return True
