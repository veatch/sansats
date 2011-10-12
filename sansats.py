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

if __name__ == '__main__':
    app.run(debug=True)