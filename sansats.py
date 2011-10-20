import datetime
import tweepy

from flask import abort, Flask, render_template

app = Flask(__name__)

APP_KEY = ''
APP_SECRET = ''
auth = tweepy.OAuthHandler(APP_KEY, APP_SECRET)
api = tweepy.API(auth)

@app.route('/')
def homepage():
    return 'hello world'

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
        return render_template('user_timeline.html', tweets=tweets)


def is_relevant_to_my_interests(tweet_text, following=None):
    if tweet_text[0] != '@':
        return True
    elif following and tweet_text[1:].split() and tweet_text[1:].split()[0].lower() in following:
        return True
    return False

def format_tweet_time(tweet_time):
    # hard coding to eastern dst for now
    return (tweet_time-datetime.timedelta(hours=4)).strftime('%B %d, %Y, %I:%M %p')

app.jinja_env.filters['format_tweet_time'] = format_tweet_time

if __name__ == '__main__':
    app.run(debug=True)