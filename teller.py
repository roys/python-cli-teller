#!/usr/bin/python
# -*- coding: utf-8 -*-
# TODO: Clean up everything :-)
# TODO: Should commands be subject to L10N too?
# TODO: Clean up all the unicode stuff
# TODO: Add reset to delete encrypted ID, secret and token from config file
# TODO: RK + KREDITRENTER ==> Interest
import configparser
import locale
import os
import base64
import getpass
import sys
import time
import requests
import argparse
import json
from aescipher import AESCipher
import dateutil.parser
import urllib

VERSION = '1.0.4'
FILENAME_CONFIG = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'config.ini')
COLOR_ERROR = '\033[91m'
COLOR_RESET = '\033[0m'

config = configparser.ConfigParser()
if not config.has_section('general'):
    config.add_section('general')
config.read(FILENAME_CONFIG)

clientId = clientSecret = userId = password = None


def getLanguageConfig():
    defaultLanguage = locale.getdefaultlocale()[0]

    langConfig = configparser.ConfigParser()
    try:
        langConfig.read(os.path.join(os.path.dirname(
            os.path.realpath(__file__)), 'strings_en.ini'))
    except (configparser.NoOptionError, configparser.NoSectionError, configparser.MissingSectionHeaderError):
        pass
    try:
        langConfig.read(os.path.join(os.path.dirname(
            os.path.realpath(__file__)), 'strings_' + defaultLanguage + '.ini'))
    except (configparser.NoOptionError, configparser.NoSectionError, configparser.MissingSectionHeaderError):
        pass
    try:
        langConfig.read(os.path.join(os.path.dirname(os.path.realpath(
            __file__)), 'strings_' + config.get('general', 'language') + '.ini'))
    except (configparser.NoOptionError, configparser.NoSectionError, configparser.MissingSectionHeaderError):
        pass
    return langConfig


def storeConfig():
    config.write(open(FILENAME_CONFIG, 'w'))


langConfig = getLanguageConfig()


def _(key, *args, **kwargs):
    value = ''
    error = False
    if 'error' in kwargs:
        error = kwargs['error']
    if error:
        value += COLOR_ERROR
    if langConfig.has_option('language', key):
        dictValue = langConfig.get('language', key).replace('\\t', '    ')
        for arg in args:
            dictValue = dictValue.replace('%s', str(arg).decode('utf-8'), 1)
        value += dictValue.encode('utf-8')
    else:
        value += key
    if error:
        value += COLOR_RESET
    return value


def printShortHelp():
    print()
    print(_('short_help_description'))
    print()


def printPleaseWait():
    print()
    print(_('please_wait'))
    print()


locale.setlocale(locale.LC_ALL, _('locale'))
parser = argparse.ArgumentParser(add_help=False)
subparsers = parser.add_subparsers(dest='command')
accountsParser = subparsers.add_parser('accounts', add_help=False)
accountsParser.add_argument('-h', '--help', action='help', default=argparse.SUPPRESS, help=_('args_help'))
transferParser = subparsers.add_parser('transfer', add_help=False)
transferParser.add_argument("from_account", type=str, help=_('args_help_from_account'))
transferParser.add_argument("to_account", type=str, help=_('args_help_to_account'))
transferParser.add_argument("amount", type=float, help=_('args_help_amount'))
transferParser.add_argument("message", type=str, default='Transferred by teller', nargs='?', help=_('args_help_message'))
transferParser.add_argument('-h', '--help', action='help', default=argparse.SUPPRESS, help=_('args_help'))
transactionsParser = subparsers.add_parser('trans', add_help=False)
transactionsParser.add_argument("account", type=str, help=_('args_help_account'))
transactionsParser.add_argument("start", type=str, default='', nargs='?', help=_('args_help_start_date'))
transactionsParser.add_argument("end", type=str, default='', nargs='?', help=_('args_help_end_date'))
transactionsParser.add_argument("index", type=int, default=0, nargs='?', help=_('args_help_index'))
transactionsParser.add_argument("quantity", type=int, default=1000, nargs='?', help=_('args_help_quantity'))
transactionsParser.add_argument("-s", "--search", help=_('args_help_search'), action="store")
transactionsParser.add_argument('-h', '--help', action='help', default=argparse.SUPPRESS, help=_('args_help'))
parser.add_argument("-a", "--anon", "--anonymize", help=_('args_help_anonymize'), action="store_true")
parser.add_argument("-l", "--lang", help=_('args_help_language'), action="store")
parser.add_argument("-v", "--verbose", help=_('args_help_verbose'), action="store_true")
parser.add_argument('-V', '--version', action='version', version='%(prog)s version ' + VERSION + '. © 2018 Roy Solberg - https://roysolberg.com.')
parser.add_argument('-h', '--help', action='help', default=argparse.SUPPRESS, help=_('args_help'))
# A little HACK as add_subparsers() makes it required to have a command (event though we want to default to 'accounts'):
commands = ['accounts', 'transfer', 'trans']
if not any(i in commands for i in sys.argv):
    sys.argv.append('accounts')
args = parser.parse_args(sys.argv[1:])


if args.lang is not None:
    if args.verbose:
        print('Setting language to [' + args.lang + '].')
    config.set('general', 'language', args.lang)
    langConfig = getLanguageConfig()
    storeConfig()


firstRun = not config.has_section('sbanken')

if firstRun:
    print()
    print(_('first_run_message'))
    print
    try:
        clientId = raw_input(_('enter_client_id') + ' ')
        clientSecret = raw_input(_('enter_client_secret') + ' ')
        userId = raw_input(_('enter_user_id') + ' ')
        print()
        print(_('password_or_pin_if_you_want_to_store_data'))
        print
        password = getpass.getpass(_('enter_password'))
    except KeyboardInterrupt:  # User pressed ctrl+c
        printShortHelp()
        exit()
    isInputValid = True
    if len(clientId) == 0:
        isInputValid = False
        print(_('invalid_client_id'))
    if len(clientSecret) == 0:
        isInputValid = False
        print(_('invalid_client_id'))
    if len(userId) == 0:
        isInputValid = False
        print(_('invalid_user_id'))
    if isInputValid:
        if len(password) >= 6:
            config.add_section('sbanken')
            aesCipher = AESCipher(password)
            config.set('sbanken', 'clientId', aesCipher.encrypt(clientId))
            config.set('sbanken', 'clientSecret', aesCipher.encrypt(clientSecret))
            config.set('sbanken', 'userId', aesCipher.encrypt(userId))
            storeConfig()
    else:
        exit()


def getAccessToken():
    global clientId, clientSecret, password
    if not firstRun:
        password = getpass.getpass(_('enter_password_2'))
        clientId = AESCipher(password).decrypt(config.get('sbanken', 'clientId'))
    printPleaseWait()
    if(config.has_option('sbanken', 'accessToken') and config.has_option('sbanken', 'accessTokenExpiration')):
        try:
            accessToken = AESCipher(password).decrypt(config.get('sbanken', 'accessToken'))
            accessTokenExpiration = int(AESCipher(password).decrypt(config.get('sbanken', 'accessTokenExpiration')))
            if int(time.time()) < accessTokenExpiration:
                # print(time.time())
                # print(accessTokenExpiration)
                if args.verbose:
                    print('Using existing access token that expires in ' + str(int((int(accessTokenExpiration) - time.time()) / 60)) + ' minutes.')
                return accessToken
        except ValueError:
            print(_('error_failed_to_decrypt_token', error=True))
            printShortHelp()
            exit()
    if not firstRun:
        clientSecret = AESCipher(password).decrypt(config.get('sbanken', 'clientSecret'))

    if args.verbose:
        print('Getting a fresh access token.')
    headers = {'Authorization': 'Basic ' + base64.b64encode(urllib.quote_plus(clientId) + ':' + urllib.quote_plus(clientSecret)), 'Accept': 'application/json'}
    response = requests.post('https://auth.sbanken.no/identityserver/connect/token', {'grant_type': 'client_credentials'}, headers=headers)
    if response.status_code == 200:
        json = response.json()
        accessToken = str(json['access_token'])
        if config.has_section('sbanken'):  # User wants to store credentials
            accessTokenExpiration = str(int(time.time()) + int(json['expires_in']))
            aesCipher = AESCipher(password)
            config.set('sbanken', 'accessToken', aesCipher.encrypt(accessToken))
            config.set('sbanken', 'accessTokenExpiration', aesCipher.encrypt(accessTokenExpiration))
            storeConfig()
        return accessToken
    else:
        print()
        print(_('error_failed_to_authenticate', response.status_code, response.content, error=True))
        printShortHelp()
        exit()
    return None


def getNiceName(name):
    if args.anon:
        if isinstance(name, unicode):
            return name[:3] + '*' * (len(name) - 3)
        else:
            return (name.decode('utf-8')[:3] + '*' * (len(name) - 3)).encode('utf-8')
    return name


def getNiceAccountNo(accountNo):
    if args.anon:
        if len(accountNo) > 4:
            accountNo = accountNo[:4] + '*' * (len(accountNo) - 4)
        else:
            accountNo = '*' * len(accountNo)
    if len(accountNo) >= 11:
        # TODO: How can this be described in a better way?
        return accountNo[:4] + '.' + accountNo[4:6] + '.' + accountNo[6:]
    return accountNo


def getNiceAmount(amount, includeCurrencySymbol):
    # Wasn't happy with the no_no currency formatting, so doing this custom thingy instead:
    if includeCurrencySymbol:
        amount = locale.format('%.2f', amount, grouping=True, monetary=True) + ' ' + _('currency_symbol')
    else:
        amount = locale.format('%.2f', amount, grouping=True, monetary=True)
    if args.anon:
        if includeCurrencySymbol:
            return ('*' * 7) + amount[-(len(' ' + _('currency_symbol')) + 4):]
        return ('*' * 7) + amount[-4:]
    return amount


def getNiceTransactionType(transactionType):
    if transactionType == 'RKI':
        return _('transfer')
    if transactionType == 'RK':
        return _('purchase')
    return transactionType.encode('utf-8')


def getAccountData():
    global userId
    if userId is None:
        userId = AESCipher(password).decrypt(config.get('sbanken', 'userId'))
    headers = {'Authorization': 'Bearer ' + accessToken, 'customerId': userId, 'Accept': 'application/json', 'Content-Type': 'application/json-patch+json', }
    response = requests.get('https://api.sbanken.no/exec.bank/api/v1/accounts', headers=headers)
    return response.json()


def printBalances():
    accountData = getAccountData()
    print('┏━━━━┳━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━┓')
    print('┃  # ┃ ' + str(_('account_number')).ljust(14) + ' ┃ ' + str(_('account_name')).ljust(25) + ' ┃ ' + str(_('bank_balance')).ljust(15) + ' ┃ ' + str(_('book_balance')).decode('utf-8').ljust(15).encode('utf-8') + ' ┃')
    print('┣━━━━╋━━━━━━━━━━━━━━━━╋━━━━━━━━━━━━━━━━━━━━━━━━━━━╋━━━━━━━━━━━━━━━━━╋━━━━━━━━━━━━━━━━━┫')
    for i, account in enumerate(accountData['items']):
        print('┃' + str(i + 1).rjust(3, ' ') + ' ┃ ' + str(getNiceAccountNo(account['accountNumber']).decode('utf-8').rjust(14, ' ').encode('utf-8')) + ' ┃ ' + getNiceName(account['name']).rjust(25, ' ').encode('utf-8') + ' ┃ ' + getNiceAmount(account['available'], True).decode('utf-8').rjust(15, ' ').encode('utf-8') + ' ┃ ' + getNiceAmount(account['balance'], True).decode('utf-8').rjust(15, ' ').encode('utf-8') + ' ┃')
    print('┗━━━━┻━━━━━━━━━━━━━━━━┻━━━━━━━━━━━━━━━━━━━━━━━━━━━┻━━━━━━━━━━━━━━━━━┻━━━━━━━━━━━━━━━━━┛')
    print()
    print('💰')


def printTransactions():
    global userId
    accounts = getAccountData()['items']
    account = getAccount(args.account, accounts)
    if account is None:
        print(_('error_unknown_account', args.account, error=True))
        exit()
    if userId is None:
        userId = AESCipher(password).decrypt(config.get('sbanken', 'userId'))
    headers = {'Authorization': 'Bearer ' + accessToken, 'customerId': userId, 'Accept': 'application/json', 'Content-Type': 'application/json-patch+json', }
    if args.start is not None and args.start != '':
        try:
            args.start = dateutil.parser.parse(args.start, fuzzy=True)
            args.start = args.start.strftime('%Y-%m-%d')
        except ValueError:
            pass
    if args.end is not None and args.end != '':
        try:
            args.end = dateutil.parser.parse(args.end, fuzzy=True)
            args.end = args.end.strftime('%Y-%m-%d')
        except ValueError:
            pass
    if args.start is not None and args.start != '' and args.end is not None and args.end != '':
        if args.start > args.end:
            temp = args.start
            args.start = args.end
            args.end = temp
        print(_('using_start_date_and_end_date', args.start, args.end))
        print()
    elif args.start is not None and args.start != '':
        print(_('using_start_date', args.start))
        print()
    params = {'index': args.index, 'length': args.quantity, 'startDate': args.start, 'endDate': args.end}
    # print account
    response = requests.get('https://api.sbanken.no/exec.bank/api/v1/transactions/' + account['accountId'], headers=headers, params=params)
    if response.status_code == 200:
        jsonObj = response.json()
        if not jsonObj['isError']:
            transactions = jsonObj['items']
            transactionsCount = len(transactions)
            if args.search is None:
                print(_('transactions_for', transactionsCount, getNiceName(account['name'].encode('utf-8')), getNiceAccountNo(account['accountNumber'])))
            else:
                print(_('searching_transactions_for', args.search, getNiceName(account['name'].encode('utf-8')), getNiceAccountNo(account['accountNumber'])))
                args.search = args.search.decode('utf-8').lower()
            print('┏━━━━━━━━━━━━┳━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━┓')
            print('┃ ' + str(_('accounting_date')).ljust(10) + ' ┃ ' + str(_('interest_date')).ljust(10) + ' ┃ ' + str(_('text')).ljust(61) + ' ┃ ' + str(_('amount')).decode('utf-8').ljust(15).encode('utf-8') + ' ┃ ' + str(_('type')).decode('utf-8').ljust(10).encode('utf-8') + ' ┃')
            print('┣━━━━━━━━━━━━╋━━━━━━━━━━━━╋━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━╋━━━━━━━━━━━━━━━━━╋━━━━━━━━━━━━┫')
            # RKI = "Overførsel"
            # RK = "Varekjøp"
            # accountingDate ser ut til å være datoen brukt på kontoutskrift
            # Kreditrente:
            # Rentedato: 01.01.2018 <-- interestDate
            # Bokført: 31.12.2017 <-- accountingDate (vises)
            incomingAmount = 0
            incomingCount = 0
            outgoingAmount = 0
            outgoingCount = 0
            for transaction in transactions:
                if args.search is None or args.search in transaction['text'].lower():
                    amount = transaction['amount']
                    print('┃ ' + dateutil.parser.parse(transaction['accountingDate']).strftime(_('date_format')).rjust(10, ' ') + ' ┃ ' + dateutil.parser.parse(transaction['interestDate']).strftime(_('date_format')).rjust(10, ' ') + ' ┃ ' + getNiceName(transaction['text'].encode('utf-8')).decode('utf-8').ljust(61).encode('utf-8') + ' ┃ ' + getNiceAmount(amount, True).decode('utf-8').rjust(15, ' ').encode('utf-8') + ' ┃ ' + getNiceTransactionType(transaction['transactionType']).decode('utf-8').ljust(10, ' ').encode('utf-8') + ' ┃')
                    if amount >= 0:
                        incomingAmount += amount
                        incomingCount += 1
                    else:
                        outgoingAmount += amount
                        outgoingCount += 1
            # str(transaction['transactionId'])
            # Always None:
            # print(str(transaction['otherAccountNumber'])
            # print(str(transaction['registrationDate'])
            totalCount = incomingCount + outgoingCount
            rJustCount = len(str(totalCount))
            print('┣━━━━━━━━━━━━╋━━━━━━━━━━━━╋━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━╋━━━━━━━━━━━━━━━━━╋━━━━━━━━━━━━┫')
            # TODO: We need support for plural
            if incomingCount == 1:
                print('┃            ┃            ┃ ' + _('incoming_transaction', str(incomingCount).rjust(rJustCount)).decode('utf-8').ljust(61).encode('utf-8') + ' ┃ ' + getNiceAmount(incomingAmount, True).decode('utf-8').rjust(15, ' ').encode('utf-8') + ' ┃            ┃')
            else:
                print('┃            ┃            ┃ ' + _('incoming_transactions', str(incomingCount).rjust(rJustCount)).decode('utf-8').ljust(61).encode('utf-8') + ' ┃ ' + getNiceAmount(incomingAmount, True).decode('utf-8').rjust(15, ' ').encode('utf-8') + ' ┃            ┃')
            if outgoingCount == 1:
                print('┃            ┃            ┃ ' + _('outgoing_transaction', str(outgoingCount).rjust(rJustCount)).decode('utf-8').ljust(61).encode('utf-8') + ' ┃ ' + getNiceAmount(outgoingAmount, True).decode('utf-8').rjust(15, ' ').encode('utf-8') + ' ┃            ┃')
            else:
                print('┃            ┃            ┃ ' + _('outgoing_transactions', str(outgoingCount).rjust(rJustCount)).decode('utf-8').ljust(61).encode('utf-8') + ' ┃ ' + getNiceAmount(outgoingAmount, True).decode('utf-8').rjust(15, ' ').encode('utf-8') + ' ┃            ┃')
            if totalCount == 1:
                print('┃            ┃            ┃ ' + _('total_transaction', str(totalCount).rjust(rJustCount)).decode('utf-8').ljust(61).encode('utf-8') + ' ┃ ' + getNiceAmount(incomingAmount + outgoingAmount, True).decode('utf-8').rjust(15, ' ').encode('utf-8') + ' ┃            ┃')
            else:
                print('┃            ┃            ┃ ' + _('total_transactions', str(totalCount).rjust(rJustCount)).decode('utf-8').ljust(61).encode('utf-8') + ' ┃ ' + getNiceAmount(incomingAmount + outgoingAmount, True).decode('utf-8').rjust(15, ' ').encode('utf-8') + ' ┃            ┃')
            print('┗━━━━━━━━━━━━┻━━━━━━━━━━━━┻━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┻━━━━━━━━━━━━━━━━━┻━━━━━━━━━━━━┛')
            if jsonObj['availableItems'] > transactionsCount:
                print()
                print(_('got_x_elements_of_y_available', transactionsCount, jsonObj['availableItems']))
                print()
            exit()
        else:
            print(_('error_transactions_listing_failed', jsonObj['errorMessage'].encode('utf-8'), error=True))
            printShortHelp()
            exit()
    else:
        print()
        print(_('error_transactions_listing_failed', response.status_code, response.content, error=True))
        printShortHelp()
        exit()


def getAccount(accountToFind, accounts):
    accountToFindCleaned = accountToFind.replace(' ', '').replace('.', '').replace('#', '').decode('utf-8')
    for i, account in enumerate(accounts):
        if accountToFindCleaned == account['accountNumber']:
            return account
        if accountToFind.decode('utf-8').lower() == account['name'].lower():
            return account
        if str(i + 1) == accountToFindCleaned:
            return account
    return None


def validateTransfer(fromAccount, toAccount):
    if fromAccount is None:
        print(_('error_unknown_account', args.from_account, error=True))
        exit()
    if args.verbose:
        print('Using from account ' + str(fromAccount))
    if toAccount is None:
        print(_('error_unknown_account', args.to_account, error=True))
        exit()
    if args.verbose:
        print('Using to account ' + str(toAccount))
    if fromAccount['accountNumber'] == toAccount['accountNumber']:
        print(_('error_from_and_to_account_cannot_be_the_same', error=True))
        exit()


def doTransfer():
    global userId
    accounts = getAccountData()['items']
    fromAccount = getAccount(args.from_account, accounts)
    toAccount = getAccount(args.to_account, accounts)
    validateTransfer(fromAccount, toAccount)
    if userId is None:
        userId = AESCipher(password).decrypt(config.get('sbanken', 'userId'))
    headers = {'Authorization': 'Bearer ' + accessToken, 'customerId': userId, 'Accept': 'application/json', 'Content-Type': 'application/json-patch+json', }
    transfer = {'fromAccountId': fromAccount['accountId'], 'toAccountId': toAccount['accountId'], 'amount': args.amount, 'message': args.message}
    response = requests.post('https://api.sbanken.no/exec.bank/api/v1/transfers', headers=headers, data=json.dumps(transfer))
    # This one gives HTTP 200 even on some errors
    if response.status_code == 200:
        jsonObj = response.json()
        if not jsonObj['isError']:
            print(_('transfer_successful', getNiceAmount(args.amount, True), getNiceAccountNo(fromAccount['accountNumber']), getNiceAccountNo(toAccount['accountNumber'])))
            exit()
        else:
            print()
            print(_('error_transfer_failed_2', jsonObj['errorMessage'].encode('utf-8'), error=True))
            printShortHelp()
            exit()
    else:
        print()
        print(_('error_transfer_failed', response.status_code, response.content, error=True))
        printShortHelp()
        exit()

    print(response.status_code)
    print(response.reason)
    print(response.headers)
    print('Content:' + str(response.content))


try:
    accessToken = getAccessToken()
except KeyboardInterrupt:  # User pressed ctrl+c
    printShortHelp()
    exit()

if args.command == 'accounts':
    printBalances()
    printShortHelp()
elif args.command == 'transfer':
    doTransfer()
elif args.command == 'trans':
    printTransactions()
