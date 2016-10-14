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




@manager.command
def store_all_campaign_contributions_csv():
    for y in range(2003, 2016):
        store_campaign_contributions_csv(y)





state_replacement_dict = {u'Mississippi': u'MS', u'Oklahoma': u'OK', u'Delaware': u'DE', u'Minnesota': u'MN', \
u'Illinois': u'IL', u'Arkansas': u'AR', u'New Mexico': u'NM', u'Indiana': u'IN', u'Maryland': u'MD', u'Louisiana': u'LA', \
u'Idaho': u'ID', u'Wyoming': u'WY', u'Tennessee': u'TN', u'Arizona': u'AZ', u'Iowa': u'IA', u'Michigan': u'MI', u'Kansas': u'KS', \
u'Utah': u'UT', u'Virginia': u'VA', u'Oregon': u'OR', u'Connecticut': u'CT', u'Montana': u'MT', u'California': u'CA', \
u'Massachusetts': u'MA', u'West Virginia': u'WV', u'South Carolina': u'SC', u'New Hampshire': u'NH', u'Wisconsin': u'WI', \
u'Vermont': u'VT', u'Georgia': u'GA', u'North Dakota': u'ND', u'Pennsylvania': u'PA', u'Florida': u'FL', u'Alaska': u'AK', \
u'Kentucky': u'KY', u'Hawaii': u'HI', u'Nebraska': u'NE', u'Missouri': u'MO', u'Ohio': u'OH', u'Alabama': u'AL', \
u'Rhode Island': u'RI', u'South Dakota': u'SD', u'Colorado': u'CO', u'New Jersey': u'NJ', u'Washington': u'WA', \
u'North Carolina': u'NC', u'New York': u'NY', u'District of Columbia': u'DC', u'Texas': u'TX', u'Nevada': u'NV', u'Maine': u'ME'}
state_replacement_dict['DC, DC'] = 'DC'
state_replacement_dict['DC, MD'] = 'DC'
state_replacement_dict['DE, DE'] = 'DE'
state_replacement_dict['DE DE'] = 'DE'

#state_replacement_dict[''] = ''



# Upper case the string before testing
# Generated by function generate_street_suffix_abbr_dict, which pulls form USPS
street_type_replacement_dict = {u'WLS': u'WLS', u'CPE': u'CPE', u'ORCHRD': u'ORCH', u'CRESCENT': u'CRES', u'FALL': u'FALL', u'BEACH': u'BCH', u'MSSN': u'MSN', u'RAMP': u'RAMP', u'KYS': u'KYS', u'SPG': u'SPG', u'JCTN': u'JCT', u'TUNEL': u'TUNL', u'PARKWAYS': u'PKWY', u'COVE': u'CV', u'BYP': u'BYP', u'SPRINGS': u'SPGS', u'ISLANDS': u'ISS', u'RIVER': u'RIV', u'SPUR': u'SPUR', u'JCTS': u'JCTS', u'VIADCT': u'VIA', u'PINES': u'PNES', u'EXPRESS': u'EXPY', u'MNRS': u'MNRS', u'TUNLS': u'TUNL', u'GROVES': u'GRVS', u'SUMITT': u'SMT', u'OVL': u'OVAL', u'VIEW': u'VW', u'CRSNT': u'CRES', u'PKWYS': u'PKWY', u'TRK': u'TRAK', u'THROUGHWAY': u'TRWY', u'SQUARE': u'SQ', u'CSWY': u'CSWY', u'CMP': u'CP', u'CENTR': u'CTR', u'VLG': u'VLG', u'VLY': u'VLY', u'FRD': u'FRD', u'COMMON': u'CMN', u'GRV': u'GRV', u'FLAT': u'FLT', u'LOAF': u'LF', u'JCTNS': u'JCTS', u'UNION': u'UN', u'BAYOO': u'BYU', u'DRIVES': u'DRS', u'BAYOU': u'BYU', u'GRN': u'GRN', u'FERRY': u'FRY', u'TRCE': u'TRCE', u'BLF': u'BLF', u'SPRNG': u'SPG', u'BYPAS': u'BYP', u'RADL': u'RADL', u'HLS': u'HLS', u'VWS': u'VWS', u'MT': u'MT', u'GRDN': u'GDN', u'FT': u'FT', u'GLN': u'GLN', u'CTS': u'CTS', u'SMT': u'SMT', u'KNOL': u'KNL', u'STATION': u'STA', u'BEND': u'BND', u'CORNER': u'COR', u'POINT': u'PT', u'SHL': u'SHL', u'MDW': u'MDWS', u'BURGS': u'BGS', u'ESTATE': u'EST', u'CRSENT': u'CRES', u'PLAIN': u'PLN', u'MOUNT': u'MT', u'MNTAIN': u'MTN', u'MEDOWS': u'MDWS', u'SPRNGS': u'SPGS', u'TURNPIKE': u'TPKE', u'CREEK': u'CRK', u'SQ': u'SQ', u'ST': u'ST', u'ALY': u'ALY', u'ROADS': u'RDS', u'RADIEL': u'RADL', u'OVERPASS': u'OPAS', u'TRLR': u'TRLR', u'TRLS': u'TRL', u'RIDGE': u'RDG', u'FORESTS': u'FRST', u'GREEN': u'GRN', u'LF': u'LF', u'GARDN': u'GDN', u'VDCT': u'VIA', u'LN': u'LN', u'PARKWY': u'PKWY', u'BLUFF': u'BLF', u'CLIFFS': u'CLFS', u'FORK': u'FRK', u'STA': u'STA', u'KEYS': u'KYS', u'STN': u'STA', u'RANCH': u'RNCH', u'FORG': u'FRG', u'REST': u'RST', u'FORD': u'FRD', u'FRWAY': u'FWY', u'CRSSNG': u'XING', u'CNTR': u'CTR', u'STR': u'ST', u'KNOLL': u'KNL', u'FORT': u'FT', u'BOUL': u'BLVD', u'SQRS': u'SQS', u'HAVEN': u'HVN', u'NCK': u'NCK', u'RST': u'RST', u'PIKES': u'PIKE', u'GLENS': u'GLNS', u'SQRE': u'SQ', u'RAPID': u'RPD', u'PKWAY': u'PKWY', u'LK': u'LK', u'GARDENS': u'GDNS', u'PIKE': u'PIKE', u'RAD': u'RADL', u'EXTS': u'EXTS', u'BOTTOM': u'BTM', u'STRAV': u'STRA', u'FRRY': u'FRY', u'LCKS': u'LCKS', u'CNYN': u'CYN', u'RD': u'RD', u'PRT': u'PRT', u'PRR': u'PR', u'EXTN': u'EXT', u'ROAD': u'RD', u'CRSE': u'CRSE', u'CURVE': u'CURV', u'SHOARS': u'SHRS', u'VIA': u'VIA', u'XING': u'XING', u'STREME': u'STRM', u'LAKE': u'LK', u'TRAIL': u'TRL', u'RADIAL': u'RADL', u'EXPRESSWAY': u'EXPY', u'JUNCTIONS': u'JCTS', u'CLIFF': u'CLF', u'CNTER': u'CTR', u'PASSAGE': u'PSGE', u'TRAFFICWAY': u'TRFY', u'MEADOWS': u'MDWS', u'HARBORS': u'HBRS', u'MOUNTAIN': u'MTN', u'GREENS': u'GRNS', u'ANNX': u'ANX', u'CEN': u'CTR', u'PKY': u'PKWY', u'FALLS': u'FLS', u'STRVN': u'STRA', u'BRNCH': u'BR', u'HILL': u'HL', u'VILLAGE': u'VLG', u'PLNS': u'PLNS', u'SHR': u'SHR', u'MISSN': u'MSN', u'STRAVN': u'STRA', u'PLAZA': u'PLZ', u'EXPY': u'EXPY', u'MOTORWAY': u'MTWY', u'BOTTM': u'BTM', u'SHRS': u'SHRS', u'HWAY': u'HWY', u'CREST': u'CRST', u'HIGHWAY': u'HWY', u'GLEN': u'GLN', u'SHORES': u'SHRS', u'MOUNTIN': u'MTN', u'CRES': u'CRES', u'CANYON': u'CYN', u'LOOP': u'LOOP', u'FRKS': u'FRKS', u'BTM': u'BTM', u'CENTERS': u'CTRS', u'COURT': u'CT', u'ISS': u'ISS', u'SPRING': u'SPG', u'TUNL': u'TUNL', u'HARBR': u'HBR', u'COURTS': u'CTS', u'LANE': u'LN', u'LAND': u'LAND', u'JCTION': u'JCT', u'EXPR': u'EXPY', u'STREETS': u'STS', u'EXPW': u'EXPY', u'LAKES': u'LKS', u'CAUSEWAY': u'CSWY', u'VILLIAGE': u'VLG', u'GATEWY': u'GTWY', u'VISTA': u'VIS', u'FRG': u'FRG', u'MOUNTAINS': u'MTNS', u'FRK': u'FRK', u'CLF': u'CLF', u'CLB': u'CLB', u'SKYWAY': u'SKWY', u'FRT': u'FT', u'FRY': u'FRY', u'BOULV': u'BLVD', u'ISLNDS': u'ISS', u'HVN': u'HVN', u'KEY': u'KY', u'KY': u'KY', u'FLTS': u'FLTS', u'BRIDGE': u'BRG', u'DL': u'DL', u'DM': u'DM', u'EXTENSION': u'EXT', u'LODG': u'LDG', u'ESTATES': u'ESTS', u'ISLND': u'IS', u'DV': u'DV', u'PATH': u'PATH', u'DR': u'DR', u'HIGHWY': u'HWY', u'VALLEYS': u'VLYS', u'CAMP': u'CP', u'RPD': u'RPD', u'LOOPS': u'LOOP', u'RAPIDS': u'RPDS', u'HOLW': u'HOLW', u'RNCHS': u'RNCH', u'HOLLOW': u'HOLW', u'VALLY': u'VLY', u'MILL': u'ML', u'STRVNUE': u'STRA', u'ANNEX': u'ANX', u'PNES': u'PNES', u'TUNNL': u'TUNL', u'ISLES': u'ISLE', u'LGT': u'LGT', u'MEADOW': u'MDW', u'TRAILS': u'TRL', u'EXT': u'EXT', u'STREET': u'ST', u'WELLS': u'WLS', u'EXP': u'EXPY', u'BLVD': u'BLVD', u'WY': u'WAY', u'CIRCLES': u'CIRS', u'RIV': u'RIV', u'GRDEN': u'GDN', u'TUNNELS': u'TUNL', u'PATHS': u'PATH', u'KNL': u'KNL', u'PARK': u'PARK', u'VILLAGES': u'VLGS', u'PARKS': u'PARK', u'TRACKS': u'TRAK', u'BLUF': u'BLF', u'PASS': u'PASS', u'BND': u'BND', u'GRDNS': u'GDNS', u'RDGS': u'RDGS', u'LNDG': u'LNDG', u'LANDING': u'LNDG', u'RDGE': u'RDG', u'CIRCLE': u'CIR', u'LIGHT': u'LGT', u'COMMONS': u'CMNS', u'VLYS': u'VLYS', u'FREEWAY': u'FWY', u'SHORE': u'SHR', u'CRK': u'CRK', u'PORT': u'PRT', u'SPNGS': u'SPGS', u'PR': u'PR', u'LDG': u'LDG', u'PT': u'PT', u'FIELDS': u'FLDS', u'DRIV': u'DR', u'MALL': u'MALL', u'BYPASS': u'BYP', u'PL': u'PL', u'MEWS': u'MEWS', u'DIVIDE': u'DV', u'CLUB': u'CLB', u'VILL': u'VLG', u'TRLRS': u'TRLR', u'LODGE': u'LDG', u'ANEX': u'ANX', u'TRAILER': u'TRLR', u'UNDERPASS': u'UPAS', u'NECK': u'NCK', u'TRACE': u'TRCE', u'TRACK': u'TRAK', u'FRST': u'FRST', u'STRT': u'ST', u'RPDS': u'RPDS', u'STRM': u'STRM', u'STRA': u'STRA', u'ANX': u'ANX', u'LCK': u'LCK', u'COR': u'COR', u'JUNCTION': u'JCT', u'STREAM': u'STRM', u'DVD': u'DV', u'HARB': u'HBR', u'PRK': u'PARK', u'RIVR': u'RIV', u'OVAL': u'OVAL', u'VIST': u'VIS', u'MANOR': u'MNR', u'TUNNEL': u'TUNL', u'GTWAY': u'GTWY', u'PKWY': u'PKWY', u'AVENU': u'AVE', u'JUNCTON': u'JCT', u'SUMMIT': u'SMT', u'HWY': u'HWY', u'MTIN': u'MTN', u'TRACES': u'TRCE', u'TERRACE': u'TER', u'ORCHARD': u'ORCH', u'CENTRE': u'CTR', u'LOCK': u'LCK', u'COVES': u'CVS', u'FIELD': u'FLD', u'WAY': u'WAY', u'STATN': u'STA', u'CP': u'CP', u'GROV': u'GRV', u'CV': u'CV', u'CT': u'CT', u'LNDNG': u'LNDG', u'RUN': u'RUN', u'PLZ': u'PLZ', u'TRAK': u'TRAK', u'RUE': u'RUE', u'LOCKS': u'LCKS', u'PLN': u'PLN', u'MNTN': u'MTN', u'FRWY': u'FWY', u'DIV': u'DV', u'KNOLLS': u'KNLS', u'LIGHTS': u'LGTS', u'CRCLE': u'CIR', u'HIWY': u'HWY', u'TERR': u'TER', u'JCT': u'JCT', u'INLT': u'INLT', u'IS': u'IS', u'BROOK': u'BRK', u'BROOKS': u'BRKS', u'MTN': u'MTN', u'CIRCL': u'CIR', u'VW': u'VW', u'FLATS': u'FLTS', u'PINE': u'PNE', u'ARC': u'ARC', u'LDGE': u'LDG', u'FREEWY': u'FWY', u'HILLS': u'HLS', u'SHLS': u'SHLS', u'BOT': u'BTM', u'BRDGE': u'BRG', u'DRV': u'DR', u'FWY': u'FWY', u'BR': u'BR', u'BCH': u'BCH', u'FORKS': u'FRKS', u'HIWAY': u'HWY', u'VL': u'VL', u'HBR': u'HBR', u'TURNPK': u'TPKE', u'CTR': u'CTR', u'CENT': u'CTR', u'CROSSROADS': u'XRDS', u'RVR': u'RIV', u'HOLWS': u'HOLW', u'PRAIRIE': u'PR', u'BRANCH': u'BR', u'VALLEY': u'VLY', u'ALLY': u'ALY', u'GROVE': u'GRV', u'CLFS': u'CLFS', u'RIDGES': u'RDGS', u'PORTS': u'PRTS', u'VILLAG': u'VLG', u'BYPA': u'BYP', u'VIEWS': u'VWS', u'HARBOR': u'HBR', u'SQR': u'SQ', u'SQU': u'SQ', u'BYPS': u'BYP', u'FORDS': u'FRDS', u'MANORS': u'MNRS', u'ISLE': u'ISLE', u'CRCL': u'CIR', u'BURG': u'BG', u'HLLW': u'HOLW', u'GARDEN': u'GDN', u'FLS': u'FLS', u'FLT': u'FLT', u'HT': u'HTS', u'HL': u'HL', u'AVENUE': u'AVE', u'FLD': u'FLD', u'GTWY': u'GTWY', u'CENTER': u'CTR', u'VIS': u'VIS', u'MNR': u'MNR', u'MNT': u'MT', u'PLAINS': u'PLNS', u'JUNCTN': u'JCT', u'PTS': u'PTS', u'ROW': u'ROW', u'FORGES': u'FRGS', u'BOULEVARD': u'BLVD', u'TRL': u'TRL', u'COURSE': u'CRSE', u'TRKS': u'TRAK', u'CAPE': u'CPE', u'SHOAR': u'SHR', u'VIADUCT': u'VIA', u'AVN': u'AVE', u'UN': u'UN', u'HTS': u'HTS', u'SHOAL': u'SHL', u'CROSSING': u'XING', u'AVE': u'AVE', u'ROUTE': u'RTE', u'FLDS': u'FLDS', u'VLGS': u'VLGS', u'AVNUE': u'AVE', u'ESTS': u'ESTS', u'FORGE': u'FRG', u'STRAVENUE': u'STRA', u'MNTNS': u'MTNS', u'AVEN': u'AVE', u'VLLY': u'VLY', u'VSTA': u'VIS', u'WALKS': u'WALK', u'TER': u'TER', u'PRTS': u'PRTS', u'RDS': u'RDS', u'MILLS': u'MLS', u'RDG': u'RDG', u'KNLS': u'KNLS', u'CORS': u'CORS', u'CANYN': u'CYN', u'CROSSROAD': u'XRD', u'SPURS': u'SPUR', u'VILLE': u'VL', u'VILLG': u'VLG', u'WAYS': u'WAYS', u'ISLAND': u'IS', u'SUMIT': u'SMT', u'MDWS': u'MDWS', u'CIRC': u'CIR', u'BRK': u'BRK', u'BRG': u'BRG', u'DALE': u'DL', u'TRNPK': u'TPKE', u'WALK': u'WALK', u'HRBOR': u'HBR', u'WALL': u'WALL', u'BLUFFS': u'BLFS', u'DRIVE': u'DR', u'PLZA': u'PLZ', u'CIR': u'CIR', u'RANCHES': u'RNCH', u'PARKWAY': u'PKWY', u'SPNG': u'SPG', u'EXTNSN': u'EXT', u'ARCADE': u'ARC', u'DAM': u'DM', u'WELL': u'WL', u'ALLEY': u'ALY', u'LKS': u'LKS', u'ALLEE': u'ALY', u'POINTS': u'PTS', u'FOREST': u'FRST', u'ORCH': u'ORCH', u'CORNERS': u'CORS', u'EST': u'EST', u'STRAVEN': u'STRA', u'SHOALS': u'SHLS', u'RNCH': u'RNCH', u'HOLLOWS': u'HOLW', u'AV': u'AVE', u'SQUARES': u'SQS', u'GDNS': u'GDNS', u'SPGS': u'SPGS', u'VST': u'VIS', u'CAUSWA': u'CSWY', u'GATEWAY': u'GTWY', u'UNIONS': u'UNS', u'GATWAY': u'GTWY'}


# Extras
street_type_replacement_dict['PK'] = 'PIKE'
street_type_replacement_dict['STREE'] = 'ST'
street_type_replacement_dict['CR'] = 'CIR'
street_type_replacement_dict['PLACE'] = 'PL'
street_type_replacement_dict['QT'] = 'CT'
street_type_replacement_dict['STS'] = 'ST'
#street_type_replacement_dict[''] = ''


# Upper case the string before testing
street_direction_replacement_dict = {'NORTH': 'N', 'SOUTH': 'S', 'EAST': 'E', 'WEST': 'W', 'NORTHEAST': 'NE', 'NORTHWEST': 'NW', \
    'SOUTHEAST': 'SE', 'SOUTHWEST': 'SW', 'SO': 'S', 'WWEST': 'W', }



# From table C2 on pg 72 of http://pe.usps.gov/cpim/ftp/pubs/Pub28/pub28.pdf
usps_unit_designators = {'LOWER': 'LOWR', 'OFFICE': 'OFC', 'FLR': 'FL', 'STOP': 'STOP', 'HANGER': 'HNGR', \
    'LOT': 'LOT', 'SUITE': 'STE', 'REAR': 'REAR', 'PENTHOUSE': 'PH', 'ROOM': 'RM', 'SPACE': 'SPC', \
    'UNIT': 'UNIT', 'FRONT': 'FRNT', 'LOBBY': 'LBBY', 'APARTMENT': 'APT', 'FLOOR': 'FL', 'DEPARTMENT': 'DEPT', \
    'SLIP': 'SLIP', 'BASEMENT': 'BSMT', 'PIER': 'PIER', 'TRAILER': 'TRLR', 'BUILDING': 'BLDG', 'UPPER': 'UPPR', \
    'SUTIE': 'STE', 'KEY': 'KEY', 'SIDE': 'SIDE'}

# Add custom
usps_unit_designators['FLR'] = 'FL'

usps_unit_designators['NO'] = '#'
usps_unit_designators['NUMBER'] = '#'
usps_unit_designators['CONDO'] = '#'

usps_unit_designators['SUTIE'] = 'STE'
usps_unit_designators['SIOTE'] = 'STE'
usps_unit_designators['SITE'] = 'STE'
usps_unit_designators['STE:'] = 'STE'
usps_unit_designators['STE'] = 'STE'
usps_unit_designators['SUTE'] = 'STE'
usps_unit_designators['SUIT'] = 'STE'


usps_unit_designators['UNTI'] = 'UNIT'
usps_unit_designators['UNITE'] = 'UNIT'
usps_unit_designators['UNIY'] = 'UNIT'
usps_unit_designators['UNITE'] = 'UNIT'
usps_unit_designators['UNIT, UNIT'] = 'UNIT'


usps_unit_designators['APT. APT'] = 'APT'
usps_unit_designators['APPT'] = 'APT'
#usps_unit_designators[''] = ''



fields_to_strip_periods = ['StreetNamePostType', 'StreetNamePreDirectional', 'AddressNumberSuffix', 'StreetNamePostModifier', \
    'StreetNamePostDirectional', 'OccupancyType', 'SubaddressType', 'SecondStreetNamePostType', 'USPSBoxGroupType']



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
    for year in range(2008, 2017):
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

            usaddress_address = usaddress.tag(mailing_address)

        except Exception as e:

            print 'usaddress ERROR:'
            print e

            # Ugh, everything below needs to be within the try statement!


        print 'usaddress addy:', usaddress_address

        address_dict = dict(usaddress_address[0])

        address_type = usaddress_address[1]
        address_dict['address_type'] = address_type
        address_dict['original_address'] = mailing_address

        # Make sure we're using state abbreviation instead of full state name
        if 'StateName' in address_dict and address_dict['StateName'] in state_replacement_dict:
            address_dict['StateName'] = state_replacement_dict[address_dict['StateName']]


        # Remove trailing '.' from any abbreviations
        for field in fields_to_strip_periods:
            if field in address_dict:
                address_dict[field] = address_dict[field].strip('.')


        # Use standard abbreviated for street direction (N instead of North)
        if 'StreetNamePreDirectional' in address_dict:
            address_dict['StreetNamePreDirectional'] = address_dict['StreetNamePreDirectional'].strip().replace(' ', '').replace('.', '')
            if address_dict['StreetNamePreDirectional'] in street_direction_replacement_dict:
                address_dict['StreetNamePreDirectional'] = street_direction_replacement_dict[address_dict['StreetNamePreDirectional']]
        
        if 'StreetNamePostDirectional' in address_dict:
            address_dict['StreetNamePostDirectional'] = address_dict['StreetNamePostDirectional'].strip().replace(' ', '').replace('.', '')
            if address_dict['StreetNamePostDirectional'] in street_direction_replacement_dict:
                address_dict['StreetNamePostDirectional'] = street_direction_replacement_dict[address_dict['StreetNamePostDirectional']]

        if 'SecondStreetNamePostDirectional' in address_dict:
            address_dict['SecondStreetNamePostDirectional'] = address_dict['SecondStreetNamePostDirectional'].strip().replace(' ', '').replace('.', '')
            if address_dict['SecondStreetNamePostDirectional'] in street_direction_replacement_dict:
                address_dict['SecondStreetNamePostDirectional'] = street_direction_replacement_dict[address_dict['SecondStreetNamePostDirectional']]




        # Use standard abbreviated for street type (Rd instead of Road)
        if 'StreetNamePostType' in address_dict and address_dict['StreetNamePostType'].strip() in street_type_replacement_dict:
                address_dict['StreetNamePostType'] = street_type_replacement_dict[address_dict['StreetNamePostType'].strip()]

        if 'SecondStreetNamePostType' in address_dict and address_dict['SecondStreetNamePostType'].strip() in street_type_replacement_dict:
                address_dict['SecondStreetNamePostType'] = street_type_replacement_dict[address_dict['SecondStreetNamePostType'].strip()]

        if 'USPSBoxGroupType' in address_dict and address_dict['USPSBoxGroupType'].strip() in street_type_replacement_dict:
                address_dict['USPSBoxGroupType'] = street_type_replacement_dict[address_dict['USPSBoxGroupType'].strip()]




        # Standardize unit types
        if 'OccupancyType' in address_dict and address_dict['OccupancyType'].strip() in usps_unit_designators:
                address_dict['OccupancyType'] = usps_unit_designators[address_dict['OccupancyType'].strip()]

        if 'SubaddressType' in address_dict and address_dict['SubaddressType'].strip() in usps_unit_designators:
                address_dict['SubaddressType'] = usps_unit_designators[address_dict['SubaddressType'].strip()]




        # Remove preceiding '#' from OccupancyIdentifier
        if 'OccupancyIdentifier' in address_dict and address_dict['OccupancyIdentifier'][0] == '#':
            address_dict['OccupancyIdentifier'] = address_dict['OccupancyIdentifier'].strip('#').strip()

            # If OccupancyType is not set, and OccupancyIdentifier is set, and OccupancyIdentifier starts with '#' 
            # then make '#' the OccupancyType
            if 'OccupancyType' not in address_dict:
                address_dict['OccupancyType'] = '#'


        # If USPSBoxType is set, just make it 'PO BOX'
        if 'USPSBoxType' in address_dict:
            address_dict['USPSBoxType'] = 'PO BOX'


        # Only connect multiple streets with '&' 
        if 'IntersectionSeparator' in address_dict and address_dict['IntersectionSeparator'] == 'AND':
            address_dict['IntersectionSeparator'] = '&'


        # Only use first 5 digits in zip code, don't care about extended
        if 'ZipCode' in address_dict and len(address_dict['ZipCode']) > 5:
            address_dict['ZipCode'] = ''.join([i for i in address_dict['ZipCode'] if i.isdigit()])[:5]


        # Clean up state name. Remove ', DE' if length is 6 and last three == ', DE'
        if 'StateName' in address_dict and len(address_dict['StateName']) == 6 and address_dict['StateName'][2:] == ', DE':
            address_dict['StateName'] = address_dict['StateName'][:2]




        print 'usaddress addy dict:', address_dict

        test_addy = TestUsAddressCleaner(**address_dict)

        db.session.add(test_addy)        


        if 'AddressNumber' not in address_dict:
            if 'PlaceName' in address_dict and address_dict['PlaceName'][0].isdigit():
                # Get number in front of PlaceName
                pass


            else:
                print 'ERROR: Bad address:', row[2]

    db.session.commit()









@manager.command
def load_testing_probable_people_library():
    for year in range(2008, 2017):
        testing_probable_people_library(year)



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

            original_name = row[1].upper().replace('  ',', ')


            # Make edits to original_name before calling probablepeople



            probablepeople_name = probablepeople.tag(original_name)


            #print 'probable name:', probablepeople_name

            name_dict = dict(probablepeople_name[0])

            name_type = probablepeople_name[1]

            name_dict['name_type'] = name_type

            name_dict['original_name'] = original_name

            print 'probable name dict:', name_dict






        except Exception as e:

            print 'probablepeople ERROR:'
            print e




        test_probable_name = TestProbablePeopleCleaner(**name_dict)

        db.session.add(test_probable_name)        




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