import imapclient, pyzmail, re, gspread, datetime
from oauth2client.service_account import ServiceAccountCredentials

def get_googlesheets_client():

    scope = ['https://spreadsheets.google.com/feeds','https://www.googleapis.com/auth/drive']
    credentials = ServiceAccountCredentials.from_json_keyfile_name('insert full path to credentials .json file', scope)
    return gspread.authorize(credentials)

def connect_email(emailAdd, emailPass):
    """
    connects to email and searches with criteria, pulls regexMessage, cleans it, and returns regexMessage for regex_email function
    """
    conn = imapclient.IMAPClient('imap.gmail.com', ssl = True)
    conn.login(emailAdd, emailPass)
    return conn

def fetch_emails(conn, searchCriteria, emailInbox):
    """
    searches designated inbox for all the UIDS that match the searchCriteria and returns a list of those UIDs. Also prints a count of the number of emails that matched.
    """
    conn.select_folder(emailInbox, readonly=False)
    UIDs = conn.gmail_search(searchCriteria, charset='UTF-8')
    if len(UIDs) > 0:
        print("Matching emails found: " + str(len(UIDs)))
        return UIDs

    else:
        print("!NO MATCHING EMAILS FOUND!")
        exit()

def check_transaction_IDs(conn, UIDs, IDs_for_regex, trans_ID_list, transaction_data, USD_contributions):
    """
    iterates through each email, grabs that emails transaction ID through Regex, then checks if that ID has been recorded. If it has not, it proceeds to regex the entire message according to our IDs_for_regex by calling regex_email(). along the way we mark each email as 'seen' and increment the number of unrecorded transaction IDs.
    """
    unrecorded_transaction_IDs = 0
    for i in range(0,len(UIDs)):
        email_trans_ID, regexMessage = grab_email_IDs(i, conn, UIDs, IDs_for_regex)

        if email_trans_ID: #if an email exists
            email_trans_ID = email_trans_ID.group(1)

            if email_trans_ID not in trans_ID_list: #cross reference each ID with the existing ID list.
                unrecorded_transaction_IDs += 1
                conn.set_flags(UIDs[i],'\Seen')
                print("UNIQUE")
                regex_email(IDs_for_regex, transaction_data, regexMessage, email_trans_ID, USD_contributions)
            else:
                print("RECORDED\n"+email_trans_ID)

    if unrecorded_transaction_IDs == 0: #exit the program if there are no unrecorded IDs
        print("ALL TRANSACTIONS RECORDED")
        exit()

    if len(transaction_data) == 0: #exit the program if unable to grab any transaction data, which indicates a regex error
        print("=====\nNO TRANSACTION DATA")
        exit()

def grab_email_IDs(i, conn, UIDs, IDs_for_regex):
    """
    searches each email by UID for its transaction ID. returns that ID to be compared with the list of existing IDs.
    """
    print("======")
    rawEmail = conn.fetch(UIDs[i],['BODY[]','FLAGS'])
    regexMessage = pyzmail.PyzMessage.factory(rawEmail[UIDs[i]][b'BODY[]'])
    regexMessage = str(regexMessage.text_part.get_payload().decode('UTF-8'))
    email_trans_ID = re.search(IDs_for_regex['TransID'],regexMessage)
    return email_trans_ID, regexMessage

def regex_email(IDs_for_regex, transaction_data, regexMessage, email_trans_ID, USD_contributions):
    """
    regexes for all terms listed in IDs_for_regex, and appends that data to transaction_data.

    because some emails may be for other cryptocurrencies, it first checks to ensure that this email contains a btc transaction. then it iterates through each IDs_for_regex term and uses a try/except block to convert the right data to float.

    has a check near the bottom to ensure that the total USD contributions equal the sum of the USD in the transaction. Would be bad if this was not that same, and the amount does change from time to time.
    """
    btc_check = re.search(IDs_for_regex['BTC'], regexMessage)
    if btc_check.group(3) == "BTC":
        transaction_data[email_trans_ID] = {}

        for id in IDs_for_regex.keys():
            data = re.search(IDs_for_regex[id], regexMessage)

            if data:

                    transaction_data[email_trans_ID][id] = data.group(1)

                    try:
                        transaction_data[email_trans_ID][id] = float(transaction_data[email_trans_ID][id])
                    except ValueError:
                        pass
            else:
                print("NO MATCH FOUND - " + id)
                exit()

        for id,value in transaction_data[email_trans_ID].items(): #print out the contents of each email ID key.
            print(id + ": " + str(value))

        if transaction_data[email_trans_ID]['USD'] != sum(USD_contributions.values()):
            print("TRANSACTION AMOUNT DOES NOT EQUAL CONTRIBUTIONS")
            exit()

        print(transaction_data)

    elif btc_check.group(3) != "BTC": #skips email if not a btc transaction
        print("SKIPPED")

    return transaction_data

def input_data_to_sheet(USD_contributions, transaction_data, share_of_BTC, googlesheet_name, client):
    """
    uploads data to the googlesheet.

    loops through each ID in transaction_data and each person in USD_contributions, creating a new data_list of the relevant data to upload at each iterationof the loop. appends each value to the correct column one by one.

    Google APIs have a quota that cannot be exceeded, so this function contains a try/except block to monitor for that error.
    """

    for id in transaction_data:
        for person in USD_contributions:
            #data to upload
            data_list = [transaction_data[id]['Date'],
                        transaction_data[id]['TransID'],
                        transaction_data[id]['ConvRate'],
                        USD_contributions[person],
                        share_of_BTC[id][person]
                        ]
            #opens the worksheet of the person in USD_contributions
            worksheet = client.open(googlesheet_name).worksheet(person.title())
            update_row = len(worksheet.col_values(2)) + 1 #navigate to the row where values start, col titles, empty cells
            update_col = 2 #iterates after each item to move by 1 col to the right
            print("Updating " + person.title() + ", row " + str(update_row))
            for item in data_list:
                try:
                    worksheet.update_cell(update_row, update_col, item)
                except gspread.exceptions.APIError:
                    print("GOOGLE API QUOTA EXCEEDED. WAIT 1 MIN.")
                    exit()
                update_col += 1

def get_transID_list(client, googlesheet_name, tab_name):
    """
    get the list of recorded transaction IDs to cross reference with the IDs we will get from email. return that list of IDs.
    """
    worksheet = client.open(googlesheet_name).worksheet(tab_name)
    transaction_ID_list = worksheet.col_values(3)

    return transaction_ID_list

def split_up_BTC(USD_contributions, transaction_data):
    """
    takes the USD contributions per person (daily investment) and total BTC in each transaction to calculate each persons share of that total. records those portions into a share_of_BTC dictionary. also returns percent_of_total and totalUSD for debugging purposes. only share_of_BTC data will be uploaded to googlesheet.
    """
    print("======")

    #function that takes USDC contributions per person (daily investment) and total BTC to calculate each persons share of the bulk BTC purchase, returns total USDC and two dictionaries with contribution percentages and split of BTC.

    totalUSD = sum(USD_contributions.values())
    percent_of_total = {}
    share_of_BTC = {}

    for id in transaction_data: #establish dict key for each term in transaction_data
        percent_of_total[id]={}
        share_of_BTC[id]={}

        for person in USD_contributions:
            percent_of_total[id][person]=round(USD_contributions[person]/totalUSD,3) #calc each person's percentage
            share_of_BTC[id][person]=round(percent_of_total[id][person]*transaction_data[id]['BTC'],8)

    print("Percentages: " + str(percent_of_total))
    print("BTC split: " + str(share_of_BTC))

    return totalUSD, percent_of_total, share_of_BTC

def sort_googlesheet(client, googlesheet_name, USD_contributions):
    """
    sort the googlesheet by cycling through each tab and sorting each one by one
    """
    for person in USD_contributions:
        worksheet = client.open(googlesheet_name).worksheet(person.title())
        last_row = len(worksheet.col_values(2))
        worksheet.sort((2, 'des'),range="B4:" + "G" + str(last_row))
