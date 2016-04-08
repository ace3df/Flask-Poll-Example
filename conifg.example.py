import os
basedir = os.path.abspath(os.path.dirname(__file__))

SQLALCHEMY_DATABASE_URI = 'sqlite:///' + os.path.join(basedir, 'my_app.db')
SQLALCHEMY_MIGRATE_REPO = os.path.join(basedir, 'db_repository')

DOMAIN_NAME = "http://example.com/"

WTF_CSRF_ENABLED = True
SECRET_KEY = ''

# https://www.google.com/recaptcha/admin#list
RECAPTCHA_ENABLED = True
RECAPTCHA_SITE_KEY = ""
RECAPTCHA_SECRET_KEY = ""

PORT = 8000
