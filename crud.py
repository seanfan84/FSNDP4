from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine
from database_setup import Base
from database_setup import Category
from database_setup import Product
from database_setup import User
# import string

# engine = create_engine('sqlite:///productdata.db', echo=True)
# IN MEM
engine = create_engine('sqlite:///catalog.db', echo=True)
Base.metadata.create_all(engine)
# End In MEM
Base.metadata.bind = engine
Session = sessionmaker(bind=engine)
session = Session()


# returns all categories, used in sidebars
def showCategory():
    '''return all categories'''
    ls = session.query(Category).all()
    # for i in ls:
    #     print i.__dict__
    return ls


# makes a new category
def newCategory(name):
    '''This function will strip any leading and tailing space tab newline
    '''
    name = name.strip()
    if name == '':
        return None
    new = Category(name=name.lower(),)
    try:
        session.add(new)
        session.commit()
        return new
    except Exception:
        session.rollback()
        return None


def getAllCategories():
    category = session.query(Category).all()
    if any(category):
        return category


def getCategoryByID(id):
    category = session.query(Category).filter_by(id=id)
    if any(category):
        return category.one()


def getCategoryByName(name):
    category = session.query(Category).filter_by(name=name)
    if any(category):
        return category.one()


def editCategory(old_name, name):
    """Rename category, stripped and name must not be empty string

    Keyword Arguments:
    old_name -- string
    name     -- string
    """
    edit = session.query(Category).filter_by(name=old_name)
    name = name.strip()
    try:
        if edit.one() and name != "":
            edit = edit.one()
            print edit.__dict__
            edit.name = name.lower()
            # session.add(edit)
            session.commit()
            print "Success: Edit Category (%s) successful" % edit.id
            return edit
        else:
            print "Failure: Category (%s) NOT found" % id
            return None
    except Exception:
        print Exception.__dict__
        session.rollback()
        return None


def deleteCategory(id):
    delete = session.query(Category).filter_by(id=id)
    try:
        if any(delete):
            name = delete.name
            delete = delete.one()
            session.delete(delete)
            session.commit()
            print "Success: delete Category (%s,%s) successful" % (id, name)
        else:
            print "Failure: Category (%s,%s) NOT found" % (id, name)
    except Exception:
        print "rollback?"
        session.rollback()


def deleteCategoryByName(name):
    """Select category by name, if there is only one, delete it, return bool
    True - for success
    False - for faillure
    """
    delete = session.query(Category).filter_by(name=name)
    try:
        if delete.one():
            delete = delete.one()
            products = session.query(Product).filter_by(
                category_id=delete.id).all()
            if any(products):
                for each in products:
                    session.delete(each)
            session.delete(delete)
            session.commit()
            print "Success: delete category (%s) and its\
             containing products successful" % (name)
            return True
        else:
            print "Failure: Category (%s) NOT found" % (name)
            return False
    except Exception:
        print "Something did not go right. Contact Admin."
        session.rollback()
        return False


def showProducts(category_id=None):
    if category_id:
        ls = (
            session.query(Product)
            .filter_by(category_id=category_id)
        ).all()
        for i in ls:
            print i.id, i.name
    else:
        ls = session.query(Product).all()
    print "Show MenuItems: Successful"
    return ls


def showProductsByCategoryName(category_name=''):
    category = getCategoryByName(category_name)
    if category:
        ls = (
            session.query(Product)
            .filter_by(category_id=category.id)
        ).all()
    else:
        ls = session.query(Product).all()
    print "Show MenuItems: Successful"
    return ls


def getProductById(id):
    try:
        product = session.query(Product).filter_by(id=id).one()
    except Exception:
        product = None
    return product


def getProductByName(name):
    try:
        product = session.query(Product).filter_by(name=name).one()
    except Exception:
        product = None
    return product


def newProduct(name, description, price, category_id, owner_id):
    '''name description price category_id owner_id'''
    if (not name) or name.strip() == '':
        return None
    new = Product(
        name=name.lower(),
        description=description,
        price=price,
        category_id=category_id,
        owner_id=owner_id
    )
    try:
        session.add(new)
        session.commit()
        print "new product successful"
        return new
    except Exception:
        session.rollback()
        print "new product FAIL"
        return None


def editProduct(product, new_name, new_price, new_description):
    """Rename category, stripped and name must not be empty string
    Keyword Arguments:

    product -- SQLalchemy Mapping Product
    new_name     -- string
    new_price -- string
    new_description -- string
    """
    # edit = session.query(Product).filter_by(id=id)
    if product:
        product.name = new_name
        product.description = new_description
        product.price = new_price
        # edit.category_id = category_id
        # edit.owner_id = owner_id
        # session.add(edit)
        session.commit()
        print "##Edit Product (%s) successful" % new_name
        return True
    else:
        print "##Edit Product (%s) NOT successful" % new_name
        return False


def deleteProduct(product):
    # delete = session.query(Product).filter_by(id=id)
    if product:
        session.delete(product)
        session.commit()
        print "Product Delete successful"
        return True
    else:
        print "Product Delete NOT successful"
        return False


def createUser(username, email, password, picture=''):
    if username and email:
        user = User(username=username, email=email,
                    password=password, picture=picture)
        session.add(user)
        session.commit()
    return user


def getUserByEmail(email):
    try:
        user = session.query(User).filter_by(email=email).one()
        return user
    except Exception:
        return None


# OBSOLETE CODE

# def getUserByID(user_id):
#     user = session.query(User).filter_by(id=user_id).one()
#     return user
