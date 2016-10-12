from flask import g, render_template, session, flash, request, redirect, url_for, Response, send_file, make_response

#from flask_login import login_user, logout_user, current_user, login_required
from flask_security import login_required, current_user, logout_user
from flask_security import Security, SQLAlchemyUserDatastore


from de_scrape import app

from de_scrape import db, forms


import datetime

#from de_scrape.forms import *

from models import *


from sqlalchemy.sql import func

#from werkzeug import secure_filename


# Initialize toolbar
from flask_debugtoolbar import DebugToolbarExtension
toolbar = DebugToolbarExtension(app)


# Setup Flask-Security
user_datastore = SQLAlchemyUserDatastore(db, User, Role)
security = Security(app, user_datastore)





#@app.route('/', methods=['GET', 'POST'])
@app.route('/')
#@login_required
def index():
    """
    Main view.
    """

    return render_template('index.html')



@app.route('/race/<slug>')
#@login_required
def race(slug):
    """
    Race view.
    """

    race = db.session.query(Race).filter(Race.slug==slug).one()

    print 'slug:', race.slug

    rep_candidates = db.session.query(Candidate).filter(Candidate.party_id==1)\
        .filter(Candidate.race_id==race.id).filter(Candidate.is_active==1).order_by(Candidate.order)

    dem_candidates = db.session.query(Candidate).filter(Candidate.party_id==2)\
        .filter(Candidate.race_id==race.id).filter(Candidate.is_active==1).order_by(Candidate.order)

    return render_template('race.html', race=race, rep_candidates=rep_candidates, \
        dem_candidates=dem_candidates)




@app.route('/candidate/<race_slug>/<candidate_slug>')
#@login_required
def candidate(race_slug, candidate_slug):
    """
    Candidate view.
    """

    race = db.session.query(Race).filter(Race.slug==race_slug).one()

    candidate = db.session.query(Candidate).filter(Candidate.slug==candidate_slug).one()


    print 'slug:', candidate.slug

    return render_template('race.html', race=race, candidate=candidate)





@app.route('/contact')
def contact():
    """
    Contact view.
    """

    return render_template('contact.html')





@app.errorhandler(404)
def page_not_found(e):
    """
    Standard 404
    """
    return render_template('404.html', path=app.root_path), 404


@app.errorhandler(500)
def internal_server_error(e):
    """
    Standard 500
    """
    return render_template('500.html'), 500


