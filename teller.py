#!/usr/bin/python
# -*- coding: utf-8 -*-
# TODO: Clean up everything :-)
import configparser
import locale
import os
import base64
import getpass
import sys
import time
import requests
from aescipher import AESCipher

VERSION = '1.0.1'
FILENAME_CONFIG = os.path.join(os.path.dirname(
    os.path.realpath(__file__)), 'config.ini')
anonymize = False

config = configparser.ConfigParser()
if not config.has_section('general'):
    config.add_section('general')
config.read(FILENAME_CONFIG)


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


def _(key, *args):
    if langConfig.has_option('language', key):
        value = langConfig.get('language', key).replace('\\t', '    ')
        for arg in args:
            value = value.replace('%s', str(arg), 1)
        return value.encode('utf-8')
    return key


def printShortHelp():
    print
    print 'Type \'teller --help\' for a list of all available commnads.'
    print


def printHelp():
    print _('help_description')


for i, arg in enumerate(sys.argv):
    if arg == '--anonymize' or arg == '--anon' or arg == '-a':
        anonymize = True
    elif arg == '--help' or arg == '-h':
        printHelp()
        exit()
    elif arg == '--version' or arg == '-v':
        print 'Version ' + VERSION + '. © 2018 Roy Solberg - https://roysolberg.com .'
        exit()
    elif arg.startswith('-l=') or arg.startswith('--lang='):
        lang = arg.split('=', 2)[1]
        if len(lang) > 0:
            config.set('general', 'language', lang)
            langConfig = getLanguageConfig()
            storeConfig()
        else:
            print _('error_specify_language')
            exit()
        pass


def getCleanOutput(input, *onlyParts):
    if anonymize:
        if onlyParts:
            return input[:4].ljust(len(input), '*').encode('utf-8')
        return '*' * len(input)
    return input.encode('utf-8')


firstRun = not config.has_section('sbanken')

if firstRun:
    print
    print _('first_run_message')
    print
    clientId = raw_input(_('enter_client_id') + ' ')
    clientSecret = raw_input(_('enter_client_secret') + ' ')
    userId = raw_input(_('enter_user_id') + ' ')
    print
    print _('password_or_pin_if_you_want_to_store_data')
    print
    global password
    password = getpass.getpass(_('enter_password'))
    isInputValid = True
    if len(clientId) == 0:
        isInputValid = False
        print _('invalid_client_id')
    if len(clientSecret) == 0:
        isInputValid = False
        print _('invalid_client_id')
    if len(userId) == 0:
        isInputValid = False
        print _('invalid_user_id')
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
else:
    print
    print _('welcome_back')
    print


def getAccessToken():
    global password
    password = getpass.getpass(_('enter_password_2'))
    clientId = AESCipher(password).decrypt(config.get('sbanken', 'clientId'))
    if(config.has_option('sbanken', 'accessToken') and config.has_option('sbanken', 'accessTokenExpiration')):
        accessToken = AESCipher(password).decrypt(config.get('sbanken', 'accessToken'))
        accessTokenExpiration = int(AESCipher(password).decrypt(config.get('sbanken', 'accessTokenExpiration')))
        if int(time.time()) < accessTokenExpiration:
            # print time.time()
            # print accessTokenExpiration
            # print 'Using existing access token that expires in ' + str((int(accessTokenExpiration) - time.time()) / 60) + ' minutes.'
            return accessToken
    clientSecret = AESCipher(password).decrypt(config.get('sbanken', 'clientSecret'))

    headers = {'Authorization': 'Basic ' + base64.b64encode(clientId + ':' + clientSecret), 'Accept': 'application/json'}
    response = requests.post('https://api.sbanken.no/identityserver/connect/token', {'grant_type': 'client_credentials'}, headers=headers)
    if response.status_code == 200:
        json = response.json()
        accessToken = json['access_token']
        accessTokenExpiration = str(int(time.time()) + int(json['expires_in']))
        aesCipher = AESCipher(password)
        config.set('sbanken', 'accessToken', aesCipher.encrypt(accessToken))
        config.set('sbanken', 'accessTokenExpiration', aesCipher.encrypt(accessTokenExpiration))
        storeConfig()
        return accessToken
    else:
        print
        print _('error_failed_to_authenticate', response.status_code, response.content)
        printShortHelp()
        exit()
    return None


try:
    accessToken = getAccessToken()
except KeyboardInterrupt:  # User pressed ctrl+c
    printShortHelp()
    exit()


def getNiceAccountNo(accountNo):
    if len(accountNo) >= 11:
        # TODO: How can this be described in a better way?
        return accountNo[:4] + '.' + accountNo[4:6] + '.' + accountNo[6:]
    return accountNo


def printBalances():
    print
    print 'Please wait...'
    print
    userId = AESCipher(password).decrypt(config.get('sbanken', 'userId'))

    headers = {'Authorization': 'Bearer ' + accessToken, 'Accept': 'application/json'}
    response = requests.get('https://api.sbanken.no/bank/api/v1/accounts/' + userId, headers=headers)
    accountData = response.json()
    print '┏━━━━┳━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━┓'
    print '┃  # ┃ ' + str(_('account_number')).ljust(14) + ' ┃ ' + str(_('account_name')).ljust(25) + ' ┃ ' + str(_('bank_balance')).ljust(15) + ' ┃ ' + str(_('book_balance')).decode('utf-8').ljust(15).encode('utf-8') + ' ┃'
    print '┣━━━━╋━━━━━━━━━━━━━━━━╋━━━━━━━━━━━━━━━━━━━━━━━━━━━╋━━━━━━━━━━━━━━━━━╋━━━━━━━━━━━━━━━━━┫'
    for i, account in enumerate(accountData['items']):
        print '┃' + str(i + 1).rjust(3, ' ') + ' ┃ ' + str(getCleanOutput(getNiceAccountNo(account['accountNumber']), True).rjust(14, ' ')) + ' ┃ ' + getCleanOutput(account['name'], True).decode('utf-8').rjust(25, ' ').encode('utf-8') + ' ┃ ' + getCleanOutput(('{:,.2f}'.format(account['available'])).rjust(15, ' ')) + ' ┃ ' + getCleanOutput(('{:,.2f}'.format(account['balance'])).rjust(15, ' ')) + ' ┃'
    print '┗━━━━┻━━━━━━━━━━━━━━━━┻━━━━━━━━━━━━━━━━━━━━━━━━━━━┻━━━━━━━━━━━━━━━━━┻━━━━━━━━━━━━━━━━━┛'
    print
    print '💰'


printBalances()
printShortHelp()
