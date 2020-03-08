from .ibank import IBank


class Sbanken(IBank):
    def __init__(self, user_id, access_token, access_token_expiration):
        super().__init__()
        self.user_id = user_id
        self.access_token = access_token
        self.access_token_expiration = access_token_expiration

    def get_id(self):
        return 'sbanken'

    def get_account_data(self):
        headers = {'Authorization': 'Bearer ' + accessToken, 'customerId': userId, 'Accept': 'application/json', 'Content-Type': 'application/json-patch+json', }
        response = requests.get('https://api.sbanken.no/exec.bank/api/v1/accounts', headers=headers)
        return response.json()

    def get_accounts(self):
        pass
