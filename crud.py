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
            edit.name = name
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


# TODO: impletment casade delete
def deleteCategoryByName(name):
    """Select category by name, if there is only one, delete it, return bool
    True - for success
    False - for faillure
    """
    delete = session.query(Category).filter_by(name=name)
    try:
        if delete.one():
            delete = delete.one()
            session.delete(delete)
            session.commit()
            print "Success: delete Category (%s) successful" % (name)
            return True
        else:
            print "Failure: Category (%s) NOT found" % (name)
            return False
    except Exception:
        print "rollback?"
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


def showProductById(id):
    menuItem = session.query(Product).filter_by(id=id)
    if any(menuItem):
        menuItem = menuItem.one()
    print "getMenuByID: Successful"
    return menuItem


def newProduct(name, description, price, category_id, owner_id):
    '''name description category_id owner_id'''
    new = Product(
        name=name.lower(),
        description=description,
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


def editProduct(id, name, price, description, category_id, owner_id):
    edit = session.query(Product).filter_by(id=id)
    if any(edit):
        edit = edit.one()
        print edit
        edit.name = name
        edit.description = description
        edit.category_id = category_id
        edit.owner_id = owner_id
        session.add(edit)
        session.commit()
        print "##Edit MenuItem (%s) successful" % id
    else:
        print "##Edit MenuItem (%s) NOT successful" % id


def deleteProduct(id):
    delete = session.query(Product).filter_by(id=id)
    if any(delete):
        session.delete(delete.one())
        session.commit()
        print "delete MenuItem (%s) successful" % id
    else:
        print "delete MenuItem (%s) NOT successful" % id


def createUser(username, email, picture):
    if username and email:
        user = User(username=username, email=email, picture=picture)
        session.add(user)
        session.commit()
    return user


def getUserByEmail(email):
    user = session.query(User).filter_by(email=email)
    if any(user):
        user = user.one()
        return user


def getUserByID(user_id):
    user = session.query(User).filter_by(id=user_id).one()
    return user


# TEST:
# print newRestaurant("123")
# print editRestaurant(3, "456")
# showRestaurants()
