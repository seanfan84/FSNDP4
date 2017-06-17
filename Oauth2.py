from flask import Flask, render_template, request, redirect,\
    jsonify, url_for, flash
from functools import wraps
# for anti-forgery state token
from flask import session as login_session
import string
import random

from oauth2client.client import flow_from_clientsecrets
from oauth2client.client import FlowExchangeError

from flask import make_response
# A comprehensive HTTP client library.
import httplib2
import requests
import json

app = Flask(__name__)


CLIENT_ID = '407221188946-5r2g4pbsnni5sqqv0cqod9f6ag853t2n'\
            '.apps.googleusercontent.com'

# Connect to Database and create database session
engine = create_engine('sqlite:///restaurantmenuwithuser.db')
Base.metadata.bind = engine

# Create DBSession class at runtime
DBSession = sessionmaker(bind=engine)
# Instantiate DBSession class
session = DBSession()


def createUser(name, email, picture):
    if name and email:
        user = User(name=name, email=email, picture=picture)
        session.add(user)
        session.commit()
    return user


def getUserId(email):
    user = session.query(User).filter_by(email=email)
    if any(user):
        user = user.one()
        return user.id


def getUserInfo(user_id):
    user = session.query(User).filter_by(id=user_id).one()
    return user


def checkUser(email, name, picture):
    print "--------CHECKING USER-------------"
    user_id = getUserId(login_session['email'])

    if user_id:
        print ">>Existing User"
        user = getUserInfo(user_id)
    else:
        print ">>New User"
        user = createUser(
            name=login_session['username'],
            email=login_session['email'],
            picture=login_session['picture']
        )
    return user.id


def requireLogin(f):
    @wraps(f)
    def decorated_func(*args, **kwargs):
        if 'username' not in login_session:
            return redirect(url_for('showLogin'))
        else:
            return f(*args, **kwargs)
    return decorated_func


@app.route('/login/')
def showLogin():
    state = "".join(
        random.choice(
            string.ascii_uppercase + string.digits
        )
        for x in xrange(32))
    login_session['state'] = state
    # return "The current session state is %s" % login_session['state']
    return render_template("login2.html", state=state)


@app.route('/fbconnect', methods=['post'])
def fbconnect():
    # if 'provider' in login_session:
    #     flash("You have signed in with your" + login_session['provider'] +
    #         "account. Log out if you with to sign in with a different account."
    #         )
    #     return redirect(url_for('showRestaurants'))

    if request.args.get('state') != login_session['state']:
        print 'not equal'
        response = make_response('Invalid state parameter.', 401)
        return response
    access_token = request.data
    print '>>>>access token: ', access_token
    url = "https://graph.facebook.com/v2.8/me?"\
          "fields=name,email&access_token=%s" % access_token
    print ">>>>CALLING Facebook GRAPH API: ", url
    h = httplib2.Http()
    result = h.request(url, 'GET')[1]
    print result

    app_id = json.loads(
        open('fb_client_secrets.json', 'r').read()
    )['web']['app_id']

    app_secret = json.loads(
        open('fb_client_secrets.json', 'r').read()
    )['web']['app_secret']

    url = "https://graph.facebook.com/v2.8/oauth/access_token?"\
        "grant_type=fb_exchange_token&"\
        "client_id=%s&client_secret=%s&fb_exchange_token=%s"\
        % (app_id, app_secret, access_token)

    print ">>TOKEN EXCHANGE: ", url
    h = httplib2.Http()
    result = json.loads(h.request(url, 'GET')[1])
    print ">>LONG LIVE TOKEN RECEIVED: ", result
    login_session['access_token'] = result['access_token']

    url = "https://graph.facebook.com/v2.8/me?"\
        "fields=id,name,email&access_token=%s" % result["access_token"]
    print ">>>>TRYING NEW TOKEN: ", url
    h = httplib2.Http()
    result = h.request(url, 'GET')
    print "RESPONSE[1]", result[1]

    data = json.loads(result[1])

    login_session['provider'] = 'facebook'
    login_session['username'] = data['name']
    login_session['facebook_id'] = data['id']
    login_session['email'] = data['email']

    url = "https://graph.facebook.com/v2.8/%s/picture?access_token"\
          "=%s&redirect=0" % (data['id'], access_token)
    print ">>>>GETTING FACEBOOK PROFILE PICTURE: ", url

    h = httplib2.Http()
    result = json.loads(h.request(url, 'GET')[1])
    print result['data'][u'url']
    login_session['picture'] = result['data']['url']
    print login_session['picture']

    login_session['user_id'] = checkUser(
        login_session['email'],
        login_session['username'],
        login_session['picture'])
    print ">>>>facebook_id: ", login_session['facebook_id']
    return 'success'


@app.route('/gconnect', methods=['post'])
def gconnect():
    # Validate state token
    print request.args.get('state') + '|' + login_session['state']
    if request.args.get('state') != login_session['state']:
        response = make_response(json.dumps('Invalid state parameter.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    # Obtain authorization code
    code = request.data

    try:
        # Upgrade the authorization code into a credentials object
        oauth_flow = flow_from_clientsecrets('client_secrets.json', scope='')
# !!!question
        # Applications that use languages and frameworks like PHP,
        # Java, Python, Ruby, and .NET must specify authorized
        # redirect URIs. The redirect URIs are the endpoints to
        # which the OAuth 2.0 server can send responses.
        oauth_flow.redirect_uri = 'postmessage'

        # Credentials have access_token and id_token
        credentials = oauth_flow.step2_exchange(code)
    except FlowExchangeError:
        response = make_response(
            json.dumps('Failed to upgrade the authorization code.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Check that the access token is valid.
    access_token = credentials.access_token
    print access_token
    url = ('https://www.googleapis.com/oauth2/v1/tokeninfo?access_token=%s'
           % access_token)
    h = httplib2.Http()
    result = json.loads(h.request(url, 'GET')[1])
    # If there was an error in the access token info, abort.
    if result.get('error') is not None:
        response = make_response(json.dumps(result.get('error')), 500)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Verify that the access token is used for the intended user.
    print 'credentials.id_token[sub]:' + credentials.id_token['sub']
    gplus_id = credentials.id_token['sub']
    print 'userID:' + result['user_id']
    if result['user_id'] != gplus_id:
        response = make_response(
            json.dumps("Token's user ID doesn't match given user ID."), 401)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Verify that the access token is valid for this app.
    print 'result[issued_to]:' + result['issued_to']
    print CLIENT_ID
    if result['issued_to'] != CLIENT_ID:
        response = make_response(
            json.dumps("Token's client ID does not match app's."), 401)
        print "Token's client ID does not match app's."
        response.headers['Content-Type'] = 'application/json'
        return response

    stored_credentials = login_session.get('credentials')
    print ">>>>STORED CREDENTIALS: " + str(stored_credentials)

    stored_gplus_id = login_session.get('gplus_id')
    if stored_credentials is not None and gplus_id == stored_gplus_id:
        response = make_response(
            json.dumps('Current user is already connected.'), 200
        )
        response.headers['Content-Type'] = 'application/json'
        return response

    # Store the access token in the session for later use.
    login_session['credentials'] = credentials.to_json()
    login_session['gplus_id'] = gplus_id

    # Get user info
    userinfo_url = "https://www.googleapis.com/oauth2/v1/userinfo"
    params = {'access_token': credentials.access_token, 'alt': 'json'}
    answer = requests.get(userinfo_url, params=params)

    data = answer.json()
    login_session['provider'] = 'google'
    login_session['username'] = data['name']
    login_session['picture'] = data['picture']
    login_session['email'] = data['email']

    login_session['user_id'] = checkUser(
        login_session['email'],
        login_session['username'],
        login_session['picture'])

    output = ''
    output += '<h1>Welcome, '
    output += login_session['username']
    output += '!</h1>'
    output += '<img src="'
    output += login_session['picture']
    output += ' " style = "width: 300px; height: 300px;border-radius:'
    output += ' 150px;-webkit-border-radius: 150px;'
    output += '-moz-border-radius: 150px;"> '
    flash("you are now logged in as %s" % login_session['username'])
    return output


@app.route('/disconnect')
def disconnect():
    if 'provider' in login_session:
        if login_session['provider'] == 'google':
            gdisconnect()
        if login_session['provider'] == 'facebook':
            fbdisconnect()
        response = make_response(
            json.dumps('Successful'), 200
        )
        flash("you have logged out successfully")
        return redirect(url_for('showRestaurants'))
    else:
        response = make_response(
            json.dumps('Current user not connected.'), 401
        )
        response.headers['Content-Type'] = 'application/json'
        return response


@app.route('/gdisconnect')
def gdisconnect():
    credentials = login_session['credentials']
    if not credentials:
        response = make_response(
            json.dumps('Current user not connected.'), 401
        )
        response.headers['Content-Type'] = 'application/json'
        return response
    credentials = json.loads(credentials)
    token = credentials['access_token']
    print token
    url = 'https://accounts.google.com/o/oauth2/revoke?token=%s' % token
    print url
    h = httplib2.Http()
    result = h.request(url, 'GET')[0]

    print result
    if result.status == 200:
        del login_session['credentials']
        del login_session['gplus_id']
        del login_session['username']
        del login_session['email']
        del login_session['picture']
        response = make_response(json.dumps('Successfully disconnected'), 200)
        response.headers['Content-Type'] = 'application/json'
        return response
    else:
        response = make_response(json.dumps(
            'Failed to revoke token for given user'), 400)
        response.headers['Content-Type'] = 'application/json'
        return response



@app.route('/fbdisconnect')
def fbdisconnect():
    print ">>Facebook disconnect"
    if 'facebook_id' in login_session:
        facebook_id = login_session['facebook_id']
        url = "https://graph.facebook.com/v2.8/%s/permissions?"\
              "access_token=%s" % (facebook_id, login_session['access_token'])
        del login_session['facebook_id']
        del login_session['access_token']
        del login_session['email']
        del login_session['username']
        del login_session['picture']
        del login_session['user_id']
        httplib2.Http().request(url, 'DELETE')
        # Log got verification is not implemented, as it keeps throwing
        # broken pipe error
        print "LOGGED OUT SUCCESSFULLY"
    else:
        print "NOT LOGGED IN"
    return redirect(url_for("showLogin"))