# btc-portfolio-automation
I buy Bitcoin everyday through an exchange and log those transactions in a Google sheet. I automated that process.

### Backstory
Some time ago I started squirreling away money in cryptocurrency. I quickly grew tired of constantly monitoring prices for buying opportunities and making manually, so I began using a more passive strategy called [dollar-cost averaging](https://www.investopedia.com/terms/d/dollarcostaveraging.asp) (DCA). Most major exchanges have a "reccuring buy" feature that allows you to automate your crypto purchases and make DCA easy. I'm meticulous about tracking the performance of my investments, so I created a googlesheet to log the details of every transaction.

After telling friends and family about my strategy and showing them my investment dashboard, a few of them asked me if I could implement the same thing for them. I love bringing people into crypto, so I agreed. It wasn't long before I was purchasing, managing, and tracking cryptocurrency transactions for multiple people. Inevitably, tedious administrative work began to pile up. Every day I had to preruse my email for transaction confirmations, copy and paste that transaction data into the appropriate spreadsheet, format the new cells for each spreadsheet, and then file away the old emails to avoid mistaking them for new transactions.

This repository contains the files I use to automate that entire process everyday.

### Process Overview

This program works by connecting to both an email client of choice (I use gmail) and the Google Drive API to interface with Googlesheets.

The overall process can be broken down into four main parts:  
1. Regex my email inbox to gather all of the relevant transaction data. This requires the use of the imapclient, pyzmail, and re modules to interface with gmail, interpret the contents of messages, and find specific phrases and terms within those contents.

2. Filtering new transactions apart from transactions I've already logged. Doing so consists of comparing the two lists of transaction ID (IDs already recorded and the IDs regexed from our email) and finding those not recorded. Once an unrecorded ID is found, we regex for the rest of the terms we need (crypto total, USD total, transaction timestamp, and conversion rate) and put those terms in a transaction data dictionary under their unique ID.

3. From that data, calculate how much cryptocurrency each portfolio owner bought that day. This is just a bit of algebra to divide up the total transaction among the portfolio owners. Each portoflio owner has a specified daily investment amount in USD that we can use to calculate their "share" in the pot. This information is put into a dictionary of its own.

4. Package that information up into a nice form and input it into the appropriate tabs in the googlesheet. This step requires the use of multiple nested loops to iterate through each transaction ID not yet recorded, and then for every person with a claim on that ID. For each new transaction we pull the relevant data, and then for each person in that transaction we pull the information relevant to their share. We can then use the gspread library to input that data.
