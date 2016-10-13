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

import usaddress
import probablepeople


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




@manager.command
def store_all_campaign_contributions_csv():
    for y in range(2003, 2016):
        store_campaign_contributions_csv(y)





state_replacement_dict = {s.state: s.abbreviation for s in State.query}

street_type_replacement_dict = {'Lane': 'Ln', 'Road': 'Rd', 'Street': 'St', 'Avenue': 'Ave', 'Drive': 'Dr'}


street_direction_replacement_dict = {'North': 'N', 'South': 'S', 'East': 'E', 'West': 'W'}


@manager.command
def testing_us_address_library():

    file_location = app.config['CONTRIBUTION_CSV_DIRECTORY']+'DE_Contributions_2015_partial.csv'

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



        probablepeople_name = probablepeople.tag(row[1].replace('  ',', '))

        print 'probable name:', probablepeople_name

        name_dict = dict(probablepeople_name[0])

        name_type = probablepeople_name[1]

        print 'probable name dict:', name_dict


        #print 'original addy:', row[2]



        usaddress_address = usaddress.tag(row[2].replace('  ',', '))

        print 'usaddress addy:', usaddress_address

        address_dict = dict(usaddress_address[0])

        address_type = usaddress_address[1]

        # Make sure we're using state abbreviation instead of full state name
        if 'StateName' in address_dict and address_dict['StateName'] in state_replacement_dict:
            address_dict['StateName'] = state_replacement_dict[address_dict['StateName']]


        # Use standard abbreviated for street type (Rd instead of Road), and remove trailing '.' from any abbreviations
        if 'StreetNamePostType' in address_dict:
            if address_dict['StreetNamePostType'] in street_type_replacement_dict:
                address_dict['StreetNamePostType'] = street_type_replacement_dict[address_dict['StreetNamePostType']]

            address_dict['StreetNamePostType'] = address_dict['StreetNamePostType'].strip('.')


        # Use standard abbreviated for street direction (N instead of North), and remove trailing '.' from any abbreviations
        if 'StreetNamePreDirectional' in address_dict:
            if address_dict['StreetNamePreDirectional'] in street_direction_replacement_dict:
                address_dict['StreetNamePreDirectional'] = street_direction_replacement_dict[address_dict['StreetNamePreDirectional']]

            address_dict['StreetNamePreDirectional'] = address_dict['StreetNamePreDirectional'].strip('.')




        # Remove trailing '-' from zipcode
        address_dict['ZipCode'] = address_dict['ZipCode'].strip('-')





        print 'usaddress addy dict:', address_dict

        test_addy = TestUsAddressCleaner(**address_dict)

        db.session.add(test_addy)        


        if 'AddressNumber' not in address_dict:
            if address_dict['PlaceName'][0].isdigit():
                # Get number in front of PlaceName
                pass


            else:
                print 'ERROR: Bad address:', row[2]

    db.session.commit()








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

    

    #file_location = app.config['CONTRIBUTION_CSV_DIRECTORY']+'DE_Contributions_'+str(year)+'.csv'
    file_location = app.config['CONTRIBUTION_CSV_DIRECTORY']+'DE_Contributions_2015_partial.csv'

    total_contributed = 0

    amount_list = list('1234567890.$,-')



    suffix_list = ['JR', 'SR', 'II', 'III', 'IV', 'V', 'VI', 'VII', 'TTEE', 'PA', '2ND', '3RD', 'CFSP', \
        'ESQ', 'CPA', 'JD', 'MD', 'PHD', 'MR', 'DMD', 'DDS']

    prefix_list = ['MR', 'MS', 'DR', 'MRS', 'LT COL', 'LT', 'COL', 'HONORABLE', 'HON']

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

        for i in range(len(row)):
            row[i] = row[i].strip()

        full_name = ''

        # remove double spaces from name
        raw_name = row[1].replace('  ', ' ').replace('  ', ' ').replace('  ', ' ').replace('  ', ' ').replace('  ', ' ').replace('  ', ' ')

        # remove non-alpha chars, and upper case it
        raw_name = ''.join(re.findall('([0-9A-Z -])', raw_name.upper())).replace('  ', ' ')

        if raw_name == 'Anonymous'.upper() or raw_name == '' or raw_name in ['0', '00', '000', '0000', '00000']:
            continue

        # remove double spaces and non-alpha chars, or single space, and upper it
        #full_name = row[1].replace('.', '').replace('  ', ' ').replace('  ', ' ').strip()
        #full_name = ''.join(re.findall('([0-9a-zA-z -])', row[1].replace('  ', ' ').upper())).replace('  ', ' ').replace('  ', ' ')


        # Look for weird characters in amounts
        received_list = list(row[7])

        extra_chars = [c for c in received_list if c not in amount_list] 

        if len(extra_chars):
            print 'line',line,': ERROR: extra chars in amount:', ''.join(extra_chars)

        donation_amount = ''.join(re.findall('([0-9\.-])', row[7]))

        #print 'donation:', donation_amount

        # Convert first column to datetime
        donation_date_obj = datetime.datetime.strptime(row[0], '%m/%d/%Y')
        #print donation_date_obj



        # Check employeers
        #if row[4] != '':
        #    print row[4]

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


        zipcode = ''
        state = ''
        city = ''
        addr1 = ''
        addr2 = ''
        addr3 = ''

        full_address = row[2].replace('--', '  ').replace(';', ' ').replace('.', ' ').upper()

        address_split = full_address.split('  ')

        address_split = [l.strip() for l in address_split if l.strip() != '']


        #print 'len address split is:', len(address_split)
        #print address_split

        if len(address_split) > 2:


            city_state = address_split.pop()

            city_state_split = city_state.split(' ')

            if len(city_state_split) == 0:
                print 'line',line,': ERROR: length of city_state_split is: 0'
                print city_state_split

                zipcode = ''
                state = ''

            elif len(city_state_split) == 1:
                #print 'ERROR, line',line,' length of city_state_split is: 1'
                #print city_state_split

                zipcode = ''
                state = city_state_split.pop().strip()

            else:

                zipcode = ''.join(re.findall('([0-9])', city_state_split.pop()))

                state = city_state_split.pop().strip()

            city = address_split.pop()


            if len(address_split) == 3:
                addr1 = address_split[0]
                addr2 = address_split[1]
                addr3 = address_split[2]

            elif len(address_split) == 2:
                addr1 = address_split[0]
                addr2 = address_split[1]

            elif len(address_split) == 1:
                addr1 = address_split[0]

            else:
                #print 'line',line,': ERROR: counldnt figure out address'
                #print 'line',line,': c, s, z:',city, state, zipcode
                #print 'line',line,': rest:', address_split
                addr1 = ' '.join(address_split)

        elif len(address_split) <= 2:
            print 'line',line,'address <= 2:'
            print address_split

            unknown = ''

            if len(address_split) == 2:
                # Get last element
                last_element = address_split.pop()

                last_element_split = last_element.split(' ')

                # Only look for zipcode and state in last_element
                while (len(last_element_split)):

                    check_element = last_element_split.pop()

                    if len(check_element) == 2 and de_election_db_cache.return_state_id_from_name(check_element) > 0:
                        state = check_element

                    elif len(check_element) >= 5 and check_element[:5] == ''.join(re.findall('([0-9])', check_element[:5])):
                        zipcode = check_element[:5]

                #print 'in last element, s, z:', state, zipcode

            # Go through first (remaining) element
            first_element = address_split.pop()

            found_state_in_first_element = False

            new_first_element = first_element

            first_element_split = first_element.split(' ')

            #print 'checking:', first_element_split

            # Cycle through, try to find state and zipcode

            for check_element in first_element_split:

                if len(check_element) == 2 and de_election_db_cache.return_state_id_from_name(check_element) > 0:
                    state = check_element
                    found_state_in_first_element = True
                    new_first_element = new_first_element.replace(state, '').strip().replace('  ', ' ').replace('  ', ' ')

                elif len(check_element) >= 5 and check_element[:5] == ''.join(re.findall('([0-9])', check_element[:5])):
                    zipcode = check_element[:5]
                    new_first_element = new_first_element.replace(check_element, '').strip().replace('  ', ' ').replace('  ', ' ')


            # if we found state in first element, assume preceding is city
            if found_state_in_first_element:

                new_first_element_split = new_first_element.split(' ')
                new_first_element_split = [l.strip() for l in new_first_element_split if l.strip() != '']

                if len(new_first_element_split):
                    city = new_first_element_split.pop()

                new_first_element = ' '.join(new_first_element_split).replace('  ', ' ').replace('  ', ' ')

            addr1 = new_first_element.replace('  ', ' ').replace('  ', ' ')

            #print 'in first element, c, s, z, a:', city, state, zipcode, addr1


        # Make sure there is a space between street number and street
        sn_search = re.search('^([0-9]*)', addr1)
        street_num = addr1[:sn_search.end()]
        addr_rest = addr1[sn_search.end():]
        addr1 = street_num+' '+addr_rest.strip()


        # Make sure spacing didn't confuse city with a road type
        if city in address_abbreviations or replace_with_road_abbreviations(city) in address_abbreviations:
            addr1 = addr1 +' '+replace_with_road_abbreviations(city)
            city = ''

        # Do same for addr2
        if addr2 in address_abbreviations or replace_with_road_abbreviations(addr2) in address_abbreviations:
            addr1 = addr1 +' '+replace_with_road_abbreviations(addr2)
            addr2 = ''

        # put abbreviations for Road, Drive, etcc, in addr1
        addr1 = replace_with_road_abbreviations(addr1)

        # try to remove extra crap from addr1
        for abbr in address_abbreviations:
            addr_space = ' '+abbr+' '
            if addr1.find(addr_space) > 0:
                addr1_split = addr1.split(addr_space)
                addr1 = addr1_split[0]+' '+abbr
                addr2 = ' '.join(addr1_split[1:])+', '+addr2

        # Only care about first 5 digits of zipcode
        if len(zipcode) > 5:
            zipcode = zipcode[:5]


        #print 'original:', row[2]
        #print 'final: addr1, c, s, z:', addr1, ',', city, ',', state, ',', zipcode


        #if line > 1000:
        #    break





        is_person = 0
        is_business = 0

        name_prefix = ''
        name_first = ''
        name_middle = ''
        name_last = ''
        name_suffix = ''


        #print row[1], full_name

        raw_name_split = raw_name.split(' ')

        len_raw_name_split = len(raw_name_split)
        suffix_index = len_raw_name_split - 1

        # Only split out name for individuals, 
        if row[3] in ['Self (Candidate)', 'Individual'] and raw_name_split[suffix_index] not in ['INC', 'LLC', 'PAC']:

            is_person = 1

            # is last element suffix
            if raw_name_split[suffix_index] in suffix_list:
                #print 'suffix last'
                full_name = ' '.join(raw_name_split)

            # is first element a prefix
            elif raw_name_split[0] in prefix_list:
                #print 'prefix first'
                full_name = ' '.join(raw_name_split)

            # does last element have a dash? if so, probably a last name
            elif raw_name_split[suffix_index].find('-') > 0:
                #print 'last element has dash'
                full_name = ' '.join(raw_name_split)


            # is last element a single letter? If so, treat like middle initial
            elif len(raw_name_split[suffix_index]) == 1:
                #print 'last element is single letter'
                # Check if second is suffix
                if len(raw_name_split) >= 3 and raw_name_split[1] in suffix_list:
                    full_name = ' '.join(raw_name_split[2:]) + ' ' + raw_name_split[0] + ' ' + raw_name_split[1]
                else:
                    full_name = ' '.join(raw_name_split[1:]) + ' ' + raw_name_split[0]

            # is first element a suffix
            elif raw_name_split[0] in suffix_list:
                #print 'first element is suffix'
                full_name = ' '.join(raw_name_split[1:]) + ' ' + raw_name_split[0]

            # is second element a suffix
            elif len(raw_name_split) >= 3 and raw_name_split[1] in suffix_list:
                #print 'second element is suffix'
                full_name = ' '.join(raw_name_split[2:]) + ' ' + raw_name_split[0] + ' ' + raw_name_split[1]

            # does first element have a dash
            elif raw_name_split[0].find('-') > 0:
                #print 'first element has dash'
                # Check if second is suffix
                if len(raw_name_split) >= 3 and raw_name_split[1] in suffix_list:
                    full_name = ' '.join(raw_name_split[2:]) + ' ' + raw_name_split[0] + ' ' + raw_name_split[1]
                else:
                    full_name = ' '.join(raw_name_split[1:]) + ' ' + raw_name_split[0]

            # is last element a popular last name
            elif de_election_db_cache.return_census_last_name_id_from_name(raw_name_split[suffix_index]) > 0:
                #print 'last element popular last name'
                full_name = ' '.join(raw_name_split)

            # is first element a popular last name
            elif de_election_db_cache.return_census_last_name_id_from_name(raw_name_split[0]) > 0:
                #print 'first element popular last name'
                # Check if second is suffix
                if len(raw_name_split) >= 3 and raw_name_split[1] in suffix_list:
                    full_name = ' '.join(raw_name_split[2:]) + ' ' + raw_name_split[0] + ' ' + raw_name_split[1]
                else:
                    full_name = ' '.join(raw_name_split[1:]) + ' ' + raw_name_split[0]

            # All else fail, just use default order
            else:
                #print 'leaving as is'
                full_name = ' '.join(raw_name_split)


            #print raw_name, 'became:', full_name


            # Check prefixes
            for p in prefix_list:
                p_space = p+' '
                len_p_space = len(p_space)
                if full_name[:len_p_space] == p_space:
                    name_prefix = p
                    full_name = full_name[len_p_space:]


            # Check suffixes
            for s in suffix_list:
                s_space = ' '+s
                len_s_space = len(s_space)
                len_name = len(full_name)
                if full_name[len_name-len_s_space:] == s_space:
                    name_suffix = s
                    full_name = full_name[:len_name-len_s_space]

            full_name_split = full_name.split(' ')

            if len(full_name_split) < 2:
                print 'line',line,': bad name:',full_name


            name_last = full_name_split.pop()

            if len(full_name_split):
                # Reverse, get first element, reverse back
                full_name_split.reverse()
                name_first = full_name_split.pop()
                full_name_split.reverse()

            name_middle = ' '.join(full_name_split)

            #print name_prefix, '/', name_first, '/', name_middle, '/', name_last, '/', name_suffix

            # Check if contributor already exists from first,last,suffix,addr1,zipcode
            try:

                contributor = DePoliticalDonationContributor.query\
                    .filter(DePoliticalDonationContributor.name_first == name_first)\
                    .filter(DePoliticalDonationContributor.name_last == name_last)\
                    .filter(DePoliticalDonationContributor.name_suffix == name_suffix)\
                    .filter(DePoliticalDonationContributor.addr1 == addr1)\
                    .filter(DePoliticalDonationContributor.zipcode == zipcode)\
                    .one()

            except Exception as e:

                # Try swapping first and last name
                try:

                    contributor = DePoliticalDonationContributor.query\
                        .filter(DePoliticalDonationContributor.name_first == name_last)\
                        .filter(DePoliticalDonationContributor.name_last == name_first)\
                        .filter(DePoliticalDonationContributor.name_suffix == name_suffix)\
                        .filter(DePoliticalDonationContributor.addr1 == addr1)\
                        .filter(DePoliticalDonationContributor.zipcode == zipcode)\
                        .one()


                except Exception as e:

                    if name_first == '' and name_last == '':
                        print 'storing empty name for:', raw_name

                    contributor = DePoliticalDonationContributor()
                    contributor.name_prefix = name_prefix
                    contributor.name_first = name_first
                    contributor.name_middle = name_middle
                    contributor.name_last = name_last
                    contributor.name_suffix = name_suffix
                    contributor.addr1 = addr1
                    contributor.addr2 = addr2
                    contributor.addr3 = addr3
                    contributor.city = city
                    contributor.state = state
                    contributor.zipcode = zipcode
                    contributor.is_person = is_person
                    contributor.is_business = is_business

                    db.session.add(contributor)        
                    db.session.commit()




            """

            # Check for suffixes
            if check_suffix.upper() in suffix_list:
                name_suffix = check_suffix.upper()

                name_last = full_name_split.pop()

            # Reverse, get first element, reverse back
            full_name_split.reverse()
            check_prefix = full_name_split.pop()
            full_name_split.reverse()


            # Check first element for prefix
            if len(check_prefix) < 4 and check_prefix.upper() not in prefix_list:
                #print check_prefix
                pass


            if len(check_suffix) < 5 and check_suffix.upper() not in suffix_list:
                #print check_suffix
                pass

            if check_suffix.upper() in ['INC', 'LLC', 'PAC']:
                #print 'line',line,':',full_name
                pass

            if len(full_name_split) > 5:
                #print 'line',line,':',full_name
                pass

            """


        # Don't store individual names
        else:

            # Check if contributor already exists from full_name,addr1,zipcode
            try:

                contributor = DePoliticalDonationContributor.query\
                    .filter(DePoliticalDonationContributor.full_name == full_name)\
                    .filter(DePoliticalDonationContributor.addr1 == addr1)\
                    .filter(DePoliticalDonationContributor.zipcode == zipcode)\
                    .one()

            except Exception as e:

                contributor = DePoliticalDonationContributor()
                contributor.full_name = full_name
                contributor.addr1 = addr1
                contributor.addr2 = addr2
                contributor.addr3 = addr3
                contributor.city = city
                contributor.state = state
                contributor.zipcode = zipcode
                contributor.is_person = is_person
                contributor.is_business = is_business

                db.session.add(contributor)        
                db.session.commit()


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



        # Check if donation already exists from contributor_id, committee_id, donation_date, donation_amount
        try:

            donation = DePoliticalDonation.query\
                .filter(DePoliticalDonation.contributor_id == contributor.id)\
                .filter(DePoliticalDonation.committee_id == committee_id)\
                .filter(DePoliticalDonation.donation_date == donation_date_obj)\
                .filter(DePoliticalDonation.donation_amount == donation_amount)\
                .one()

        except Exception as e:

            donation = DePoliticalDonation()
            donation.contributor_id = contributor.id
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
        # Convert address string into add1, add2, city, state, zip
        address_split = row[2].split(' ')

        zipcode = ''.join(re.findall('([0-9])', address_split.pop()))

        state = address_split.pop()

        if state == '':
            state = address_split.pop()

        city = address_split.pop()

        if city == '':
            city = address_split.pop()

        if city == '':
            city = address_split.pop()

        if city in ['City', 'Beach', 'View', 'Island', 'Castle', 'D.C.']:
            city = address_split.pop() + ' ' + city

        if city not in city_list:
            city_list.append(city)

        #print city, state, zipcode

        #print address_split.pop()

        """




        # Store row


        total_contributed = total_contributed + float(row[7])

    #print city_list

    print 'total contributed:', total_contributed








if __name__ == "__main__":
    manager.run()