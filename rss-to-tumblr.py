from feedreader.parser import from_url
import datetime
import re
import sqlite3
import urllib
import urllib2

try:
    from settings import *
except ImportError:
    pass

conn = sqlite3.connect('db.sqlite')
conn.isolation_level = None

GROUP = 'http://YOUR TUMBLR.tumblr.com'
ENDPOINT = 'http://www.tumblr.com/api/write'
EMAIL = 'YOUR EMAIL'
PASSWORD = 'YOUR PASSWORD'

TAGS = ''

FEEDS = (
    ('USERNAME', 'FEED URL'),
)

def slugify(value):
    """
    Normalizes string, converts to lowercase, removes non-alpha characters,
    and converts spaces to hyphens.
    """
    import unicodedata
    value = unicodedata.normalize('NFKD', value).encode('ascii', 'ignore')
    value = unicode(re.sub('[^\w\s-]', '', value).strip().lower())
    value = re.sub('[-\s]+', '-', value)
    return value

class TumblrError(Exception): pass

class FeedAggregator(object):
    def collect(self, author, feed_url): 
        feed = from_url(feed_url)
        for entry in feed.entries:
            cursor = conn.cursor()
            cursor.execute('select 1 from entries where url = ? limit 1', [unicode(entry.link)])
            if not cursor.fetchall():
                slug = '%s-%s' % (author, slugify(unicode(entry.title)))
                self.write(entry.link, entry.title, entry.description, entry.published, slug)
                cursor.execute('insert into entries values(?)', [unicode(entry.link)])
    
    def write(self, url, title, description, date=None, slug=None):
        print "Saving", url
        if not date:
            date = datetime.datetime.now()
        
        out = {
            'email': EMAIL,
            'password': PASSWORD,
            'type': 'link',
            'format': 'html',
            'state': 'published',
            'group': GROUP,
            'generator': 'SexyTumblrRSS 1.0',
            'tags': TAGS,
            'name': title,
            'url': url,
            'slug': slug,
            'description': description,
            'date': date.strftime('%Y-%m-%d %H:%M:%S'),
        }
        
        req = urllib2.Request(ENDPOINT, urllib.urlencode(out))
        try:
            f = urllib2.urlopen(req)
        except urllib2.URLError, e:
            raise TumblrError(e.read())
        else:
            response = f.read()
            print response

def main():
    conn.execute('create table if not exists entries (url text)')
    
    agg = FeedAggregator()
    for author, feed in FEEDS:
        agg.collect(author, feed)

if __name__ == '__main__':
    main()