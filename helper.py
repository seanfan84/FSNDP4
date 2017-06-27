import random
import string
import hashlib
import re


# registration
def make_salt():
    return ''.join(random.choice(string.letters) for i in range(5))


def make_pw_hash(email, pw):
    salt = make_salt()
    h = hashlib.sha256(email + pw + salt).hexdigest()
    return '%s,%s' % (h, salt)


def valid_pw(email, pw, h):
    if h.split(",")[0] ==  \
            hashlib.sha256(email + pw + h.split(",")[1]).hexdigest():
        return True
    else:
        return False


# Input Verification
USER_RE = re.compile(r"^[a-zA-Z0-9_-]{3,20}$")


def valid_username(username):
    return username and USER_RE.match(username)


PASS_RE = re.compile(r"^.{8,20}$")


def valid_password(password):
    return password and PASS_RE.match(password)


EMAIL_RE = re.compile(r"^[\S]+@[\S]+.[\S]+$")


def valid_email(email):
    return not email or EMAIL_RE.match(email)
