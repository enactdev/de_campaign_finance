# de_campaign_finance
Looking at campaign finance data from the state of Delaware


# Basic guide to git:
http://rogerdudler.github.io/git-guide/


To use this code:

copy config_example.py to config.py

Edit CONTRIBUTION_CSV_DIRECTORY to point to where you will store the CSV files. For privacy reasons, this git will not host the CSV files with users campaign contribution data.


Download campagin contribution data from:

https://cfrs.elections.delaware.gov

Click on "View Contributions / Loans"

Select a year, click search, and download the CSV file.

Store the files in a directory, recommended store format: DE_Contributions_<YEAR>.csv such as DE_Contributions_2016.csv

Code is loaded from manage.py. There is a test command you can use on the command line to make sure Flask is set up correctly.







