from aescipher import AESCipher
import argparse
from bank.sbanken import Sbanken
from bank.demobank import DemoBank
import cmd
import configparser
import datetime
import dateutil.parser
import getpass
import locale
import os
import sys
import time

"""
TODO:
Add support for transfers - https://api.sbanken.no/exec.bank/swagger/index.html?urls.primaryName=Transfers%20v1
Add support for get_standing_orders_data + get_due_payments_data + 
Add support for paying eFaktura - https://api.sbanken.no/exec.bank/swagger/index.html?urls.primaryName=EFakturas%20v1
Demo
Anonymizing
"""

VERSION = '2.0.0'
FILENAME_CONFIG = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'config.ini')
COLOR_OK = '\033[92m'
COLOR_ERROR = '\033[91m'
COLOR_RESET = '\033[0m'
COLOR_BLUE = '\x1b[34m'

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
            __file__)), 'strings_v2_' + config.get('general', 'language') + '.ini'))
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


class Column():
    def __init__(self, text, justification='LEFT', min_width=0):
        if not isinstance(text, str):
            text = str(text)
        self.text = text
        self.width = max(min_width, 0 if text is None else len(text.replace(COLOR_ERROR, '').replace(COLOR_RESET, '')) + 2)
        self.justification = justification

    def calculate_width(self, width):
        return max(width, self.width)

    def set_width(self, width):
        self.width = width

    def __str__(self):
        if self.text is None:
            return ' ' * self.width
        extra = 9 if COLOR_RESET in self.text else 0
        if self.justification == 'RIGHT':
            return ' ' + self.text.rjust(self.width - 2 + extra, ' ') + ' '
        return ' ' + self.text.ljust(self.width - 2 + extra, ' ') + ' '


class Row():
    def __init__(self):
        self.columns = []

    def add(self, column):
        self.columns.append(column)

    def calculate_widths(self, widths):
        if widths is None:
            widths = [0] * len(self.columns)
        for i in range(len(widths)):
            try:
                widths[i] = self.columns[i].calculate_width(widths[i])
            except IndexError:
                pass
        return widths

    def set_widths(self, widths):
        for i in range(len(widths)):
            try:
                self.columns[i].set_width(widths[i])
            except IndexError:
                pass

    def __str__(self):
        output = '┃'
        for column in self.columns:
            output += str(column)
            output += '┃'
        return output


class HeaderRow(Row):
    def __init__(self):
        super().__init__()

    def __str__(self):
        output = ''
        for i, column in enumerate(self.columns):
            if i == 0:
                output += '┏'
            else:
                output += '┳'
            output += '━' * column.width
        output += '┓\n'
        output += super().__str__()
        for i, column in enumerate(self.columns):
            if i == 0:
                output += '\n┣'
            else:
                output += '╋'
            output += '━' * column.width
        output += '┫'
        return output


class Table():
    def __init__(self):
        self.rows = []

    def add(self, row):
        self.rows.append(row)

    def __str__(self):
        widths = None
        for row in self.rows:
            widths = row.calculate_widths(widths)
        output = '\n'
        last_row = None
        for row in self.rows:
            row.set_widths(widths)
            output += str(row) + '\n'
            last_row = row
        if last_row is not None:
            for i, column in enumerate(last_row.columns):
                if i == 0:
                    output += '┗'
                else:
                    output += '┻'
                output += '━' * column.width
            output += '┛'
        output += '\n'
        return output


class Teller(cmd.Cmd):
    doc_header = _('doc_header')
    undoc_header = _('undoc_header')
    misc_header = _('misc_header')

    def __init__(self, bank, verbose, anonymize):
        super().__init__()
        self.bank = bank
        self.verbose = verbose
        self.anonymize = anonymize
        self.current_directory = bank.get_name()
        self.current_directory_type = 'top_level'
        self.current_account = None
        print(_('connecting_to_the_bank'))
        self.print_balances()
        self.set_prompt()
        self.aliases = {'dir': self.do_ls,
                        'list': self.do_ls,
                        'll': self.do_ls,
                        'q': self.do_exit,
                        'quit': self.do_exit,
                        'w': self.do_whoami,
                        'h': self.do_help,
                        '?': self.do_help}

    def default(self, line):
        cmd, arg, line = self.parseline(line)
        if cmd in self.aliases:
            self.aliases[cmd](arg)
        else:
            print("*** Unknown syntax: %s" % line)

    def get_nice_account_no(self, accountNo):
        if args.anon:
            if len(accountNo) > 4:
                accountNo = accountNo[:4] + '*' * (len(accountNo) - 4)
            else:
                accountNo = '*' * len(accountNo)
        if len(accountNo) >= 11:
            # TODO: How can this be described in a better way?
            return accountNo[:4] + '.' + accountNo[4:6] + '.' + accountNo[6:]
        return accountNo

    def get_nice_name(self, name):
        if args.anon:
            return name[:3] + '*' * (len(name) - 3)
        return name

    def get_nice_amount(self, amount, includeCurrencySymbol=True):
        # Wasn't happy with the no_no currency formatting, so doing this custom thingy instead:
        if includeCurrencySymbol:
            amount = locale.format_string('%.2f', amount, grouping=True, monetary=True) + ' ' + _('currency_symbol')
        else:
            amount = locale.format_string('%.2f', amount, grouping=True, monetary=True)
        if args.anon:
            if includeCurrencySymbol:
                return ('*' * 7) + amount[-(len(' ' + _('currency_symbol')) + 4):]
            return ('*' * 7) + amount[-4:]
        return amount

    def get_nice_transaction_type(self, transactionType):
        value = _('transfer_' + transactionType)
        if value.startswith('transfer_'): # No translation available - return type as-is
            return transactionType
        return value

    def get_nice_date(self, date_str, red_if_overdue=False):
        if red_if_overdue:
            now = datetime.datetime.now(datetime.timezone.utc)
            due_day = dateutil.parser.parse(date_str)
            diff = due_day - now
            if diff.days < 0:
                return COLOR_ERROR + due_day.strftime(_('date_format')) + COLOR_RESET
        return dateutil.parser.parse(date_str).strftime(_('date_format'))

    def get_nice_expiry_date(self, date_str):
        return dateutil.parser.parse(date_str).strftime(_('date_format_expiry'))

    def get_nice_card_product(self, product):
        if product == 'DebitCard' or product == 'DebitCardCL':
            return _('debit')
        if product == 'CreditCard' or product == 'CreditCardCL':
            return _('credit')
        return product

    def get_nice_card_status(self, status):
        if status == 'Active':
            return COLOR_OK + _('active') + COLOR_RESET
        if status == 'Deleted':
            return COLOR_ERROR + _('deleted') + COLOR_RESET
        return status

    def get_nice_card_owner(self, owner_id):
        if owner_id == self.bank.user_id:
            return _('owner_you')
        return owner_id[0:6]

    def get_nice_efaktura_type(self, efaktura_type):
        value = _('efaktura_type_' + efaktura_type)
        if value.startswith('efaktura_type_'): # No translation available - return type as-is
            return efaktura_type
        return value

    def get_nice_efaktura_status(self, status):
        value = _('efaktura_status_' + status)
        if value.startswith('efaktura_status_'): # No translation available - return type as-is
            return status
        if status == 'PROCESSED':
            return COLOR_OK + value + COLOR_RESET
        if status == 'NEW':
            return COLOR_BLUE + value + COLOR_RESET
        return value

    def get_nice_payment_status(self, status1, status2):
        if status1 == 'Active' and status2 == 'Active':
            return _('active')
        if status1 == 'Active' and status2 == 'NoFunds':
            return COLOR_ERROR + _('no_funds') + COLOR_RESET
        if status1 == status2:
            return status1
        return status1 + '/' + status2

    def get_nice_payment_type(self, type1, type2):
        if type1 == 'Nettgiro' and type2 == 'Efaktura':
            return _('efaktura')
        if type1 == 'StandingOrder' and type2 == 'TransferBetweenPayersOwnAccounts':
            return _('transfer')
        if type1 == 'Avtalegiro':
            return _('avtalegiro')
        if type1 == 'Nettgiro' and type2 == 'PaymentWithStatement':
            return _('invoice')
        if type1 == 'Loan':
            return _('loan')
        return type1

    def get_ttl_hash(self, seconds=10):
        """Return the same value withing `seconds` time period"""
        return round(time.time() / seconds)

    def print_balances(self):
        accountData = self.bank.get_account_data(ttl_hash=self.get_ttl_hash())
        table = Table()
        header_row = HeaderRow()
        header_row.add(Column('#'))
        header_row.add(Column(_('account_number')))
        header_row.add(Column(_('account_name')))
        header_row.add(Column(_('bank_balance')))
        header_row.add(Column(_('book_balance')))
        table.add(header_row)
        for i, account in enumerate(accountData['items']):
            row = Row()
            row.add(Column(i + 1))
            row.add(Column(self.get_nice_account_no(account['accountNumber'])))
            row.add(Column(self.get_nice_name(account['name'])))
            row.add(Column(self.get_nice_amount(account['available']), justification='RIGHT'))
            row.add(Column(self.get_nice_amount(account['balance']), justification='RIGHT'))
            table.add(row)
        print(table)

    def print_transactions(self):
        transactions_data = self.bank.get_transactions_data(self.current_account['accountId'], ttl_hash=self.get_ttl_hash())
        table = Table()
        header_row = HeaderRow()
        header_row.add(Column(_('accounting_date')))
        header_row.add(Column(_('interest_date')))
        header_row.add(Column(_('text'), min_width=61))
        header_row.add(Column(_('amount')))
        header_row.add(Column(_('type')))
        table.add(header_row)
        for payment in transactions_data['items']:
            row = Row()
            row.add(Column(self.get_nice_date(payment['accountingDate'])))
            row.add(Column(self.get_nice_date(payment['interestDate'])))
            row.add(Column(payment['text']))
            row.add(Column(self.get_nice_amount(payment['amount']), justification='RIGHT'))
            row.add(Column(self.get_nice_transaction_type(payment['transactionType'])))
            table.add(row)
        print(table)
        pass

    def print_cards(self):
        card_data = self.bank.get_card_data(ttl_hash=self.get_ttl_hash())
        account_data = self.bank.get_account_data(ttl_hash=self.get_ttl_hash())
        table = Table()
        header_row = HeaderRow()
        header_row.add(Column('#'))
        header_row.add(Column(_('account_number')))
        header_row.add(Column(_('account_name')))
        header_row.add(Column(_('card_number')))
        header_row.add(Column(_('expiry_date')))
        header_row.add(Column(_('card_type')))
        header_row.add(Column(_('card_owner')))
        header_row.add(Column(_('status')))
        table.add(header_row)
        for i, card in enumerate(card_data['items']):
            account_name = ''
            for j, account in enumerate(account_data['items']):
                if card['accountNumber'] == account['accountNumber']:
                    account_name = self.get_nice_name(account['name'])
                    break
            row = Row()
            row.add(Column(i + 1))
            row.add(Column(self.get_nice_account_no(card['accountNumber'])))
            row.add(Column(account_name))
            row.add(Column(card['cardNumber']))
            row.add(Column(self.get_nice_expiry_date(card['expiryDate'])))
            row.add(Column(self.get_nice_card_product(card['productCode'])))
            row.add(Column(self.get_nice_card_owner(card['customerId'])))
            row.add(Column(self.get_nice_card_status(card['status'])))
            table.add(row)
        print(table)

    def print_due_payments(self):
        if self.current_account:
            self.print_due_payments_for_account(self.current_account['accountId'])
        else:
            account_data = self.bank.get_account_data(ttl_hash=self.get_ttl_hash())
            for account in account_data['items']:
                self.print_due_payments_for_account(account['accountId'])

    def print_due_payments_for_account(self, account_id):
        payments_data = self.bank.get_due_payments_data(account_id, ttl_hash=self.get_ttl_hash())
        if len(payments_data['items']) == 0:
            return
        table = Table()
        header_row = HeaderRow()
        header_row.add(Column(_('due_date')))
        header_row.add(Column(_('recipient'), min_width=25))
        header_row.add(Column(_('account_number')))
        header_row.add(Column(_('amount')))
        header_row.add(Column(_('kid_number')))
        header_row.add(Column(_('text')))
        header_row.add(Column(_('status')))
        header_row.add(Column(_('type')))
        table.add(header_row)
        for payment in payments_data['items']:
            row = Row()
            row.add(Column(self.get_nice_date(payment['dueDate'], red_if_overdue=True)))
            row.add(Column(payment['beneficiaryName']))
            row.add(Column(self.get_nice_account_no(payment['recipientAccountNumber'])))
            row.add(Column(self.get_nice_amount(payment['amount']), justification='RIGHT'))
            row.add(Column(payment['kid']))
            row.add(Column(payment['text'].strip() if(payment['text'] is not None and payment['text'] != payment['beneficiaryName']) else ''))
            row.add(Column(self.get_nice_payment_status(payment['status'], payment['statusDetails'])))
            row.add(Column(self.get_nice_payment_type(payment['productType'], payment['paymentType'])))
            table.add(row)
        print(table)

    def print_efaktura(self):
        efaktura_data = self.bank.get_efaktura_data(ttl_hash=self.get_ttl_hash())
        table = Table()
        header_row = HeaderRow()
        header_row.add(Column('#'))
        header_row.add(Column(_('due_date')))
        header_row.add(Column(_('recipient')))
        header_row.add(Column(_('amount')))
        header_row.add(Column(_('efaktura_type')))
        header_row.add(Column(_('status')))
        table.add(header_row)
        for i, efaktura in enumerate(efaktura_data['items']):
            row = Row()
            row.add(Column(i + 1))
            row.add(Column(self.get_nice_date(efaktura['originalDueDate'])))
            row.add(Column(efaktura['issuerName']))
            if efaktura['updatedAmount']:
                row.add(Column('* ' + self.get_nice_amount(efaktura['updatedAmount'], True), justification='RIGHT'))
            else:
                row.add(Column(self.get_nice_amount(efaktura['originalAmount'], True), justification='RIGHT'))
            row.add(Column(self.get_nice_efaktura_type(efaktura['documentType'])))
            row.add(Column(self.get_nice_efaktura_status(efaktura['status'])))
            table.add(row)
        print(table)

    def set_prompt(self):
        self.prompt = self.current_directory + '> '

    def do_cd(self, line):
        if len(line) == 0:
            return
        accounts = self.bank.get_account_data(ttl_hash=self.get_ttl_hash())
        if accounts and accounts['items']:
            for i, account in enumerate(accounts['items']):
                if account['name'].lower() == line.lower() or self.get_nice_account_no(account['accountNumber']) == line or account['accountNumber'] == line or (line.isdigit() and int(line) == i + 1):
                    self.current_directory = account['name']
                    self.current_directory_type = 'account'
                    self.current_account = account
                    self.set_prompt()
                    return
        if _('cards').lower() == line.lower():
            if self.current_account:
                self.current_directory = self.current_account['name'] + '/' + _('cards')
            else:
                self.current_directory = _('cards')
            self.current_directory_type = 'cards'
        if _('cards').lower() == line.lower():
            if self.current_account:
                self.current_directory = self.current_account['name'] + '/' + _('cards')
            else:
                self.current_directory = _('cards')
            self.current_directory_type = 'cards'
        if _('standing_orders').lower() == line.lower():
            if self.current_account:
                self.current_directory = self.current_account['name'] + '/' + _('standing_orders')
            else:
                self.current_directory = _('standing_orders')
            self.current_directory_type = 'standing_orders'
        if _('due_payments').lower() == line.lower():
            if self.current_account:
                self.current_directory = self.current_account['name'] + '/' + _('due_payments')
            else:
                self.current_directory = _('due_payments')
            self.current_directory_type = 'due_payments'
        if _('efaktura').lower() == line.lower():
            self.current_directory = _('efaktura')
            self.current_directory_type = 'efaktura'
            self.current_account = None
        if '..' == line:
            if self.current_directory_type == 'account' or self.current_account is None:
                self.current_directory = bank.get_name()
                self.current_directory_type = 'top_level'
                self.current_account = None
            else:
                self.current_directory = self.current_account['name']
                self.current_directory_type = 'account'
        self.set_prompt()

    def help_cd(self):
        print(_('help_cd'))

    def complete_cd(self, text, line, begidx, endidx):
        # accounts = ['text: [' + text + ']', 'line: [' + line + ']', 'begidx: [' + str(begidx) + ']', 'endidx: [' + str(endidx) + ']']
        complete = []
        if self.current_directory_type != 'top_level' and (len(text) == 0 or '..'.startswith(text)):
            complete.append('..')
        accounts = self.bank.get_account_data(ttl_hash=self.get_ttl_hash())
        if accounts and accounts['items']:
            for account in accounts['items']:
                if len(text) == 0:
                    complete.append(account['name'])
                elif self.get_nice_account_no(account['accountNumber']).startswith(text):
                    complete.append(self.get_nice_account_no(account['accountNumber']))
                elif account['accountNumber'].startswith(text):
                    complete.append(self.get_nice_account_no(account['accountNumber']))
                elif account['name'].lower().startswith(text.lower()):
                    complete.append(account['name'])
        if len(text) == 0 or _('cards').lower().startswith(text.lower()):
            complete.append(_('cards'))
        if len(text) == 0 or _('efaktura').lower().startswith(text.lower()):
            complete.append(_('efaktura'))
        if len(text) == 0 or _('standing_orders').lower().startswith(text.lower()):
            complete.append(_('standing_orders'))
        if len(text) == 0 or _('due_payments').lower().startswith(text.lower()):
            complete.append(_('due_payments'))
        return complete

    def do_ls(self, line):
        if self.current_directory_type == 'top_level':
            self.print_balances()
            # TODO
        elif self.current_directory_type == 'account':
            self.print_transactions()
        elif self.current_directory_type == 'efaktura':
            self.print_efaktura()
        elif self.current_directory_type == 'cards':
            self.print_cards()
        elif self.current_directory_type == 'due_payments':
            self.print_due_payments()

    def help_ls(self):
        print(_('help_ls'))

    def complete_ls(self):
        pass

    complete_dir = complete_ls
    complete_list = complete_ls

    def do_whoami(self, line):
        customer = self.bank.get_customer_info(ttl_hash=self.get_ttl_hash())['item']
        print()
        print('%s %s' % (customer['firstName'], customer['lastName']))
        if customer['postalAddress']['addressLine1']:
            print('%s' % customer['postalAddress']['addressLine1'])
        if customer['postalAddress']['addressLine2']:
            print('%s' % customer['postalAddress']['addressLine2'])
        if customer['postalAddress']['addressLine3']:
            print('%s' % customer['postalAddress']['addressLine3'])
        if customer['postalAddress']['addressLine4']:
            print('%s' % customer['postalAddress']['addressLine4'])
        print()
        print('%s' % customer['emailAddress'])
        print('%s' % customer['phoneNumbers'][0]['number'])
        print()

    def help_whoami(self):
        print(_('help_whoami'))

    def do_exit(self, line):
        print(_('good_bye'))
        return -1

    def help_exit(self):
        print(_('help_exit'))

    # do_EOF = do_exit
    # help_EOF = help_exit


locale.setlocale(locale.LC_ALL, _('locale'))
parser = argparse.ArgumentParser(add_help=False)
subparsers = parser.add_subparsers(dest='command')
parser.add_argument("-a", "--anon", "--anonymize", "--anonymise", help=_('args_help_anonymize'), action="store_true")
parser.add_argument("-d", "--demo", help=_('args_help_demo'), action='store_true')
parser.add_argument("-l", "--lang", help=_('args_help_language'), action="store")
parser.add_argument("-r", "--reset", help=_('args_help_reset'), action='store_true')
parser.add_argument("-v", "--verbose", help=_('args_help_verbose'), action='store_true')
parser.add_argument("--raw", help=_('args_help_raw'), action='store_true')
copyright_year = str(max(datetime.datetime.now().year, 2021))
parser.add_argument('-V', '--version', action='version', version='%(prog)s version ' + VERSION + '. © 2018-' + copyright_year + ' Roy Solberg - https://roysolberg.com.')
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
aesCipher = None

if args.demo:
    bank = DemoBank()
else:
    bank = Sbanken()
    firstRun = not config.has_section(bank.get_id()) or args.reset
    if firstRun:
        print()
        print(_('first_run_message'))
        print
        try:
            client_id = input(_('enter_client_id') + ' ')
            client_secret = input(_('enter_client_secret') + ' ')
            user_id = input(_('enter_user_id') + ' ')
            print()
            print(_('password_or_pin_if_you_want_to_store_data'))
            print
            password = getpass.getpass(_('enter_password'))
        except KeyboardInterrupt:  # User pressed ctrl+c
            printShortHelp()
            exit()
        isInputValid = True
        if len(client_id) == 0:
            isInputValid = False
            print(_('invalid_client_id'))
        if len(client_secret) == 0:
            isInputValid = False
            print(_('invalid_client_secret'))
        if len(user_id) == 0:
            isInputValid = False
            print(_('invalid_user_id'))
        if isInputValid:
            if len(password) >= 6:
                config.add_section(bank.get_id())
                aesCipher = AESCipher(password)
                config.set(bank.get_id(), 'clientId', aesCipher.encrypt(client_id))
                config.set(bank.get_id(), 'clientSecret', aesCipher.encrypt(client_secret))
                config.set(bank.get_id(), 'userId', aesCipher.encrypt(user_id))
                storeConfig()
        else:
            exit()
    else:
        password = getpass.getpass(_('enter_password_2'))
        aesCipher = AESCipher(password)
        client_id = aesCipher.decrypt(config.get(bank.get_id(), 'clientId'))
        client_secret = aesCipher.decrypt(config.get(bank.get_id(), 'clientSecret'))
        user_id = aesCipher.decrypt(config.get(bank.get_id(), 'userId'))
        if(config.has_option(bank.get_id(), 'accessToken') and config.has_option(bank.get_id(), 'accessTokenExpiration')):
            try:
                access_token = aesCipher.decrypt(config.get(bank.get_id(), 'accessToken'))
                access_token_expiration = int(aesCipher.decrypt(config.get(bank.get_id(), 'accessTokenExpiration')))
                if int(time.time()) >= access_token_expiration:
                    access_token = None
                    access_token_expiration = None
            except (ValueError, UnicodeDecodeError):
                print(_('error_failed_to_decrypt_token', error=True))
                printShortHelp()
                exit()
    bank = Sbanken(client_id, client_secret, user_id, access_token, access_token_expiration, _, args.verbose, args.raw)

if __name__ == '__main__':
    try:
        teller = Teller(bank, args.verbose, args.anon)
        teller.cmdloop()
    except KeyboardInterrupt:
        pass
    if not args.demo:
        config.set(bank.get_id(), 'accessToken', aesCipher.encrypt(bank.access_token))
        config.set(bank.get_id(), 'accessTokenExpiration', aesCipher.encrypt(str(bank.access_token_expiration)))
        storeConfig()
