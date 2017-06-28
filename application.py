import random
import string
import httplib2
import json

from functools import wraps

from flask import Flask, render_template, url_for, request, redirect
from flask import flash
from flask import jsonify, make_response
from flask import session as login_session

from oauth2client.client import flow_from_clientsecrets
from oauth2client.client import FlowExchangeError
import requests

import crud
import helper

app = Flask(__name__)
app.secret_key = 'some_secret'


generalData = {}
categories = {}  # falsedata.categories


# LOGIN
def checkUser(email, name, picture):
    user = crud.getUserByEmail(email)
    if user:
        return user.id
    else:
        user = crud.createUser(
            username=login_session['username'],
            email=login_session['email'],
            password="",
            picture=login_session['picture']
        )
        return user.id
# 

# SECURITY
def authentication(f):
    @wraps(f)
    def decorated_func(*args, **kwargs):
        if 'username' not in login_session:
            flash("The page requires login!")
            return redirect(url_for('login'))
        else:
            return f(*args, **kwargs)
    return decorated_func


def authorization(f):
    @wraps(f)
    def decorated_func(*args, **kwargs):
        product_name = kwargs['product_name']
        product = crud.getProductByName(product_name)
        if login_session['email'] == 'admin@catalogapp.com':
            return f(*args, **kwargs)
        elif login_session['user_id'] != product.owner_id:
            return 'Must be the item owner to view, \
            Click <a href="%s">Here</a> to go back' % (
                request.referrer)
        else:
            return f(*args, **kwargs)
    return decorated_func


def adminOnly(f):
    @wraps(f)
    def decorated_func(*args, **kwargs):
        if 'email' in login_session and \
           login_session['email'] == 'admin@catalogapp.com':
            return f(*args, **kwargs)
        else:
            return 'Must login using admin@catalogapp.com to view, \
            Click <a href="%s">Here</a> to go back' % (
                request.referrer)


# Experiment Function (OBSOLETED BY authorization wrapper)
# def authorization2(product):
#     if product.owner_id == login_session['user_id']:
#         return True
#     elif login_session['email'] == 'admin@catalogapp.com':
#         return True
#     else:
#         return False


@app.route('/login/', methods=['GET', 'POST'])
def login():
    if request.method == 'GET':
        if 'email' in login_session:
            print login_session['email'], login_session['username']
            return redirect(url_for('showHome'))
        state = "".join(
            random.choice(
                string.ascii_uppercase + string.digits
            )
            for x in xrange(32))
        login_session['state'] = state
        return render_template("login.html", state=state)
    if request.method == 'POST':
        if 'email' in login_session:
            print login_session['email'], login_session['username']
            return redirect(url_for('showHome'))
        if request.form['state'] != login_session['state']:
            return redirect(url_for('login'))
        user = crud.getUserByEmail(request.form['email'])
        if user and helper.valid_pw(
            request.form['email'],
            request.form['password'], user.password
        ):
            login_session['user_id'] = user.id
            login_session['email'] = user.email
            login_session['username'] = user.username
            generalData['login_session'] = login_session
            print "user logged in as %s !" % (login_session['username'])
            return redirect(url_for('showHome'))
        else:
            flash("Incorrect email or password")
            return redirect(url_for('login'))


@app.route('/signup/', methods=['GET', 'POST'])
def signup():
    if request.method == 'GET':
        return render_template("signup.html")

    if request.method == 'POST':
        have_error = False
        email = request.form['email']
        username = request.form['username']
        password = request.form['password']
        verify = request.form['verify']

        params = dict(email=email, username=username)

        if not helper.valid_email(email):
            have_error = True
            params['error_email'] = 'Not valid email'
        if not helper.valid_username(username):
            have_error = True
            params['error_username'] = 'Not valid username'
        if not helper.valid_password(password):
            have_error = True
            params['error_password'] = 'Not valid password'
        if password != verify:
            have_error = True
            params['error_verify'] = 'The password is \
            not as same as verification'

        if have_error:
            return render_template('signup.html', **params)
        else:
            h = helper.make_pw_hash(email, password)
            crud.createUser(username, email, h)
            return redirect(url_for('login'))
        return redirect(url_for('showHome'))


@app.route('/logout/')
@authentication
def logout():
    if 'provider' in login_session and login_session['provider'] == 'facebook':
        print ">>Facebook disconnect"
        facebook_id = login_session['provider_id']
        url = "https://graph.facebook.com/v2.8/%s/permissions?"\
            "access_token=%s" %\
            (facebook_id, login_session['access_token'])
        del login_session['provider']
        del login_session['provider_id']
        del login_session['access_token']
        del login_session['email']
        del login_session['username']
        del login_session['picture']
        del login_session['user_id']
        httplib2.Http().request(url, 'DELETE')
    elif 'provider' in login_session and login_session['provider'] == 'google':
        print ">>Google disconnect"
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
            del login_session['provider']
            del login_session['provider_id']
            del login_session['credentials']
            del login_session['email']
            del login_session['username']
            del login_session['picture']
            del login_session['user_id']

            # response = make_response(json.dumps('Successfully disconnected'),
            #                          200)
            # response.headers['Content-Type'] = 'application/json'
            flash("Logged out from google")
            return redirect(url_for('showHome'))
        else:
            # response = make_response(json.dumps(
            #     'Failed to revoke token for given user'), 400)
            # response.headers['Content-Type'] = 'application/json'
            flash("Failed to logout from google, try again later")
            return redirect(url_for('showHome'))
    else:
        del login_session['username']
        del login_session['email']
        del login_session['user_id']
        # del generalData['login_session']
    return redirect(url_for('showHome'))


@app.route('/gconnect', methods=['post'])
def gconnect():
    if 'email' in login_session:
        flash("You have signed in. Log out if you wish to sign in with a \
              different account."
              )
        return redirect(url_for('showHome'))
    if request.args.get('state') != login_session['state']:
        response = make_response(json.dumps('Invalid state parameter.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    # Obtain authorization code
    code = request.data

    try:
        # Upgrade the authorization code into a credentials object
        oauth_flow = flow_from_clientsecrets('g_client_secrets.json', scope='')
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
    client_id = json.loads(
        open('g_client_secrets.json', 'r').read()
    )['web']['client_id']
    if result['issued_to'] != client_id:
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
    login_session['provider_id'] = gplus_id

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
    generalData['login_session'] = login_session
    # output = ''
    # output += '<h1>Welcome, '
    # output += login_session['username']
    # output += '!</h1>'
    # output += '<img src="'
    # output += login_session['picture']
    # output += ' " style = "width: 300px; height: 300px;border-radius:'
    # output += ' 150px;-webkit-border-radius: 150px;'
    # output += '-moz-border-radius: 150px;"> '
    flash("you are now logged in as %s" % login_session['username'])
    return 'success'


@app.route('/fbconnect', methods=['post'])
def fbconnect():
    if 'email' in login_session:
        flash("You have signed in. Log out if you wish to sign in with a \
              different account."
              )
        return redirect(url_for('showHome'))

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

    login_session['email'] = data['email']
    login_session['username'] = data['name']
    login_session['provider'] = 'facebook'
    login_session['provider_id'] = data['id']

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
    generalData['login_session'] = login_session
    print ">>>>facebook_id: ", login_session['provider_id']
    return 'success'


@app.route("/")
def showHome():
    # for i in login_session:
    #     print str(i) + ":" + str(login_session[i])
    loadGeneralData()
    if not 'login_session' in generalData:
    	generalData['login_session'] = login_session
    return render_template("base.html", **generalData)


@app.route('/category/new/', methods=['get', 'post'])
@authentication
def newCategory():
    # return "This page will be for making a new category"
    if request.method == 'GET':
        loadGeneralData()
        return render_template(
            "categoryEdit.html", category=None,
            title="New Category", delete=False, **generalData)
    if request.method == 'POST':
        category = crud.newCategory(request.form['CategoryName'])
        if category:
            flash('new category created')
        else:
            flash('Failed to create new category')
        return redirect(url_for('showHome'))


@app.route("/<string:category_name>/edit/", methods=['GET', 'POST'])
@authentication
def editCategory(category_name):
    print category_name
    if request.method == 'GET':
        category = crud.getCategoryByName(category_name)
        loadGeneralData()
        return render_template(
            "categoryEdit.html", category=category,
            title="EDIT Category", delete=True, **generalData)
    if request.method == 'POST':
        category = crud.editCategory(
            category_name, request.form['CategoryName'])
        if category:
            flash("%s successfully updated to %s" % (
                category_name, category.name))
        return redirect(url_for('showHome'))


@app.route("/<string:category_name>/delete/", methods=['GET', 'POST'])
@authentication
def deleteCategory(category_name):
    # return "This page will be for deleting category %s" % category_id
    if request.method == 'GET':
        return render_template(
            "categoryDelete.html", title="DELETE category",
            name=category_name, **generalData)
    if request.method == 'POST':
        if crud.deleteCategoryByName(category_name):
            flash('Category %s Successfully Deleted' % category_name)
        else:
            flash('Failed to delete category %s' % category_name)
        return redirect(url_for('showHome'))


@app.route("/<string:category_name>/products/", defaults={'category_id': 0})
@app.route("/category <int:category_id>/", defaults={'category_name': ''})
def showProducts(category_name, category_id):
    # return "This page is the menu for category %s" % category_id
    # products = falsedata.products
    products = {}
    generalData['category_name'] = category_name

    if category_id == 0:
        category = crud.getCategoryByName(category_name)
        if category:
            print category.id, category.name
            products = crud.showProducts(category.id)
    elif category_name == '':
        products = crud.showProducts(category_id)
    else:
        products = crud.showProducts()
    loadGeneralData()
    return render_template("productlist.html", products=products,
                           category_id=category_id, **generalData)


@app.route("/<string:category_name>/<string:product_name>/",
           defaults={"product_id": 0})
@app.route("/product/<int:product_id>/",
           defaults={"product_name": None, "category_name": None})
def showProductDetail(product_id, product_name, category_name):
    # return "This page is the menu for category %s" % category_id
    # product = falsedata.product
    if product_id != 0:
        product = crud.getProductById(product_id)
    else:
        product = crud.getProductByName(product_name)
    isOwner = False
    if product and\
       'user_id' in login_session and\
       product.owner_id == login_session['user_id']:
        isOwner = True
    elif 'email' in login_session and \
         login_session['email'] == 'admin@catalogapp.com':
        isOwner = True
    loadGeneralData()
    return render_template(
        "productDetail.html", product=product, isOwner=isOwner, **generalData
    )


@app.route("/<string:category_name>/product/new/",
           methods=['get', 'post'])
@authentication
def newProduct(category_name):
    # return "This page is for making a new \
    # menu item for category %s" % category_id
    if request.method == 'GET':
        generalData['category_name'] = category_name
        loadGeneralData()
        return render_template("productEdit.html", **generalData)
    if request.method == 'POST':
        category = crud.getCategoryByName(category_name)
        if category:
            name = request.form['name']
            description = request.form['description']
            price = request.form['price']
            new = crud.newProduct(name, description, price,
                                  category.id, login_session['user_id'])
            if new:
                flash('Product Item Created')
            else:
                flash('Failed to create the product')
            return redirect(
                url_for('showProducts', category_name=category_name))
        return redirect(url_for('showError'))


@app.route("/<string:category_name>/<string:product_name>/edit/",
           methods=['get', 'post'])
@authentication
@authorization
def editProduct(category_name, product_name, **kwargs):
    if request.method == 'GET':
        generalData['category_name'] = category_name
        loadGeneralData()
        product = crud.getProductByName(product_name)
        if product and category_name == product.category.name:
            return render_template("productEdit.html",
                                   product=product, **generalData)
        else:
            return redirect(url_for("showError"))

    if request.method == 'POST':
        product = crud.getProductByName(product_name)
        if product and category_name == product.category.name:

            name = request.form['name']
            description = request.form['description']
            price = request.form['price']
            crud.editProduct(product, name, price, description)
            flash('Product Item Successfully Edited')
            return redirect(url_for('showProducts',
                                    category_name=category_name))
        else:
            return redirect(url_for("showError"))


@app.route("/<string:category_name>/<string:product_name>/delete/",
           methods=['get', 'post'])
@authentication
def deleteProduct(category_name, product_name):
    if request.method == 'GET':
        product = crud.getProductByName(product_name)
        if not product or category_name != product.category.name:
            return redirect(url_for("showError"))
        return render_template("productDelete.html", title="DELETE category",
                               name=product_name, **generalData)
    if request.method == 'POST':
        product = crud.getProductByName(product_name)
        if not product and category_name != product.category.name:
            return redirect(url_for("showError"))
        # TODO
        if crud.deleteProduct(product):
            flash('Product %s Successfully Deleted' % product_name)
        else:
            flash('Failed to delete Product %s' % product_name)
        return redirect(url_for('showHome'))


# Define API End Point
@app.route("/categories/json/")
@authentication
def showCategoriesJason():
    category = crud.getAllCategories()
    return jsonify(category=[r.serialize for r in category])


@app.route("/<string:category_name>/products/json/")
@authentication
def showProductsJson(category_name):
    products = crud.showProductsByCategoryName(category_name)
    return jsonify(products=[i.serialize for i in products])


@app.route("/<string:category_name>/<string:product_name>/json/")
@authentication
def showProductDetailJson(category_name, product_name):
    item = crud.getProductByName(product_name)
    print item.owner_id
    return jsonify(detail=item.serialize)


@app.route("/error/")
def showError():
    # return 'Oops, something did not go right,<br>\
    # The resource you request does not exist,<br>\
    # Click <a href="%s">Here</a> to go back<br>\
    # </pre>' % (request.referrer)
    return 'Oops, something did not go right,<br>\
    The resource you request does not exist,<br>\
    Click <a href="/">Here</a> to go to home page<br>\
    </pre>'


def loadGeneralData():
    categories = crud.getAllCategories()
    if categories:
        generalData['categories'] = categories
        # generalData['login_session'] = login_session
    else:
        generalData['categories'] = {}
        categories = {}
    return categories




if __name__ == '__main__':
    app.debug = True
    app.run(host='0.0.0.0', port=8000)
