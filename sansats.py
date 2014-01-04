import datetime
import re
import tweepy

from flask import abort, Flask, Markup, render_template, request, redirect
from functools import partial

app = Flask(__name__)

APP_KEY = ''
APP_SECRET = ''
auth = tweepy.OAuthHandler(APP_KEY, APP_SECRET)
api = tweepy.API(auth)

# set to empty string when serving from domain root (example.com)
# set to 'prefix/' when serving from example.com/prefix
APP_ROOT = 't/'

@app.route('/%s' % APP_ROOT, methods=['GET', 'POST'])
def homepage():
    if request.method == 'POST':
        return redirect('/%s%s' % (APP_ROOT, request.form['username'].strip()))
    return render_template('index.html')

@app.route('/%sfavicon.ico' % APP_ROOT)
def favicon():
    return abort(404)

def handle_rts(tweet):
    '''
    If tweet is a retweet, set tweet.text using "RT @username: original tweet" format.
    We do this because otherwise retweets near 140 character limit will be truncated.
    '''
    if hasattr(tweet, 'retweeted_status'):
        tweet.text = 'RT @%s: %s' % (tweet.retweeted_status.user.screen_name, tweet.retweeted_status.text)
    return tweet

@app.route('/%s<username>/' % APP_ROOT, defaults={'tweet_id':None})
@app.route('/%s<username>/<int:tweet_id>' % APP_ROOT)
def user_timeline(username, tweet_id):

    filtered_tweets = []
    tweets = []
    status = 200
    if tweet_id:
        tweet_id = int(tweet_id) - 1
    try:
        tweets = api.user_timeline(username, count=60, include_rts=True, max_id=tweet_id)
    except tweepy.TweepError, e:
        status = e.response.status
    else:
        filtered_tweets = [handle_rts(tweet) for tweet in tweets if is_relevant_to_my_interests(tweet.text)]
    if len(tweets) > 1 and not filtered_tweets:
        return user_timeline(username, tweets[-1].id)
    kwargs = dict(username=username.lower(), tweets=filtered_tweets, status=status, app_root=APP_ROOT)
    return render_template('user_timeline.html', **kwargs)

def is_relevant_to_my_interests(tweet_text, following=None):
    if tweet_text[0] != '@':
        return True
    elif following and tweet_text[1:].split() and tweet_text[1:].split()[0].lower() in following:
        return True
    return False

def format_tweet_time(tweet_time):
    # hard coding to eastern dst for now
    return (tweet_time-datetime.timedelta(hours=4)).strftime('%B %d, %Y, %I:%M %p')

# This was taken from readmindme and modified to link to the current site instead of twitter.
# http://code.google.com/p/readmindme/
# readmindme.templatetags.tags
AT_RE = re.compile(r'(?P<prefix>(?:\W|^)@)(?P<username>[a-zA-Z0-9_]+)\b')
def user_page_link(host):
    link_sub_strings = ['%(prefix)s<a href="http://', host, '/%(username)s">%(username)s</a>']
    return ''.join(link_sub_strings)
def _SubAtReply(match, host):
    return user_page_link(host) % match.groupdict()

def urlize_ats(value):
    '''
    Link @ mentions to that user's page on the site.
    '''
    if isinstance(value, Markup):
        value = value.unescape()
    host = request.host
    return Markup(AT_RE.sub(partial(_SubAtReply, host=host), value))

app.jinja_env.filters['format_tweet_time'] = format_tweet_time
app.jinja_env.filters['urlize_ats'] = urlize_ats

if __name__ == '__main__':
    app.run()
