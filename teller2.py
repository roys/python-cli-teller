from aescipher import AESCipher
import argparse
from bank.sbanken import Sbanken
from bank.demobank import DemoBank
import cmd
import configparser
import getpass
import locale
import os
import sys
import time

VERSION = '2.0.0'
FILENAME_CONFIG = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'config.ini')
COLOR_ERROR = '\033[91m'
COLOR_RESET = '\033[0m'

config = configparser.ConfigParser()
if not config.has_section('general'):
    config.add_section('general')
config.read(FILENAME_CONFIG)


def getLanguageConfig():
    defaultLanguage = locale.getdefaultlocale()[0]

    langConfig = configparser.ConfigParser()
    try:
        langConfig.read(os.path.join(os.path.dirname(
            os.path.realpath(__file__)), 'strings_v2_en.ini'))
    except (configparser.NoOptionError, configparser.NoSectionError, configparser.MissingSectionHeaderError):
        pass
    try:
        langConfig.read(os.path.join(os.path.dirname(
            os.path.realpath(__file__)), 'strings_v2_' + defaultLanguage + '.ini'))
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
        value += dictValue
    else:
        value += key
    if error:
        value += COLOR_RESET
    return value


class Teller(cmd.Cmd):
    doc_header = _('doc_header')
    undoc_header = _('undoc_header')
    misc_header = _('misc_header')

    def __init__(self, bank, verbose, anonymize):
        super().__init__()
        self.bank = bank
        self.verbose = verbose
        self.anonymize = anonymize
        self.current_directory = bank.get_id()
        self.current_directory_type = 'top_level'
        self.intro = _('connecting_to_the_bank')
        self.set_prompt()

    def printBalances(self):
        accountData = self.bank.get_account_data()
        print('┏━━━━┳━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━┓')
        print('┃  # ┃ ' + str(_('account_number')).ljust(14) + ' ┃ ' + str(_('account_name')).ljust(25) + ' ┃ ' + str(_('bank_balance')).ljust(15) + ' ┃ ' + str(_('book_balance')).decode('utf-8').ljust(15).encode('utf-8') + ' ┃')
        print('┣━━━━╋━━━━━━━━━━━━━━━━╋━━━━━━━━━━━━━━━━━━━━━━━━━━━╋━━━━━━━━━━━━━━━━━╋━━━━━━━━━━━━━━━━━┫')
        for i, account in enumerate(accountData['items']):
            print('┃' + str(i + 1).rjust(3, ' ') + ' ┃ ' + str(getNiceAccountNo(account['accountNumber']).decode('utf-8').rjust(14, ' ').encode('utf-8')) + ' ┃ ' + getNiceName(account['name']).rjust(25, ' ').encode('utf-8') + ' ┃ ' + getNiceAmount(account['available'], True).decode('utf-8').rjust(15, ' ').encode('utf-8') + ' ┃ ' + getNiceAmount(account['balance'], True).decode('utf-8').rjust(15, ' ').encode('utf-8') + ' ┃')
        print('┗━━━━┻━━━━━━━━━━━━━━━━┻━━━━━━━━━━━━━━━━━━━━━━━━━━━┻━━━━━━━━━━━━━━━━━┻━━━━━━━━━━━━━━━━━┛')
        print()
        print('💰')

    def set_prompt(self):
        self.prompt = self.bank.get_id() + '> '

    def do_cd(self, line):
        print("hello")

    def help_cd(self):
        print(_('help_cd'))

    def complete_cd(self, text, line, begidx, endidx):
        # accounts = ['text: [' + text + ']', 'line: [' + line + ']', 'begidx: [' + str(begidx) + ']', 'endidx: [' + str(endidx) + ']']
        # return accounts
        return ['bruks']

    def do_exit(self, line):
        print(_('good_bye'))
        exit()

    def help_exit(self):
        print(_('help_exit'))

    # do_EOF = do_exit
    # help_EOF = help_exit


parser = argparse.ArgumentParser(add_help=False)
subparsers = parser.add_subparsers(dest='command')
parser.add_argument("-a", "--anon", "--anonymize", "--anonymise", help=_('args_help_anonymize'), action="store_true")
parser.add_argument("-d", "--demo", help=_('args_help_demo'), action='store_true')
parser.add_argument("-l", "--lang", help=_('args_help_language'), action="store")
parser.add_argument("-r", "--reset", help=_('args_help_reset'), action='store_true')
parser.add_argument("-v", "--verbose", help=_('args_help_verbose'), action='store_true')
parser.add_argument('-V', '--version', action='version', version='%(prog)s version ' + VERSION + '. © 2018-2020 Roy Solberg - https://roysolberg.com.')
parser.add_argument('-h', '--help', action='help', default=argparse.SUPPRESS, help=_('args_help'))
args = parser.parse_args(sys.argv[1:])


if args.lang is not None:
    if args.verbose:
        print('Setting language to [' + args.lang + '].')
    config.set('general', 'language', args.lang)
    langConfig = getLanguageConfig()
    storeConfig()


def printShortHelp():
    print()
    print(_('short_help_description'))
    print()


def printPleaseWait():
    print()
    print(_('please_wait'))
    print()


bank = None

if args.demo:
    bank = DemoBank()
else:
    firstRun = not config.has_section(bank.get_id()) or args.reset
    if firstRun:
        print()
        print(_('first_run_message'))
        print
        try:
            clientId = input(_('enter_client_id') + ' ')
            clientSecret = input(_('enter_client_secret') + ' ')
            user_id = input(_('enter_user_id') + ' ')
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
            print(_('invalid_client_secret'))
        if len(user_id) == 0:
            isInputValid = False
            print(_('invalid_user_id'))
        if isInputValid:
            if len(password) >= 6:
                config.add_section(bank.get_id())
                aesCipher = AESCipher(password)
                config.set(bank.get_id(), 'clientId', aesCipher.encrypt(clientId))
                config.set(bank.get_id(), 'clientSecret', aesCipher.encrypt(clientSecret))
                config.set(bank.get_id(), 'userId', aesCipher.encrypt(user_id))
                storeConfig()
        else:
            exit()
    else:
        password = getpass.getpass(_('enter_password_2'))
        clientId = AESCipher(password).decrypt(config.get(bank.get_id(), 'clientId'))
        clientSecret = AESCipher(password).decrypt(config.get(bank.get_id(), 'clientSecret'))
        user_id = AESCipher(password).decrypt(config.get(bank.get_id(), 'userId'))
        if(config.has_option(bank.get_id(), 'accessToken') and config.has_option(bank.get_id(), 'accessTokenExpiration')):
            try:
                accessToken = AESCipher(password).decrypt(config.get(bank.get_id(), 'accessToken'))
                accessTokenExpiration = int(AESCipher(password).decrypt(config.get(bank.get_id(), 'accessTokenExpiration')))
                if int(time.time()) < accessTokenExpiration:
                    # print(time.time())
                    # print(accessTokenExpiration)
                    if args.verbose:
                        print('Using existing access token that expires in ' + str(int((int(accessTokenExpiration) - time.time()) / 60)) + ' minutes.')
                else:
                    accessToken = None
            except ValueError:
                print(_('error_failed_to_decrypt_token', error=True))
                printShortHelp()
                exit()

    try:
        accessToken = bank.getAccessToken()
    except KeyboardInterrupt:  # User pressed ctrl+c
        printShortHelp()
        exit()

    bank = Sbanken(user_id, accessToken, accessTokenExpiration)


if __name__ == '__main__':
    try:
        Teller(bank, args.verbose, args.anon).cmdloop()
    except KeyboardInterrupt:
        exit()
