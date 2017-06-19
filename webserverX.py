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
import falsedata

app = Flask(__name__)
app.secret_key = 'some_secret'

generalData = {}
categories = {}  # falsedata.categories

# LOGIN
def checkUser(email, name, picture):
    print "--------CHECKING USER-------------"
    # user_id = crud.getUserId(login_session['email'])

    # if user_id:
    #     print ">>Existing User"
    #     user = crud.getUserInfo(user_id)
    # else:
    #     print ">>New User"
    #     user = crud.createUser(
    #         name=login_session['username'],
    #         email=login_session['email'],
    #         picture=login_session['picture']
    #     )
    # return user.id
    return 1


# SECURITY
def autentication(f):
    @wraps(f)
    def decorated_func(*args, **kwargs):
        if 'username' not in login_session:
            return redirect(url_for('showLogin'))
        else:
            return f(*args, **kwargs)
    return decorated_func


def authorization(f):
    @wraps(f)
    def decorated_func(*args, **kwargs):
        if 'user_id' not in login_session:
            return redirect(url_for('showLogin'))
        elif login_session['user_id'] != owner_id:
            return 'Not Autherized, Click <a href="%s">Here</a> to go back' % (
                request.referrer)
        else:
            return f(*args, **kwargs)
    return decorated_func


@app.route('/google')
def testgoogle():
    state = "".join(
        random.choice(
            string.ascii_uppercase + string.digits
        )
        for x in xrange(32))
    login_session['state'] = state
    return render_template("google.html", state=state)


@app.route('/login')
def login():
    state = "".join(
        random.choice(
            string.ascii_uppercase + string.digits
        )
        for x in xrange(32))
    login_session['state'] = state
    return render_template("login.html", state=state)


@app.route('/signup')
def signup():
    return render_template("signup.html")


@app.route('/logout')
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
    if 'provider' in login_session and login_session['provider'] == 'google':
        pass
    return redirect(url_for('showHome'))


@app.route('/gconnect', methods=['post'])
def gconnect():
    print 'gconnect'
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
    # if 'provider' in login_session:
    #     flash("You have signed in with your" + login_session['provider'] +
    #         "account. Log out if you with to sign in with a different account."
    #         )
    #     return redirect(url_for('showRestaurants'))
    print "fbconnect"
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
    print ">>>>facebook_id: ", login_session['provider_id']
    return 'success'


@app.route("/")
def showHome():
    for i in login_session:
        print str(i) + ":" + str(login_session[i])
    return render_template("base.html", categories=loadCategory())


@app.route('/category/new/', methods=['get', 'post'])
def newCategory():
    # return "This page will be for making a new category"
    if request.method == 'GET':
        loadCategory()
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
def editCategory(category_name):
    print category_name
    if request.method == 'GET':
        category = crud.getCategoryByName(category_name)
        loadCategory()
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
@app.route("/category<int:category_id>/", defaults={'category_name': ''})
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
    loadCategory()
    return render_template("productlist.html", products=products,
                           category_id=category_id, **generalData)


@app.route("/<string:category_name>/<string:product_name>",
           defaults={"product_id": 0})
@app.route("/product/<int:product_id>",
           defaults={"product_name": None, "category_name": None})
def showProductDetail(product_id, product_name, category_name):
    # return "This page is the menu for category %s" % category_id
    # product = falsedata.product
    if product_id != 0:
        product = crud.getProductById(product_id)
    else:
        product = crud.getProductByName(product_name)
    return render_template(
        "productDetail.html", product=product, **generalData
    )


@app.route("/<string:category_name>/product/new/",
           methods=['get', 'post'])
def newProduct(category_name):
    # return "This page is for making a new \
    # menu item for category %s" % category_id
    if request.method == 'GET':
        return render_template("productEdit.html", **generalData)
    if request.method == 'POST':
        category = crud.getCategoryByName(category_name)
        if category:
            name = request.form['name']
            description = request.form['description']
            price = request.form['price']
            new = crud.newProduct(name, description, price, category.id, 1)
            if new:
                flash('Product Item Created')
            else:
                flash('Failed to create the product')
            return redirect(
                url_for('showProducts', category_name=category_name))
        return redirect(url_for('showError'))


@app.route("/category/<int:category_id>/product/<int:product_id>/edit/",
           methods=['get', 'post'])
def editProduct(category_id, product_id):
    # return "This page is for editing menu item %s " % product_id
    if request.method == 'GET':
        # menuItem = crud.getProductById(product_id)
        menuItem = falsedata.product
        return render_template("productEdit.html", item=menuItem,
                               category_id=category_id, **generalData)
    if request.method == 'POST':
        name = request.form['name']
        description = request.form['description']
        price = request.form['price']
        course = request.form['course']
        crud.editProductItem(product_id, name, description, price, course)
        flash('Product Item Successfully Edited')
        return redirect(url_for('showProduct', category_id=category_id))


@app.route("/category/<int:category_id>/menu/<int:product_id>/delete/",
           methods=['get', 'post'])
def deleteProduct(category_id, product_id):
    # return "This page is for deleting menu item %s" % product_id
    if request.method == "GET":
        return render_template("deleteProductItem.html",
                               category_id=category_id, id=product_id)
    if request.method == "POST":
        crud.deleteProductItem(product_id)
        flash('Product Item Successfully Delete')
        return redirect(url_for('showProduct', category_id=category_id))


# Define API End Point
@app.route("/category/json/")
def showCatalogJson():
    category = crud.showCatalog()
    return jsonify(category=[r.serialize for r in category])


@app.route("/category/<int:category_id>/json/")
def showProductsJson(category_id):
    products = crud.showProducts(category_id)
    return jsonify(products=[i.serialize for i in products])


@app.route("/category/<int:category_id>/<int:product_id>/json/")
def showProductDetailJson(category_id, product_id):
    item = crud.getProductById(product_id)
    return jsonify(category=item.serialize)


@app.route("/error/")
def showError():
    return 'Oops, something did not go right,<br>\
    The resource you request does not exist,<br>\
    Click <a href="%s">Here</a> to go back<br>\
    </pre>' % (request.referrer)


def loadCategory():
    categories = crud.getAllCategories()
    if categories:
        generalData['categories'] = categories

    else:
        generalData['categories'] = {}
        categories = {}
    return categories


if __name__ == '__main__':
    app.debug = True
    app.run(host='0.0.0.0', port=5000)
