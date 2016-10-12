
# Change example to your application name
from de_scrape import app

from .models import *

from flask_admin import BaseView, expose
from flask_admin import Admin


from flask import Blueprint, request, render_template, flash, g, session, redirect, url_for
#from flask import Markup

from flask_security import login_required, current_user, roles_required

from .admin_base import SecureBaseView, SecureModelView


de_scrape_admin = Blueprint('de_scrape_admin', __name__, url_prefix='/admin')


# Add admin to running app
admin = Admin(app, name='DE Election Admin', template_mode='bootstrap3')





class UserView(SecureModelView):
    """
    Extends SecureModelView for User model
    """

    can_delete = False

    #edit_modal = True # Puts the edit form in a popup modal

    column_default_sort = ('id', True)
    column_exclude_list = ['email', 'password', 'last_login_at', 'current_login_at', 'last_login_ip', \
        'current_login_ip']
    #form_excluded_columns = ['password']
    column_sortable_list = ['username']
    column_filters = ['username']

    # Form columns order not working??!?
    #form_columns = ['email', 'first_name', 'last_name', 'active', 'roles', 'default_group', 'groups', 'last_login_at', 
    #    'current_login_at', 'last_login_ip', 'current_login_ip', 'login_count']

    form_widget_args = {
        #'email': {
        #    'readonly': True
        #},

    }


class RoleView(SecureModelView):
    """
    Extends SecureModelView for Role model
    """

    can_delete = False
    can_create = False
    can_edit = False

    column_default_sort = ('name', True)
    #column_exclude_list = ['is_active']
    #form_excluded_columns = ['password']
    column_searchable_list = ['name', 'description']
    column_sortable_list = ['name', 'description']
    column_filters = ['name', 'description']

    # Form columns order not working??!?
    #form_columns = ['email', 'first_name', 'last_name', 'active', 'roles', 'default_group', 'groups', 'last_login_at', 
    #    'current_login_at', 'last_login_ip', 'current_login_ip', 'login_count']

    form_widget_args = {
        #'email': {
        #    'readonly': True
        #},

    }



admin.add_view(UserView(User, db.session, category='User', endpoint='user/users'))

admin.add_view(RoleView(Role, db.session, category='User', endpoint='user/roles'))



from campaign_finance.models import DePoliticalDonationCommittee, DePoliticalDonationContributionType
from campaign_finance.models import DePoliticalDonationContributorType, DePoliticalDonationElectionOffice
from campaign_finance.models import DePoliticalDonationFilingPeriod , DePoliticalDonationEmployerName
from campaign_finance.models import DePoliticalDonationEmployerOccupation , DePoliticalDonationContributor
from campaign_finance.models import DePoliticalDonation


from campaign_finance.admin import DePoliticalDonationCommitteeView, DePoliticalDonationContributionTypeView
from campaign_finance.admin import DePoliticalDonationContributorTypeView, DePoliticalDonationElectionOfficeView
from campaign_finance.admin import DePoliticalDonationFilingPeriodView , DePoliticalDonationEmployerNameView
from campaign_finance.admin import DePoliticalDonationEmployerOccupationView , DePoliticalDonationContributorView
from campaign_finance.admin import DePoliticalDonationView


from campaign_finance.admin import CampaignFinanceDownloadsView


admin.add_view(DePoliticalDonationCommitteeView(DePoliticalDonationCommittee, db.session, category='DE Camp. Fin.', endpoint='donation_committee'))

admin.add_view(DePoliticalDonationContributionTypeView(DePoliticalDonationContributionType, db.session, category='DE Camp. Fin.', endpoint='contribution_type'))

admin.add_view(DePoliticalDonationContributorTypeView(DePoliticalDonationContributorType, db.session, category='DE Camp. Fin.', endpoint='contributor_type'))

admin.add_view(DePoliticalDonationElectionOfficeView(DePoliticalDonationElectionOffice, db.session, category='DE Camp. Fin.', endpoint='election_office'))

admin.add_view(DePoliticalDonationFilingPeriodView(DePoliticalDonationFilingPeriod, db.session, category='DE Camp. Fin.', endpoint='filing_period'))

admin.add_view(DePoliticalDonationEmployerNameView(DePoliticalDonationEmployerName, db.session, category='DE Camp. Fin.', endpoint='employer_name'))

admin.add_view(DePoliticalDonationEmployerOccupationView(DePoliticalDonationEmployerOccupation, db.session, category='DE Camp. Fin.', endpoint='employer_occupation'))

admin.add_view(DePoliticalDonationContributorView(DePoliticalDonationContributor, db.session, category='DE Camp. Fin.', endpoint='contributor'))

admin.add_view(DePoliticalDonationView(DePoliticalDonation, db.session, category='DE Camp. Fin.', endpoint='donation'))

admin.add_view(CampaignFinanceDownloadsView(name='Downloads', category='DE Camp. Fin.', endpoint='downloads'))


