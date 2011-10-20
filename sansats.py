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

@app.route('/<username>/')
def user_timeline(username):
    try:
        tweets = api.user_timeline(username, count=40, include_rts=True)
    except tweepy.TweepError, e:
        if e.response.status == 400:
            return 'rate limiting!'
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