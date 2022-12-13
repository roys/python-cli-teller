from .exception import ApiException
from .ibank import IBank
from functools import lru_cache
import base64
import requests
import time
import urllib
import json
from debug import debug

def _(key, *args, **kwargs):
    pass


class Sbanken(IBank):
    def __init__(self, client_id=None, client_secret=None, user_id=None, access_token=None, access_token_expiration=None, user_agent = None, dictionary=None, verbose=False, print_raw_data=False):
        super().__init__()
        self.client_id = client_id
        self.client_secret = client_secret
        self.user_id = user_id
        self.access_token = access_token
        self.access_token_expiration = access_token_expiration
        self.verbose = verbose
        self.print_raw_data = print_raw_data
        self.session = requests.Session()
        if user_agent is not None:
            self.session.headers.update({'User-Agent': user_agent})
        global _
        _ = dictionary
        debug(f'Using User-Agent [{user_agent}]')

    @staticmethod
    def get_id():
        return 'sbanken'

    def get_name(self):
        return 'Sbanken'


    def print_raw_response_if_applicable(self, response):
        if not self.print_raw_data:
            return
        print(response)
        try:
            print(json.dumps(response.json(), indent=4, sort_keys=True))
        except json.JSONDecodeError:
            print(response.text)
            pass


    @lru_cache(maxsize=1)
    def get_customer_info(self, ttl_hash=None):
        if self.verbose:
            print('Fetching customer info...')
        headers = {'Authorization': 'Bearer ' + self.get_access_token(), 'customerId': self.user_id, 'Accept': 'application/json', 'Content-Type': 'application/json-patch+json'}
        response = self.session.get('https://publicapi.sbanken.no/apibeta/api/v2/customers', headers=headers)
        self.print_raw_response_if_applicable(response)
        return response.json()

    def get_access_token(self):
        if self.access_token is not None and self.access_token_expiration is not None and int(time.time()) < self.access_token_expiration:
            if self.verbose:
                print('Using existing access token that expires in ' + str(int((int(self.access_token_expiration) - time.time()) / 60)) + ' minutes.')
            return self.access_token
        debug('Getting a fresh access token.')
        headers = {'Authorization': 'Basic ' + base64.b64encode((urllib.parse.quote_plus(self.client_id) + ':' + urllib.parse.quote_plus(self.client_secret)).encode('utf-8')).decode('utf-8'), 'Accept': 'application/json'}
        response = self.session.post('https://auth.sbanken.no/identityserver/connect/token', {'grant_type': 'client_credentials'}, headers=headers)
        self.print_raw_response_if_applicable(response)
        if response.status_code == 200:
            parsed = response.json()
            debug('Got scopes %s.' % parsed['scope'])
            self.access_token = str(parsed['access_token'])
            self.access_token_expiration = int(time.time()) + int(parsed['expires_in'])
            return self.access_token
        else:
            # TODO: Add info that {"error":"invalid_client"} means that user probably have to set up client again
            print()
            print(_('error_failed_to_authenticate', response.status_code, response.content.decode('utf-8'), error=True))
        return None

    @lru_cache(maxsize=1)
    def get_account_data(self, ttl_hash=None):
        if self.verbose:
            print('Fetching account data...')
        headers = {'Authorization': 'Bearer ' + self.get_access_token(), 'customerId': self.user_id, 'Accept': 'application/json', 'Content-Type': 'application/json-patch+json', }
        response = self.session.get('https://publicapi.sbanken.no/apibeta/api/v2/accounts', headers=headers)
        self.print_raw_response_if_applicable(response)
        return response.json()

    @lru_cache(maxsize=10)
    def get_transactions_data(self, accountId, ttl_hash=None):
        if self.verbose:
            print('Fetching transactions data for account [%s]...' % accountId)
        headers = {'Authorization': 'Bearer ' + self.get_access_token(), 'customerId': self.user_id, 'Accept': 'application/json', 'Content-Type': 'application/json-patch+json', }
        response = self.session.get('https://publicapi.sbanken.no/apibeta/api/v2/transactions/%s' % accountId, headers=headers)
        self.print_raw_response_if_applicable(response)
        return response.json()

    @lru_cache(maxsize=10)
    def get_transactions_data_by_search(self, accountId, start_date, end_date, ttl_hash=None):
        params = {'index': 0, 'length': 1000, 'startDate': start_date, 'endDate': end_date}
        if self.verbose:
            print('Fetching transactions data using params %s' % params)
        headers = {'Authorization': 'Bearer ' + self.get_access_token(), 'customerId': self.user_id, 'Accept': 'application/json', 'Content-Type': 'application/json-patch+json', }
        response = self.session.get('https://publicapi.sbanken.no/apibeta/api/v2/transactions/%s' % accountId, headers=headers, params=params)
        self.print_raw_response_if_applicable(response)
        return response.json()

    @lru_cache(maxsize=10)
    def get_standing_orders_data(self, accountId, ttl_hash=None):
        if self.verbose:
            print('Fetching standing orders for account [%s]...' % accountId)
        headers = {'Authorization': 'Bearer ' + self.get_access_token(), 'customerId': self.user_id, 'Accept': 'application/json', 'Content-Type': 'application/json-patch+json', }
        response = self.session.get('https://publicapi.sbanken.no/apibeta/api/v2/standingorders/%s' % accountId, headers=headers)
        self.print_raw_response_if_applicable(response)
        return response.json()

    @lru_cache(maxsize=10)
    def get_due_payments_data(self, accountId, ttl_hash=None):
        if self.verbose:
            print('Fetching due payments for account [%s]...' % accountId)
        headers = {'Authorization': 'Bearer ' + self.get_access_token(), 'customerId': self.user_id, 'Accept': 'application/json', 'Content-Type': 'application/json-patch+json', }
        response = self.session.get('https://publicapi.sbanken.no/apibeta/api/v2/payments/%s' % accountId, headers=headers)
        self.print_raw_response_if_applicable(response)
        if response.status_code == 200:
            # TODO: Eh, why is the order seemingly random and not by date?
            #return response.json()
            parsed = response.json()
            parsed['items'].sort(key=lambda x: x['dueDate'], reverse=False)
            return parsed
        else:
            raise ApiException(response.status_code, response.text, response.headers, response.reason)

    @lru_cache(maxsize=1)
    def get_card_data(self, ttl_hash=None):
        if self.verbose:
            print('Fetching card data...')
        headers = {'Authorization': 'Bearer ' + self.get_access_token(), 'customerId': self.user_id, 'Accept': 'application/json', 'Content-Type': 'application/json-patch+json', }
        response = self.session.get('https://publicapi.sbanken.no/apibeta/api/v2/cards', headers=headers)
        self.print_raw_response_if_applicable(response)
        if response.status_code == 200:
            return response.json()
        else:
            raise ApiException(response.status_code, response.text, response.headers, response.reason)

    @lru_cache(maxsize=1)
    def get_efaktura_data(self, ttl_hash=None):
        if self.verbose:
            print('Fetching eFaktura data...')
        headers = {'Authorization': 'Bearer ' + self.get_access_token(), 'customerId': self.user_id, 'Accept': 'application/json', 'Content-Type': 'application/json-patch+json', }
        response = self.session.get('https://publicapi.sbanken.no/apibeta/api/v2/efaktura', headers=headers)
        self.print_raw_response_if_applicable(response)
        if response.status_code == 200:
            return response.json()
        else:
            raise ApiException(response.status_code, response.text, response.headers, response.reason)


    @lru_cache(maxsize=1)
    def get_inbox(self, ttl_hash=None):
        if self.verbose:
            print('Fetching inbox messages...')
        headers = {'Authorization': 'Bearer ' + self.get_access_token(), 'customerId': self.user_id, 'Accept': 'application/json', 'Content-Type': 'application/json-patch+json', }
        response = self.session.get('https://publicapi.sbanken.no/apibeta/api/v2/mailbox/inbox', headers=headers)
        self.print_raw_response_if_applicable(response)
        if response.status_code == 200:
            return response.json()
        else:
            raise ApiException(response.status_code, response.text, response.headers, response.reason)


    @lru_cache(maxsize=1)
    def get_inbox_message(self, id, ttl_hash=None):
        if self.verbose:
            print('Fetching inbox message %s...' % id)
        headers = {'Authorization': 'Bearer ' + self.get_access_token(), 'customerId': self.user_id, 'Accept': 'application/json', 'Content-Type': 'application/json-patch+json', }
        response = self.session.get('https://publicapi.sbanken.no/apibeta/api/v2/mailbox/inbox/%s' % id, headers=headers)
        self.print_raw_response_if_applicable(response)
        if response.status_code == 200:
            message = response.json()
            if(message['status'] == 0): # Message was unread - until now
                self.mark_inbox_message_as_read(id)
            return message
        else:
            raise ApiException(response.status_code, response.text, response.headers, response.reason)

    def mark_inbox_message_as_read(self, id):
        headers = {'Authorization': 'Bearer ' + self.get_access_token(), 'customerId': self.user_id, 'Accept': 'application/json', 'Content-Type': 'application/json-patch+json', }
        response = self.session.put('https://publicapi.sbanken.no/apibeta/api/v2/mailbox/inbox/%s/readstatus' % id, headers=headers, data='{"status":1}')
        if self.print_raw_data:
            print(response)


    @lru_cache(maxsize=1)
    def get_archive(self, ttl_hash=None):
        if self.verbose:
            print('Fetching archive messages...')
        headers = {'Authorization': 'Bearer ' + self.get_access_token(), 'customerId': self.user_id, 'Accept': 'application/json', 'Content-Type': 'application/json-patch+json', }
        response = self.session.get('https://publicapi.sbanken.no/apibeta/api/v2/mailbox/archive', headers=headers)
        self.print_raw_response_if_applicable(response)
        if response.status_code == 200:
            return response.json()
        else:
            raise ApiException(response.status_code, response.text, response.headers, response.reason)


    @lru_cache(maxsize=1)
    def get_archive_message(self, id, ttl_hash=None):
        if self.verbose:
            print('Fetching inbox message %s...' % id)
        headers = {'Authorization': 'Bearer ' + self.get_access_token(), 'customerId': self.user_id, 'Accept': 'application/json', 'Content-Type': 'application/json-patch+json', }
        response = self.session.get('https://publicapi.sbanken.no/apibeta/api/v2/mailbox/archive/%s' % id, headers=headers)
        self.print_raw_response_if_applicable(response)
        if response.status_code == 200:
            message = response.json()
            if(message['status'] == 0): # Message was unread - until now
                self.mark_archive_message_as_read(id)
            return message
        else:
            raise ApiException(response.status_code, response.text, response.headers, response.reason)


    def mark_archive_message_as_read(self, id):
        headers = {'Authorization': 'Bearer ' + self.get_access_token(), 'customerId': self.user_id, 'Accept': 'application/json', 'Content-Type': 'application/json-patch+json', }
        response = self.session.put('https://publicapi.sbanken.no/apibeta/api/v2/mailbox/archive/%s/readstatus' % id, headers=headers, data='{"status":1}')
        if self.print_raw_data:
            self.print_raw_response_if_applicable(response)


    def do_transfer(self, from_account, to_account, amount, message):
        headers = {'Authorization': 'Bearer ' + self.get_access_token(), 'customerId': self.user_id, 'Accept': 'application/json', 'Content-Type': 'application/json-patch+json', }
        if not message:
            message = _('transferred_by_teller') # TODO: validate message
        message = self.get_valid_message(message)
        transfer = {'fromAccountId': from_account, 'toAccountId': to_account, 'amount': amount, 'message': message}
        if self.verbose:
            print('Sending transfer %s...' % json.dumps(transfer))
        response = self.session.post('https://publicapi.sbanken.no/apibeta/api/v2/transfers', headers=headers, data=json.dumps(transfer))
        self.print_raw_response_if_applicable(response)
        if response.status_code == 204:
            return
        else:
            raise ApiException(response.status_code, response.text, response.headers, response.reason)

    ALLOWED_CHARS = '1234567890aAbBcCdDeEfFgGhHiIjJkKlLmMnNoOpPqQrRsStTuUvVwWxXyYzZæÆøØåÅäÄëËïÏöÖüÜÿâÂêÊîÎôÔûÛãÃñÑõÕàÀèÈìÌòÒùÙáÁéÉíÍóÓýÝ,;.:!-/()? '
    def get_valid_message(self, message):
        if not message: # Won't happen
            return 'Transferred by teller'
        clean_message = ''
        for l in message:
            if l in self.ALLOWED_CHARS:
                clean_message += l
            else:
                clean_message += ' '
        return clean_message.strip()[:30]
