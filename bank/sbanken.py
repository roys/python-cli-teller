from .exception import ApiException
from .ibank import IBank
from functools import lru_cache
import base64
import requests
import time
import urllib
import json


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
        _ = dictionary
        if self.verbose:
            print('Using User-Agent [%s]' % user_agent)

    def get_id(self):
        return 'sbanken'

    def get_name(self):
        return 'Sbanken'

    @lru_cache(maxsize=1)
    def get_customer_info(self, ttl_hash=None):
        if self.verbose:
            print('Fetching customer info...')
        headers = {'Authorization': 'Bearer ' + self.get_access_token(), 'customerId': self.user_id, 'Accept': 'application/json', 'Content-Type': 'application/json-patch+json'}
        response = self.session.get('https://publicapi.sbanken.no/apibeta/api/v2/customers', headers=headers)
        if self.print_raw_data:
            print(response)
            print(json.dumps(response.json(), indent=4, sort_keys=True))
        return response.json()

    def get_access_token(self):
        if self.access_token is not None and self.access_token_expiration is not None and int(time.time()) < self.access_token_expiration:
            if self.verbose:
                print('Using existing access token that expires in ' + str(int((int(self.access_token_expiration) - time.time()) / 60)) + ' minutes.')
            return self.access_token
        if self.verbose:
            print('Getting a fresh access token.')
        headers = {'Authorization': 'Basic ' + base64.b64encode((urllib.parse.quote_plus(self.client_id) + ':' + urllib.parse.quote_plus(self.client_secret)).encode('utf-8')).decode('utf-8'), 'Accept': 'application/json'}
        response = self.session.post('https://auth.sbanken.no/identityserver/connect/token', {'grant_type': 'client_credentials'}, headers=headers)
        if self.print_raw_data:
            print(response.status_code)
            print(response)
            print(json.dumps(response.json(), indent=4, sort_keys=True))
        if response.status_code == 200:
            parsed = response.json()
            if self.verbose:
                print('Got scopes %s.' % parsed['scope'])
            self.access_token = str(parsed['access_token'])
            self.access_token_expiration = int(time.time()) + int(parsed['expires_in'])
            return self.access_token
        else:
            print()
            print(_('error_failed_to_authenticate', response.status_code, response.content, error=True))
        return None

    @lru_cache(maxsize=1)
    def get_account_data(self, ttl_hash=None):
        if self.verbose:
            print('Fetching account data...')
        headers = {'Authorization': 'Bearer ' + self.get_access_token(), 'customerId': self.user_id, 'Accept': 'application/json', 'Content-Type': 'application/json-patch+json', }
        response = self.session.get('https://publicapi.sbanken.no/apibeta/api/v2/accounts', headers=headers)
        if self.print_raw_data:
            print(response)
            print(json.dumps(response.json(), indent=4, sort_keys=True))
        return response.json()

    @lru_cache(maxsize=10)
    def get_transactions_data(self, accountId, ttl_hash=None):
        if self.verbose:
            print('Fetching transactions data for account [%s]...' % accountId)
        headers = {'Authorization': 'Bearer ' + self.get_access_token(), 'customerId': self.user_id, 'Accept': 'application/json', 'Content-Type': 'application/json-patch+json', }
        response = self.session.get('https://publicapi.sbanken.no/apibeta/api/v2/transactions/%s' % accountId, headers=headers)
        if self.print_raw_data:
            print(response)
            print(json.dumps(response.json(), indent=4, sort_keys=True))
        return response.json()

    @lru_cache(maxsize=10)
    def get_standing_orders_data(self, accountId, ttl_hash=None):
        if self.verbose:
            print('Fetching standing orders for account [%s]...' % accountId)
        headers = {'Authorization': 'Bearer ' + self.get_access_token(), 'customerId': self.user_id, 'Accept': 'application/json', 'Content-Type': 'application/json-patch+json', }
        response = self.session.get('https://publicapi.sbanken.no/apibeta/api/v2/standingorders/%s' % accountId, headers=headers)
        if self.print_raw_data:
            print(response)
            print(json.dumps(response.json(), indent=4, sort_keys=True))
        return response.json()

    @lru_cache(maxsize=10)
    def get_due_payments_data(self, accountId, ttl_hash=None):
        if self.verbose:
            print('Fetching due payments for account [%s]...' % accountId)
        headers = {'Authorization': 'Bearer ' + self.get_access_token(), 'customerId': self.user_id, 'Accept': 'application/json', 'Content-Type': 'application/json-patch+json', }
        response = self.session.get('https://publicapi.sbanken.no/apibeta/api/v2/payments/%s' % accountId, headers=headers)
        if self.print_raw_data:
            print(response)
            print(json.dumps(response.json(), indent=4, sort_keys=True))
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
        if self.print_raw_data:
            print(response)
            print(json.dumps(response.json(), indent=4, sort_keys=True))
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
        if self.print_raw_data:
            print(response)
            print(json.dumps(response.json(), indent=4, sort_keys=True))
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
        if self.print_raw_data:
            print(response)
            print(json.dumps(response.json(), indent=4, sort_keys=True))
        if response.status_code == 200:
            return response.json()
        else:
            raise ApiException(response.status_code, response.text, response.headers, response.reason)
