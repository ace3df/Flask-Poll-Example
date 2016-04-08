from string import (ascii_uppercase, ascii_lowercase,
                    digits)
import datetime
import random

from slugify import slugify

from flask import (Flask, session)
from flask.ext.sqlalchemy import SQLAlchemy
from flask_recaptcha import ReCaptcha

app = Flask(__name__)
app.config.from_object('config')
recaptcha = ReCaptcha(app=app)


db = SQLAlchemy(app)


def code_generator(size=8,
                   chars=ascii_uppercase + digits + ascii_lowercase):
    return ''.join(random.choice(chars) for _ in range(size))


def generate_csrf_token():
    if '_csrf_token' not in session:
        session['_csrf_token'] = code_generator(size=12)
    return session['_csrf_token']

app.jinja_env.globals['csrf_token'] = generate_csrf_token


import app_poll.views
