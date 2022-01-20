import datetime

"""
In this file are all the variables used to control the automation. They've all been redacted for obvious reasons.
"""

today = datetime.date.today()
yesterday = datetime.date.today() - datetime.timedelta(days=1)
yesterday = str(yesterday.strftime('%m-%d-%Y'))
emailAdd = 'email address'
emailPass = 'email password'
emailInbox = 'inbox to search'
googlesheet_name = 'google sheet name'
searchCriteria = 'criteria to search in inbox'
tab_name = 'starting tab name'
USD_contributions = {'person1':10,'person2':30,'person3':5,'person4':15} #the amount each person in the portfolio invests daily
#dictionary with regex terms. used to search emails for transaction data.
IDs_for_regex = {'BTC':'Purchase Amount: (\d+.(\d){1,}) (BTC|ETH)',
                 'TransID':'Transaction ID: ((\w){25})',
                 'USD':'Deposit Amount: ((\d){1,}) USD',
                 'ConvRate':'Fill Price: (\d+.(\d){2}) USD',
                 'Date':'placed on ((\w){1,} (\d){1,}, (\d){4})'}

transaction_data = {} #empty dictionary used to store transaction data in the same format as the IDs_for_regex dictionary.
