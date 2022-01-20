import imapclient, pyzmail, datetime, re, gspread
from oauth2client.service_account import ServiceAccountCredentials
from portfolio_auto_funcs import *
from portfolio_auto_controls import *

"""
ATTENTION: Read this repository's README before following along here. A more high-level overview of the project lives there. See portfolio_auto_funcs for the functions used below. See portfolio_auto_controls for the variables.
"""

print("PROGRAM START")

"""
Step 1:
connect to the googlesheets client and obtain credentials for step 2.
"""
client = get_googlesheets_client()

"""
Step 2:
use client credentials to log into the googlesheet and obtain a list of the currently recorded transation IDs on the sheet. We will cross reference this list of existing IDs with the list of IDs we pull from our email to find which transactions have not been logged yet.
"""
trans_ID_list = get_transID_list(client, googlesheet_name, tab_name)

"""
Step 3:
establish a connection with your email using imapclient and pyzmail.
"""
conn = connect_email(emailAdd, emailPass)

"""
Step 4:
fetch the UIDs of all emails that match our searchCriteria in our designated emailInbox.
"""
UIDs = fetch_emails(conn, searchCriteria, emailInbox)

"""
Step 5:
iterate through each email by UID and regex for that email's transaction ID, and check if that transaction ID has been recorded or not. If it has not, then regex that entire email for the data we need (see IDs_for_regex) and add that to the transaction_data dictionary.
"""
check_transaction_IDs(conn, UIDs, IDs_for_regex, trans_ID_list, transaction_data, USD_contributions)

"""
Step 6:
split up the contents of each transaction according to each person's USD contribution. return a dictionary, share_of_BTC, that logs each person's share of BTC for each transaction ID in the transaction_data dictonary.
"""
share_of_BTC = split_up_BTC(USD_contributions, transaction_data)[2]

"""
Step 7:
upload this data to the google sheet.
"""
input_data_to_sheet(USD_contributions, transaction_data, share_of_BTC, googlesheet_name, client)

"""
Step 8:
sort the google sheet in chronological order by transaction date.
"""
sort_googlesheet(client,googlesheet_name,USD_contributions)

"""
Step 9:
end your connection with the email client
"""
conn.logout()
