# -*- coding: utf-8 -*-
# This code originates in the flask-saml-okta project
# https://github.com/WPMedia/flask-saml-okta
from flask import Flask, Blueprint, request, render_template, flash, g, session, redirect, url_for, Response

from flask_security import login_required, current_user, logout_user

from flask_login import login_user

from .models import *

from .forms import *

# Change example to your application name
from de_scrape import app, db

import datetime


campaign_finance_blueprint = Blueprint('campaign_finance_blueprint', __name__)




@campaign_finance_blueprint.route("/")
def index():
    """
    Campaign finance index. 
    """



    return render_template('campaign_finance/index.html')


