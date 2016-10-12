import os
from flask import Flask, url_for
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager

from sqlalchemy.orm import sessionmaker

from de_scrape.config import *

import logging

app = Flask(__name__, static_url_path='/static')

# Edit database connection below

# https://medium.com/building-socratic/the-one-weird-trick-that-cut-our-flask-page-load-time-by-70-87145335f679
app.jinja_env.cache = {}

config = os.getenv('CONFIG_OBJECT', 'LocalConfig')
#print 'loading config:', config
app.config.from_object(eval(config))

db = SQLAlchemy(app)

lm = LoginManager()
lm.init_app(app)
# oid = OpenID(app, os.path.join(basedir, 'tmp'))
lm.login_view = 'login'




import de_scrape.controllers, de_scrape.models


from campaign_finance.controllers import campaign_finance_blueprint
app.register_blueprint(campaign_finance_blueprint, url_prefix='/campaign_finance')


from de_scrape.admin import de_scrape_admin
app.register_blueprint(de_scrape_admin, url_prefix='/admin')

