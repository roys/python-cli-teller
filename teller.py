#!/usr/bin/python
# -*- coding: utf-8 -*-
# TODO: Clean up everything :-)
import configparser
import locale
import os
from aescipher import AESCipher
import requests
import base64
import getpass
import sys

VERSION = '1.0.0'
FILENAME_CONFIG = os.path.join(os.path.dirname(
    os.path.realpath(__file__)), 'config.ini')
anonymize = False

config = configparser.ConfigParser()
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
            __file__)), 'strings_' + config.get('config', 'language') + '.ini'))
    except (configparser.NoOptionError, configparser.NoSectionError, configparser.MissingSectionHeaderError):
        pass
    return langConfig


langConfig = getLanguageConfig()


def _(key):
    if langConfig.has_option('language', key):
        return langConfig.get('language', key).replace('\\t', '    ')
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


def clean(input, *onlyParts):
    if anonymize:
        if onlyParts:
            return input[:4].ljust(len(input), '*')
        return '*' * len(input)
    return input


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
            config.set('sbanken', 'clientSecret',
                       aesCipher.encrypt(clientSecret))
            config.set('sbanken', 'userId', aesCipher.encrypt(userId))
            config.write(open(FILENAME_CONFIG, 'w'))
    else:
        exit()
else:
    print
    print _('welcome_back')
    print
    try:
        password = getpass.getpass(_('enter_password_2'))
        clientId = AESCipher(password).decrypt(
            config.get('sbanken', 'clientId'))
        clientSecret = AESCipher(password).decrypt(
            config.get('sbanken', 'clientSecret'))
        userId = AESCipher(password).decrypt(config.get('sbanken', 'userId'))
    except KeyboardInterrupt:  # User pressed ctrl+c
        printShortHelp()
        exit()

print
print 'Please wait...'
print
# print clientId
# print clientSecret
# print userId
headers = {'Authorization': 'Basic ' +
           base64.b64encode(clientId + ':' + clientSecret), 'Accept': 'application/json'}
response = requests.post('https://api.sbanken.no/identityserver/connect/token',
                         {'grant_type': 'client_credentials'}, headers=headers)

# print str(response.status_code)
# print response.content
# print response.status_code
accessToken = response.json()['access_token']
# "expires_in":3600,"token_type":"Bearer"}

if response.status_code == 200:
    headers = {'Authorization': 'Bearer ' +
               accessToken, 'Accept': 'application/json'}
    response = requests.get(
        'https://api.sbanken.no/bank/api/v1/accounts/' + userId, headers=headers)

    # print str(response.status_code)
    # print response.content
    # print response.status_code
    accountData = response.json()
    print '┏━━━━┳━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━┓'
    print '┃  # ┃ Account number     ┃ Account name              ┃ Bank balance       ┃ Book balance       ┃'
    print '┣━━━━╋━━━━━━━━━━━━━━━━━━━━╋━━━━━━━━━━━━━━━━━━━━━━━━━━━╋━━━━━━━━━━━━━━━━━━━━╋━━━━━━━━━━━━━━━━━━━━┫'
    for i, account in enumerate(accountData['items']):
        # print account
        print '┃' + str(i + 1).rjust(3, ' ') + ' ┃' + str(clean(account['accountNumber'], True).rjust(19, ' ')) + ' ┃' + clean(account['name'], True).rjust(26, ' ').encode('utf-8') + ' ┃ ' + clean(('{:,.2f}'.format(account['available'])).rjust(18, ' ')) + ' ┃ ' + clean(('{:,.2f}'.format(account['balance'])).rjust(18, ' ')) + ' ┃'
    print '┗━━━━┻━━━━━━━━━━━━━━━━━━━━┻━━━━━━━━━━━━━━━━━━━━━━━━━━━┻━━━━━━━━━━━━━━━━━━━━┻━━━━━━━━━━━━━━━━━━━━┛'
    print
    print '💰'
    printShortHelp()
else:
    # TODO
    pass
