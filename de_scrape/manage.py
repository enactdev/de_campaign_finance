#!/usr/bin/env python
# coding: utf-8

"""
Command line interface for de_scrape

From root directory, call:

> python -m de_scrape.manage COMMAND

Such as:

> python -m de_scrape.manage test_print


"""

import datetime

import requests

from bs4 import BeautifulSoup

import re

import csv

import datetime

from flask_script import Manager

from de_scrape import app, db

from de_scrape.models import *

from de_scrape.campaign_finance.models import *

import probablepeople


from standardize_us_address import *


manager = Manager(app)



@manager.command
def test_print():
    """
    Call this function to make sure manage is working
    """
    print "Hello de_scrape! CLI works."




@manager.command
def generate_admin_user():
    """
    Make suere there's an admin user
    """

    # Delete admin user if exists
    try:

        admin_user = User.query.filter(User.username=='admin').one()

        print 'found admin user:', admin_user.id

        db.session.delete(admin_user)

        db.session.commit()


    except Exception as e:

        print 'could not find user, error:', e


     # Add admin role if not exists
    try:

        admin_role = Role.query.filter(Role.name=='admin_super').one()

        print 'found admin_super role:', admin_role.id


    except Exception as e:

        admin_role = Role(name='admin_super', description='Basic super admin role.')
        db.session.add(admin_role)
        db.session.commit()

        print 'added admin role:', admin_role.id



    admin_user = User(username='admin', email='admin', password='adminpass', active=1, \
        last_login_at='0000-00-00 00:00:00', current_login_at='0000-00-00 00:00:00', \
        last_login_ip='', current_login_ip='', login_count=0)

    admin_user.roles=[admin_role]

    db.session.add(admin_user)

    db.session.commit()






def process_de_candidate_table_row(tr):

    """

0 Office
1 County
2 Party
3 Name and Address
4 Phone
5 Date Filed

    """


    text_index = 0
    return_dict = {}
    for td in tr.find_all("td"):
        #print dir(td)

        td_value = td.get_text().strip()

        #print text_index
        #print td_value

        if text_index == 0:
            return_dict['office'] = td_value

        if text_index == 1:
            return_dict['county'] = td_value

        if text_index == 2:
            return_dict['party'] = td_value

        if text_index == 3:
            return_dict['name_addr'] = td_value

        if text_index == 4:
            return_dict['phone'] = td_value

        if text_index == 5:
            return_dict['date_filed'] = td_value

        text_index = text_index + 1

    #print return_dict

    # split name_addr
    name_addr_split = [s.strip() for s in return_dict['name_addr'].splitlines() if s != '']

    #print name_addr_split

    return_dict['full_name'] = name_addr_split.pop(0)
    return_dict['address'] = name_addr_split.pop(0) if len(name_addr_split) else ''
    return_dict['mail_address'] = ''
    return_dict['email'] = ''
    return_dict['url'] = ''

    used_indexes = []

    for i in range(len(name_addr_split)):
        if name_addr_split[i][:5] == 'Email':
            return_dict['email'] = name_addr_split[i][6:]
            used_indexes.append(i)
        if name_addr_split[i][:3] == 'Url':
            return_dict['url'] = name_addr_split[i][4:]  
            used_indexes.append(i)          
        if name_addr_split[i][:7] == 'Mailing':
            i_plus_one = i + 1
            return_dict['mail_address'] = name_addr_split[i_plus_one]
            used_indexes.append(i)
            used_indexes.append(i_plus_one)

    #print used_indexes
    #print range(len(name_addr_split))

    u = set.intersection(set(used_indexes), set(range(len(name_addr_split))))

    #print u

    if len(u) != len(name_addr_split):
        print "ERROR, unused indexes:", u
        print name_addr_split

    return return_dict


def add_cadidate_from_tr_if_not_exist(candidate, date_found, page_found):

    #print candidate

    #if candidate['office'].upper() == 'PRESIDENT':
    #    print "Skipping:", candidate['full_name'], '/', candidate['office']

    if not check_candidate_filing_exists_from_name_office(candidate['full_name'], candidate['office']):

        print "Adding:", candidate['full_name'], '/', candidate['office']

        cf = CandidateFiling()
        cf.candidate_id = 0
        cf.full_name = candidate['full_name']
        cf.office = candidate['office']
        cf.county = candidate['county']
        cf.party = candidate['party']
        cf.address = candidate['address']
        cf.mail_address = candidate['mail_address']
        cf.email = candidate['email']
        cf.url = candidate['url']
        cf.phone = candidate['phone']
        cf.date_filed = datetime.datetime.strptime(candidate['date_filed'], '%m/%d/%Y')
        cf.date_found = date_found
        cf.page_found = page_found

        db.session.add(cf)        



def check_de_filed_candidates(election):


    print 'election:', election

    date_found = datetime.datetime.now()

    if election == 'primary':
        election_url = 'http://elections.delaware.gov/reports/prim_fcddt.shtml'
        page_found = 'primary'

    else:
        election_url = 'http://elections.delaware.gov/reports/genl_fcddt.shtml'
        page_found = 'general'


    r = requests.get(election_url, allow_redirects=False)

    soup = BeautifulSoup(r.content) # r.text ?

    for tr in soup.find_all("tr", class_="dataRowShaded"):
        #print tr
        candidate = process_de_candidate_table_row(tr)
        add_cadidate_from_tr_if_not_exist(candidate, date_found, page_found)


    for tr in soup.find_all("tr", class_="dataRowLight"):
        candidate = process_de_candidate_table_row(tr)
        add_cadidate_from_tr_if_not_exist(candidate, date_found, page_found)


    db.session.commit()




@manager.command
def check_de_filed_candidates_primary():
    """
    Call this function to load new primary candidates
    """

    return check_de_filed_candidates('primary')


@manager.command
def check_de_filed_candidates_general():
    """
    Call this function to load new general candidates
    """

    return check_de_filed_candidates('general')



# This can be run post-primary election to flag those made it to the general
@manager.command
def flag_de_general_candidates():

    election_url = 'http://elections.delaware.gov/reports/genl_fcddt.shtml'

    r = requests.get(election_url, allow_redirects=False)

    soup = BeautifulSoup(r.content) # r.text ?

    for tr in soup.find_all("tr", class_="dataRowShaded"):
        #print tr
        candidate = process_de_candidate_table_row(tr)

        db_candidate = return_candidate_filing_from_name_office(candidate['full_name'], candidate['office'])

        db_candidate.in_general = 1;

        #db.session.add(db_candidate)


    for tr in soup.find_all("tr", class_="dataRowLight"):
        candidate = process_de_candidate_table_row(tr)

        db_candidate = return_candidate_filing_from_name_office(candidate['full_name'], candidate['office'])

        db_candidate.in_general = 1;

        #db.session.add(db_candidate)


    db.session.commit()




# This can be run post-primary election to flag those made it to the general
@manager.command
def generate_street_suffix_abbr_dict():

    #url = 'http://pe.usps.gov/text/pub28/28apc_002.htm'

    #r = requests.get(url, allow_redirects=False)

    # Can't read URL with beautiful soup, use local copy

    html_file = '/path/to/file/from/usps_table_content.html'

    f = open(html_file, 'r')

    soup = BeautifulSoup(f.read()) # r.text ?

    tables = soup.find_all("table", id="ep533076")

    #print tables

    #print dir(tables)

    current_entry = ''

    replacement_dict = {}

    # Skip header row
    for tr in tables[0].find_all("tr")[1:]:

        tds = tr.find_all('td')

        #print len(tds)


        # If len is 3 then this is a new entry
        if len(tds) == 3:
            current_entry = tds[2].get_text().strip()
            replacement_dict[tds[1].get_text().strip()] = current_entry

        else:
            replacement_dict[tds[0].get_text().strip()] = current_entry


    print replacement_dict












@manager.command
def store_delinquent_taxpayers():
    """
    Call this function to store delinquent taxpayers

SELECT d.`id`, d.`release_date`, d.`name`, c.name_first, c.name_last, d.`amount`, d.address, count(*) 
FROM `delinquent_taxpayers` d, de_political_donation_contributor c
WHERE d.name like concat('%',c.name_first,'%')
AND d.name like concat('%',c.name_last,'%')
and c.name_first != '' and c.name_last != ''
and length(c.name_first) > 2
GROUP BY d.id
ORDER BY count(*)  DESC
    
    """

    file_location = app.config['CONTRIBUTION_CSV_DIRECTORY']+'de_delinquent_tax_payers.txt'

    fhand = open(file_location)

    delinquent_count = 0
    delinquent_line_count = 0

    delinquent_info = {}


    for line in fhand:

        delinquent_line_count = delinquent_line_count + 1 

        #print delinquent_line_count, line

        line = line.strip()

        if delinquent_line_count == 1:
            delinquent_info = {}          
            delinquent_info['name'] = line

        if delinquent_line_count == 2:
            delinquent_info['amount'] = ''.join(re.findall('([0-9])', line))

        if delinquent_line_count == 3:
            pass

        if delinquent_line_count == 4:
            delinquent_info['address'] = line

        if delinquent_line_count == 5:
            delinquent_info['city'] = line

        if delinquent_line_count == 6:
            delinquent_info['state'] = line

        if delinquent_line_count == 7:
            delinquent_info['zipcode'] = line[:5]

            #print delinquent_info
            delinquent_count = delinquent_count + 1
            delinquent_line_count = 0

            delinquent = DelinquentTaxpayer(release_date = datetime.datetime.now(), **delinquent_info)
            """
            delinquent.release_date = datetime.datetime.now()
            delinquent.name = delinquent_info['name']
            delinquent.amount = delinquent_info['amount']
            delinquent.address = delinquent_info['address']
            delinquent.city = delinquent_info['city']
            delinquent.state = delinquent_info['state']
            delinquent.zipcode = delinquent_info['zipcode']
            """



            db.session.add(delinquent)

    db.session.commit()

    print 'Delinquent Count:', delinquent_count
    



def process_campaign_contribution_row(contribution):

    address_split = contribution[2].split(',')

    print address_split


"""
address_abbreviation_list = {'Alley': 'Aly', 'Arcade': 'Arc', 'Avenue': 'Ave', \
'Boulevard': 'Blvd', 'Branch': 'Br', 'Bypass': 'Byp', 'Causeway': 'Cswy', \
'Center': 'Ctr', 'Circle': 'Cir', 'Court': 'Ct', 'Crescent': 'Cres', 'Drive': 'Dr', \
'Expressway': 'Expy', 'Extension': 'Ext', 'Freeway': 'Fwy', 'Gardens': 'Gdns', \
'Grove': 'Grv', 'Heights': 'Hts', 'Highway': 'Hwy', 'Lane': 'Ln', 'Manor': 'Mnr', \
'Place': 'Pl', 'Plaza': 'Plz', 'Point': 'Pt', 'Road': 'Rd', 'Route': 'Rte', \
'Rural': 'R', 'Square': 'Sq', 'Street': 'St', 'Terrace': 'Ter', 'Trail': 'Trl', \
'Turnpike': 'Tpke', 'Viaduct': 'Via', 'Vista': 'Vis', 
"""


address_abbreviations = ['ST', 'AVE', 'BLVD', 'CIR', 'CT', 'DR', 'LN', 'LOOP', \
    'PL', 'PLZ', 'RD', 'RTE', 'SQ', 'TER', 'LANDING']

abbr_replacements = {'Avenue': 'Ave', 'Boulevard': 'Blvd', 'Circle': 'Cir', 'Court': 'Ct', \
        'Drive': 'Dr', 'Lane': 'Ln', 'Place': 'Pl', 'Plaza': 'Plz', 'Road': 'Rd', 'Route': 'Rte', \
        'Square': 'Sq', 'Street': 'St', 'Terrace': 'Ter'}



def replace_with_road_abbreviations(address):
    address = address.strip()

    len_address = len(address)

    # In case unchanged
    return_address = address

    new_abbr_replacements = {}

    for addr_road in abbr_replacements:
        new_abbr_replacements[addr_road.upper()] = abbr_replacements[addr_road].upper()

    if address in new_abbr_replacements:
        return new_abbr_replacements[address]
        
        
    for addr_road in new_abbr_replacements:

        addr = addr_road.upper()
        len_addr = len(addr)
        abbr = new_abbr_replacements[addr_road]

        if address.find(' '+addr+' ') > 0:
            return_address = address.replace(' '+addr+' ', ' '+abbr+' ')
            #print 'in mid: replacing', addr, 'with', abbr
        elif address[len_address-len_addr:] == addr:
            return_address = address[:len_address-len_addr].strip() + ' ' + abbr
            #print 'at end: replacing', addr, 'with', abbr

    return return_address





# These replacements are made before tokenizing address
address_pre_token_replacement_dict = dict()
address_pre_token_replacement_dict[' DE, DE'] = ' DE'
address_pre_token_replacement_dict[' DC, DC'] = ' DC'
address_pre_token_replacement_dict[' GA, GA'] = ' GA'
address_pre_token_replacement_dict[' CT, CT'] = ' CT'
address_pre_token_replacement_dict[' FL, FL'] = ' FL'
address_pre_token_replacement_dict[' MD, MD'] = ' MD'
address_pre_token_replacement_dict[' IL, IL'] = ' IL'
address_pre_token_replacement_dict['D.C., DE'] = 'DC,'

address_pre_token_replacement_dict['WILMINGTON, WILMINGTON'] = 'WILMINGTON'
address_pre_token_replacement_dict['NEWARK, NEWARK'] = 'NEWARK'
address_pre_token_replacement_dict['DOVER, DOVER'] = 'DOVER'
address_pre_token_replacement_dict['SEAFORD, SEAFORD'] = 'SEAFORD'
address_pre_token_replacement_dict['LEWES, LEWES'] = 'LEWES'
address_pre_token_replacement_dict['HOCKESSIN, HOCKESSIN'] = 'HOCKESSIN'
address_pre_token_replacement_dict['MILFORD, MILFORD'] = 'MILFORD'
address_pre_token_replacement_dict['BEACH, BEACH'] = 'BEACH'
address_pre_token_replacement_dict['REHOBOTH, REHOBOTH'] = 'REHOBOTH'

#address_pre_token_replacement_dict[''] = ''




@manager.command
def print_upper_dict():
    upper_dict = dict()

    for i in usps_unit_designators:
        upper_dict[i.upper()] = usps_unit_designators[i].upper()

    print usps_unit_designators


@manager.command
def load_testing_us_address_library():

    #for year in range(2008, 2017):
    for year in range(2015, 2017):
        testing_us_address_library(year)



"""
VERY BAD:
SELECT * FROM `test_us_address_cleaner` WHERE `AddressNumber` != '' and `original_address` not like concat(`AddressNumber`, '%') 


SELECT * FROM `test_us_address_cleaner` WHERE `StateName` = '') 


"""


def testing_us_address_library(year):

    file_location = app.config['CONTRIBUTION_CSV_DIRECTORY']+'DE_Contributions_'+str(year)+'.csv'

    line = 0

    csvfile = open(file_location, 'r')

    csvreader = csv.reader(csvfile)

    de_election_db_cache = DeElectionDBCache()
    de_election_db_cache.load_cache()


    row = next(csvreader)   # skip the first line

    city_list = []

    for row in csvreader:

        donation_date_obj = datetime.datetime.strptime(row[0], '%m/%d/%Y')


        #print 'original name:', row[1]

        mailing_address = row[2].upper().replace('  ',', ')

        # Will want to clean up address before using. Check where NotAddress field is set!
        for r in address_pre_token_replacement_dict:
            mailing_address = mailing_address.replace(r, address_pre_token_replacement_dict[r])


        try:

            #usaddress_address = usaddress.tag(mailing_address)

            address_dict = standardize_us_address(mailing_address)


            print 'usaddress addy dict:', address_dict

            new_addy = TestUsAddressCleaner(**address_dict)

            db.session.add(new_addy)

            if 'AddressNumber' not in address_dict:
                if 'PlaceName' in address_dict and address_dict['PlaceName'][0].isdigit():
                    # Get number in front of PlaceName
                    pass


                else:
                    print 'ERROR: Bad address:', mailing_address


        except Exception as e:

            print 'usaddress ERROR:'
            print e

            # Ugh, everything below needs to be within the try statement!



    db.session.commit()







def clean_name(full_name):


    """
    This function takes an text address (street address, city, state, zip), tokenizes it with the usaddress library,
    and runs basic search and replace to help standardize the address

    """


    try:


        original_name = full_name.upper().replace('  ',', ')


        # Make edits to original_name before calling probablepeople



        probablepeople_name = probablepeople.tag(original_name)



        #print 'probable name:', probablepeople_name

        name_dict = dict(probablepeople_name[0])

        name_type = probablepeople_name[1]

        name_dict['name_type'] = name_type

        name_dict['original_name'] = original_name

        # Remove trailing '.' from any abbreviations
        for field in people_fields_to_strip_periods:
            if field in name_dict:
                name_dict[field] = name_dict[field].strip('.')


        #print 'probable name dict:', name_dict

        return name_dict


    except Exception as e:

        print 'probablepeople ERROR:'
        print e

        return e



@manager.command
def load_testing_probable_people_library():
    for year in range(2015, 2017):
        testing_probable_people_library(year)





people_fields_to_strip_periods = ['FirstInitial', 'MiddleInitial', 'LastInitial', 'SuffixGenerational', 'SuffixOther', \
    'SecondFirstInitial', 'SecondMiddleInitial', 'SecondLastInitial', 'SecondSuffixGenerational', 'SecondSuffixOther', \
    'CorporationLegalType', 'SecondCorporationLegalType']



def testing_probable_people_library(year):

    file_location = app.config['CONTRIBUTION_CSV_DIRECTORY']+'DE_Contributions_'+str(year)+'.csv'

    line = 0

    csvfile = open(file_location, 'r')

    csvreader = csv.reader(csvfile)

    de_election_db_cache = DeElectionDBCache()
    de_election_db_cache.load_cache()


    row = next(csvreader)   # skip the first line

    city_list = []

    for row in csvreader:

        donation_date_obj = datetime.datetime.strptime(row[0], '%m/%d/%Y')


        try:

            name_dict = clean_name(row[1])

            test_probable_name = TestProbablePeopleCleaner(**name_dict)

            db.session.add(test_probable_name)    


        except Exception as e:

            print 'probablepeople ERROR:'
            print e



    db.session.commit()










suffix_list = ['JR', 'SR', 'II', 'III', 'IV', 'V', 'VI', 'VII', 'TTEE', 'PA', '2ND', '3RD', 'CFSP', \
    'ESQ', 'CPA', 'JD', 'MD', 'PHD', 'MR', 'DMD', 'DDS']

prefix_list = ['MR', 'MS', 'DR', 'MRS', 'LT COL', 'LT', 'COL', 'HONORABLE', 'HON']



# amount_list is used to clean the amount
amount_list = list('1234567890.$,-')


@manager.command
def store_all_campaign_contributions_csv():
    for y in range(2015, 2017):
        store_campaign_contributions_csv(y)


"""
TRUNCATE `de_political_donation`;
TRUNCATE `de_political_donation_contributor`;
TRUNCATE `de_political_donation_contributor_address`;
"""



@manager.command
def store_campaign_contributions_csv(year=2015):
    """
    Call this function to all campaign contributions

Contribution Date
Contributor Name
Contributor Address
Contributor Type
Employer Name
Employer Occupation
Contribution Type
Contribution Amount
Receiving Committee
Filing Period
Office
FixedAsset


    """

    

    file_location = app.config['CONTRIBUTION_CSV_DIRECTORY']+'DE_Contributions_'+str(year)+'.csv'
    #file_location = app.config['CONTRIBUTION_CSV_DIRECTORY']+'DE_Contributions_2015_partial.csv'

    total_contributed = 0



    """ 

    For names, cycle through the suffix and prefixes, looking for matches surrounded by a space or begin/end of line
    Set prefix/suffix and remove preceding space, unless at beginning of line, in which case remove next space

    ALT: Split on double space (would be a comma)
    go through two splits, like above
    Then go through, looking for single letter, set as middle initial if exists


    """

    line = 0

    csvfile = open(file_location, 'r')

    csvreader = csv.reader(csvfile)

    de_election_db_cache = DeElectionDBCache()
    de_election_db_cache.load_cache()


    row = next(csvreader)   # skip the first line

    city_list = []

    for row in csvreader:

        line = line + 1        

        #print len(row)
        #print(row)

        for i in range(len(row)):
            row[i] = row[i].strip()



        # Look for weird characters in amounts
        received_list = list(row[7])

        extra_chars = [c for c in received_list if c not in amount_list] 

        if len(extra_chars):
            print 'year:', year, 'line:',line,': ERROR: extra chars in amount:', ''.join(extra_chars)

        donation_amount = ''.join(re.findall('([0-9\.-])', row[7]))

        #print 'donation:', donation_amount

        # Convert first column to datetime
        donation_date_obj = datetime.datetime.strptime(row[0], '%m/%d/%Y')
        #print donation_date_obj


        #committee_id = return_donation_commitee_id_from_name(row[8])
        committee_id = de_election_db_cache.return_donation_commitee_id_from_name(row[8])

        #contribution_type_id = return_contribution_type_id_from_name(row[6])
        contribution_type_id = de_election_db_cache.return_contribution_type_id_from_name(row[6])

        #contributor_type_id = return_contributor_type_id_from_name(row[3])
        contributor_type_id = de_election_db_cache.return_contributor_type_id_from_name(row[3])

        #filing_period_id = return_filing_period_id_from_name(row[9])
        filing_period_id = de_election_db_cache.return_filing_period_id_from_name(row[9])


        employer_name_id = 0
        if row[4] != '':
            employer_name_id = de_election_db_cache.return_employer_name_id_from_name(row[4])

        employer_occupation_id = 0
        if row[5] != '':
            employer_occupation_id = de_election_db_cache.return_employer_occupation_id_from_name(row[5])






        election_district = ''
        election_office = ''

        if row[11] != '':
            election_race_split = row[10].split('(')

            if len(election_race_split) == 1:
                election_district = 0
                election_office = election_race_split[0].strip().strip(')')

            elif len(election_race_split) == 2:
                election_district = election_race_split[0].replace('District ', '').replace('At large', '').strip()
                election_office = election_race_split[1].strip().strip(')')

        office_id = 0
        if election_office != '':
            office_id = de_election_db_cache.return_office_id_from_name_and_district(election_office, election_district)

        #print 'cateogry:', election_office
        #print 'district:', election_district

        #if row[11] != 'No':
        #    print row[11]

        is_fixed_asset = 1 if row[11] == 'Yes' else 0

        if len(str(election_district)) > 2:
            print 'ERROR, line',line,'district too long'
            print 'office:', election_office
            print 'district:', election_district






        # 'Total of Contributions not exceeding $100'
        is_annonymous = 0
        contributor_id = 0
        contributor_address_id = 0

        if row[1] == 'Total of Contributions not exceeding $100':
            #contributor_id = 0
            is_annonymous = 1

        else:

            full_name = ''

            bad_name = False
            bad_addy = False


            name_dict = clean_name(row[1])


            if type(name_dict) is not dict:

                print 'name ERROR:'
                bad_name = True

            mailing_address = row[2].upper().replace('  ',', ')

            # Will want to clean up address before using. Check where NotAddress field is set!
            for r in address_pre_token_replacement_dict:
                mailing_address = mailing_address.replace(r, address_pre_token_replacement_dict[r])



            address_dict = standardize_us_address(mailing_address)


            if type(address_dict) is not dict:

                print 'addy ERROR:'
                bad_addy = True


            # Make sure there is a space between street number and street
            #sn_search = re.search('^([0-9]*)', addr1)
            #street_num = addr1[:sn_search.end()]
            #addr_rest = addr1[sn_search.end():]
            #addr1 = street_num+' '+addr_rest.strip()

            #print 'address dict:', address_dict
            #print 'type:', type(address_dict)
            #print 'bad addy:', bad_addy

            ensure_address_fields_list = ['PlaceName', 'StateName', 'ZipCode']

            for field in ensure_address_fields_list:
                if not bad_addy and field not in address_dict:
                    address_dict[field] = ''


            if bad_addy or address_dict['address_type'] in ['Ambiguous', 'Intersection']:

                contributor_address_id = 0

            elif address_dict['address_type'] == 'PO Box':

                # Get address
                try:

                    contributor_address = DePoliticalDonationContributorAddress.query\
                        .filter(DePoliticalDonationContributorAddress.address_type == 'PO Box')\
                        .filter(DePoliticalDonationContributorAddress.po_box == address_dict['USPSBoxID'])\
                        .filter(DePoliticalDonationContributorAddress.zipcode == address_dict['ZipCode'])\
                        .one()

                except Exception as e:


                    contributor_address = DePoliticalDonationContributorAddress()
                    contributor_address.address_type = address_dict['address_type']

                    contributor_address.po_box = address_dict['USPSBoxID']
                    contributor_address.city = address_dict['PlaceName']
                    contributor_address.state = address_dict['StateName']
                    contributor_address.zipcode = address_dict['ZipCode']

                    db.session.add(contributor_address)        
                    db.session.commit()

                contributor_address_id = contributor_address.id

            else: # Should be a normal address

                addr1 = ''

                addr_build_list = ['AddressNumber', 'AddressNumberSuffix', 'StreetNamePreDirectional', 'StreetName', \
                    'StreetNamePostType', 'StreetNamePostDirectional']

                for field in addr_build_list:

                    if field in address_dict:
                        addr1 = addr1+' '+address_dict[field]

                addr1 = addr1.strip()


                # Get address
                try:

                    contributor_address = DePoliticalDonationContributorAddress.query\
                        .filter(DePoliticalDonationContributorAddress.address_type == 'Street Address')\
                        .filter(DePoliticalDonationContributorAddress.addr1 == addr1)\
                        .filter(DePoliticalDonationContributorAddress.zipcode == address_dict['ZipCode'])\
                        .one()

                except Exception as e:


                    contributor_address = DePoliticalDonationContributorAddress()
                    contributor_address.address_type = address_dict['address_type']

                    contributor_address.addr1 = addr1
                    contributor_address.city = address_dict['PlaceName']
                    contributor_address.state = address_dict['StateName']
                    contributor_address.zipcode = address_dict['ZipCode']

                    db.session.add(contributor_address)        
                    db.session.commit()

                contributor_address_id = contributor_address.id


            is_person = 0
            is_business = 0

            name_prefix = ''
            name_first = ''
            name_middle = ''
            name_last = ''
            name_suffix = ''




            # Only split out name for individuals, 
            if not bad_name and 'name_type' in name_dict and name_dict['name_type'] in ['Person', 'Household']:

                is_person = 1

                if 'PrefixMarital' in name_dict: 
                    name_prefix = name_dict['PrefixMarital']
                elif 'PrefixOther' in name_dict:
                    name_prefix = name_dict['PrefixOther']

                if 'GivenName' in name_dict: 
                    name_first = name_dict['GivenName']
                elif 'FirstInitial' in name_dict:
                    name_first = name_dict['FirstInitial']

                if 'MiddleName' in name_dict: 
                    name_middle = name_dict['MiddleName']
                elif 'MiddleInitial' in name_dict:
                    name_middle = name_dict['MiddleInitial']

                if 'Surname' in name_dict: 
                    name_last = name_dict['Surname']
                elif 'LastInitial' in name_dict:
                    name_last = name_dict['LastInitial']

                if 'SuffixGenerational' in name_dict: 
                    name_suffix = name_dict['SuffixGenerational']
                elif 'SuffixOther' in name_dict:
                    name_suffix = name_dict['SuffixOther']



                # Check if contributor already exists from first,last,suffix,addr1,zipcode
                try:

                    contributor = DePoliticalDonationContributor.query\
                        .filter(DePoliticalDonationContributor.address_id == contributor_address_id)\
                        .filter(DePoliticalDonationContributor.name_first == name_first)\
                        .filter(DePoliticalDonationContributor.name_last == name_last)\
                        .filter(DePoliticalDonationContributor.name_suffix == name_suffix)\
                        .one()

                except Exception as e:


                    contributor = DePoliticalDonationContributor()
                    contributor.address_id = contributor_address_id
                    contributor.name_prefix = name_prefix
                    contributor.name_first = name_first
                    contributor.name_middle = name_middle
                    contributor.name_last = name_last
                    contributor.name_suffix = name_suffix
                    contributor.name_business = ''

                    contributor.is_person = is_person
                    contributor.is_business = is_business

                    db.session.add(contributor)        
                    db.session.commit()

                contributor_id = contributor.id

            # Don't store individual names
            elif not bad_name and 'name_type' in name_dict and  name_dict['name_type'] == 'Corporation':

                is_business = 1

                if 'CorporationName' in name_dict:
                    corporation = name_dict['CorporationName']

                else:
                    corporation = name_dict['ShortForm']

                # Check if contributor already exists from full_name,addr1,zipcode
                try:

                    contributor = DePoliticalDonationContributor.query\
                        .filter(DePoliticalDonationContributor.address_id == contributor_address_id)\
                        .filter(DePoliticalDonationContributor.name_business == corporation)\
                        .one()

                except Exception as e:

                    contributor = DePoliticalDonationContributor()
                    contributor.address_id = contributor_address_id
                    contributor.name_business = corporation

                    contributor.is_person = is_person
                    contributor.is_business = is_business

                    db.session.add(contributor)        
                    db.session.commit()

                contributor_id = contributor.id


            else:

                contributor_id = 0



        # Store all donations, including multiple annonymous (under $100) and unknown (badly formed people, address)
        if True:

            donation = DePoliticalDonation()
            donation.is_annonymous = is_annonymous
            donation.contributor_id = contributor_id
            donation.contributor_type_id = contributor_type_id
            donation.contribution_type_id = contribution_type_id
            donation.committee_id = committee_id
            donation.filing_period_id = filing_period_id
            donation.employer_name_id = employer_name_id
            donation.employer_occupation_id = employer_occupation_id

            donation.donation_date = donation_date_obj 
            donation.donation_amount = donation_amount
            donation.provided_name = row[1]
            donation.provided_address = row[2]
            donation.is_fixed_asset = is_fixed_asset

            db.session.add(donation)        
            db.session.commit()

        """
        # Check if donation already exists from contributor_id, committee_id, donation_date, donation_amount
        try:

            donation = DePoliticalDonation.query\
                .filter(DePoliticalDonation.contributor_id == contributor_id)\
                .filter(DePoliticalDonation.committee_id == committee_id)\
                .filter(DePoliticalDonation.donation_date == donation_date_obj)\
                .filter(DePoliticalDonation.donation_amount == donation_amount)\
                .one()

        except Exception as e:

            donation = DePoliticalDonation()
            donation.is_annonymous = is_annonymous
            donation.contributor_id = contributor_id
            donation.contributor_type_id = contributor_type_id
            donation.contribution_type_id = contribution_type_id
            donation.committee_id = committee_id
            donation.filing_period_id = filing_period_id
            donation.employer_name_id = employer_name_id
            donation.employer_occupation_id = employer_occupation_id

            donation.donation_date = donation_date_obj 
            donation.donation_amount = donation_amount
            donation.provided_name = row[1]
            donation.provided_address = row[2]
            donation.is_fixed_asset = is_fixed_asset

            db.session.add(donation)        
            db.session.commit()

        """


        total_contributed = total_contributed + float(donation_amount)

    #print city_list

    print 'total contributed:', total_contributed








if __name__ == "__main__":
    manager.run()