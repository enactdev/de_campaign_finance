
import csv
import StringIO

from flask_admin import expose

from flask import request, render_template, flash, g, session, redirect, url_for, send_file

from .models import *

from de_scrape.admin_base import SecureBaseView, SecureModelView




"""


"""

class DePoliticalDonationCommitteeView(SecureModelView):
    """
    Extends SecureModelView for DePoliticalDonationCommittee model
    """

    allowed_roles = ['admin_super']

    can_delete = False

    column_default_sort = ('committee_name')

    column_list = ['committee_name', 'committee_slug', 'number_of_donations', 'number_of_donators', 'donation_total']

    column_sortable_list = ['committee_name', 'committee_slug']
    column_filters = ['committee_name', 'committee_slug']



class DePoliticalDonationContributionTypeView(SecureModelView):
    """
    Extends SecureModelView for DePoliticalDonationContributionType model
    """

    allowed_roles = ['admin_super']

    can_delete = False

    column_default_sort = ('type_name')

    column_list = ['type_name', 'type_slug']

    column_sortable_list = ['type_name', 'type_slug']
    column_filters = ['type_name', 'type_slug']



class DePoliticalDonationContributorTypeView(SecureModelView):
    """
    Extends SecureModelView for DePoliticalDonationContributorType model
    """

    allowed_roles = ['admin_super']

    can_delete = False

    column_default_sort = ('type_name')

    column_list = ['type_name', 'type_slug']

    column_sortable_list = ['type_name', 'type_slug']
    column_filters = ['type_name', 'type_slug']



class DePoliticalDonationElectionOfficeView(SecureModelView):
    """
    Extends SecureModelView for DePoliticalDonationElectionOffice model
    """

    allowed_roles = ['admin_super']

    can_delete = False

    column_default_sort = ('office_name')

    column_list = ['office_name', 'office_area', 'office_district']

    column_sortable_list = ['office_name', 'office_area', 'office_district']
    column_filters = ['office_name', 'office_area', 'office_district']



class DePoliticalDonationFilingPeriodView(SecureModelView):
    """
    Extends SecureModelView for DePoliticalDonationFilingPeriod model
    """

    allowed_roles = ['admin_super']

    can_delete = False

    column_default_sort = ('period_name')

    column_list = ['period_name', 'period_slug']

    column_sortable_list = ['period_name', 'period_slug']
    column_filters = ['period_name', 'period_slug']


class DePoliticalDonationEmployerNameView(SecureModelView):
    """
    Extends SecureModelView for DePoliticalDonationEmployerName model
    """

    allowed_roles = ['admin_super']

    can_delete = False

    column_default_sort = ('employer_name')

    column_list = ['employer_name', 'employer_slug']

    column_sortable_list = ['employer_name', 'employer_slug']
    column_filters = ['employer_name', 'employer_slug']



class DePoliticalDonationEmployerOccupationView(SecureModelView):
    """
    Extends SecureModelView for DePoliticalDonationEmployerOccupation model
    """

    allowed_roles = ['admin_super']

    can_delete = False

    column_default_sort = ('occupation_name')

    column_list = ['occupation_name', 'occupation_slug']

    column_sortable_list = ['occupation_name', 'occupation_slug']
    column_filters = ['occupation_name', 'occupation_slug']



class DePoliticalDonationContributorView(SecureModelView):
    """
    Extends SecureModelView forDePoliticalDonationContributor  model
    """

    allowed_roles = ['admin_super']

    can_delete = False

    column_default_sort = ('name_last')

    column_list = ['name_last', 'name_first', 'city', 'state', 'zipcode']

    column_sortable_list = ['name_last', 'name_first', 'city', 'state', 'zipcode']
    column_filters = ['name_last', 'name_first', 'city', 'state', 'zipcode']



class DePoliticalDonationView(SecureModelView):
    """
    Extends SecureModelView for DePoliticalDonation model
    """

    allowed_roles = ['admin_super']

    can_delete = False

    column_default_sort = ('provided_name')

    column_list = ['provided_name', 'provided_address', 'contributor_id', 'donation_amount']

    column_sortable_list = ['provided_name', 'donation_amount']
    column_filters = ['provided_name', 'donation_amount']




"""

DePoliticalDonationContributor





"""




class CampaignFinanceDownloadsView(SecureBaseView):
    """
    Extends SecureBaseView for downloading things
    """

    allowed_roles = ['admin_super']

    @expose('/')
    def index(self):

        courses = SatCourse.query.order_by(desc(SatCourse.course_start)).all()

        return self.render('admin/sat/registrations.html', courses=courses)

    @expose('/download_reg_csv/<course_id>')
    def download_reg_csv(self, course_id):

        course = SatCourse.query.get(course_id)


        registrations = return_registrations_by_course(course_id)

        #print registrations

        strIO = StringIO.StringIO()
        writer = csv.writer(strIO)

        writer.writerow(['reg_id', 'r.transaction_id', 'r.student_id', 'student.first_name']+\
                ['student.last_name', 'student.grade', 'student.gender', 'r.created_at'])

        for r in registrations:
            student = Student.query.filter(Student.student_id==r.student_id).one()
            writer.writerow([r.id, r.transaction_id, r.student_id, student.first_name,\
                student.last_name, student.grade, student.gender, r.date_registered])

        print 'csv:', strIO.getvalue()

        strIO.seek(0)

        return send_file(strIO,
            mimetype='text/csv',
            attachment_filename='SAT_'+course.name_as_file()+'_registrations.csv',
            as_attachment=True)



"""

class DePoliticalDonationCommitteeView(SecureModelView):


    allowed_roles = ['admin_super']

    can_delete = False

    #edit_modal = True # Puts the edit form in a popup modal


    column_default_sort = ('course_start', True)

    column_list = ['committee_name', 'committee_slug']

    column_sortable_list = ['committee_name', 'committee_slug']
    column_filters = ['committee_name', 'committee_slug']

    # Form columns order not working??!?
    #form_columns = ['email', 'first_name', 'last_name', 'active', 'roles', 'default_group', 'groups', 'last_login_at', 
    #    'current_login_at', 'last_login_ip', 'current_login_ip', 'login_count']

    #form_choices = {
    #    'guest_limit': [ ('0', '0'), ('1', '1'), ('2', '2'), ('3', '3'), ('4', '4'), ('5', '5'), ('6', '6')]
    #}

    form_widget_args = {
        #'email': {
        #    'readonly': True
        #},

    }


"""

