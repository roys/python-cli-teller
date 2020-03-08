from .ibank import IBank
import base64
import requests
import time
import urllib


def _(key, *args, **kwargs):
    pass


class Sbanken(IBank):
    def __init__(self, client_id=None, client_secret=None, user_id=None, access_token=None, access_token_expiration=None, dictionary=None, verbose=False):
        super().__init__()
        self.client_id = client_id
        self.client_secret = client_secret
        self.user_id = user_id
        self.access_token = access_token
        self.access_token_expiration = access_token_expiration
        self.verbose = verbose
        _ = dictionary

    def get_id(self):
        return 'sbanken'

    def get_access_token(self):
        if self.access_token is not None and self.access_token_expiration is not None and int(time.time()) < self.access_token_expiration:
            if self.verbose:
                print('Using existing access token that expires in ' + str(int((int(self.access_token_expiration) - time.time()) / 60)) + ' minutes.')
            return self.access_token.decode('utf-8')
        if self.verbose:
            print('Getting a fresh access token.')
            headers = {'Authorization': 'Basic ' + base64.b64encode((urllib.parse.quote_plus(self.client_id) + ':' + urllib.parse.quote_plus(self.client_secret)).encode('utf-8')).decode('utf-8'), 'Accept': 'application/json'}
        response = requests.post('https://auth.sbanken.no/identityserver/connect/token', {'grant_type': 'client_credentials'}, headers=headers)
        if response.status_code == 200:
            json = response.json()
            self.access_token = str(json['access_token'])
            self.access_token_expiration = str(int(time.time()) + int(json['expires_in']))
            return self.access_token
        else:
            print()
            print(_('error_failed_to_authenticate', response.status_code, response.content, error=True))
        return None

    def get_account_data(self):
        headers = {'Authorization': 'Bearer ' + self.get_access_token(), 'customerId': self.user_id, 'Accept': 'application/json', 'Content-Type': 'application/json-patch+json', }
        response = requests.get('https://api.sbanken.no/exec.bank/api/v1/accounts', headers=headers)
        return response.json()

    def get_accounts(self):
        pass
