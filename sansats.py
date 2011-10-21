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

@app.route('/', methods=['GET', 'POST'])
def homepage():
    if request.method == 'POST':
        return redirect('/%s' % request.form['username'].strip())
    return render_template('index.html')

@app.route('/favicon.ico')
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

@app.route('/<username>/')
def user_timeline(username):
    try:
        tweets = api.user_timeline(username, count=40, include_rts=True)
    except tweepy.TweepError, e:
        if e.response.status == 400:
            return 'rate limiting!'
    else:
        tweets = [handle_rts(tweet) for tweet in tweets if is_relevant_to_my_interests(tweet.text)]
        return render_template('user_timeline.html', username=username.lower(), tweets=tweets)



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
    app.run(debug=True)
