from .ibank import IBank


class DemoBank(IBank):
    def get_id(self):
        return 'demo'

    def get_name(self):
        return 'Demo'

    def get_customer_info(self):
        return {'item': {'customerId': '01017012345', 'firstName': 'Jane', 'lastName': 'Doe', 'emailAddress': 'jane.doe@example.com', 'dateOfBirth': '1970-01-01T00:00:00', 'postalAddress': {'addressLine1': '526 Hunter Street', 'addressLine2': '', 'addressLine3': 'Newcastle 2300 NSW', 'addressLine4': 'Australia', 'country': None, 'zipCode': None, 'city': None}, 'streetAddress': {'addressLine1': '526 Hunter Street', 'addressLine2': '', 'addressLine3': 'Newcastle 2300 NSW', 'addressLine4': 'Australia', 'country': None, 'zipCode': None, 'city': None}, 'phoneNumbers': [{'countryCode': '1', 'number': '800-555-2368'}]}, 'errorType': None, 'isError': False, 'errorCode': None, 'errorMessage': None, 'traceId': None}

    def get_accounts(self):
        pass

    def get_account_data(self, ttl_hash=None):
        return {
            "items": [
                {
                    "accountId": "123",
                    "accountNumber": "97101299999",
                    "accountType": "Standard account",
                    "available": 10441.4,
                    "balance": 10550.0,
                    "creditLimit": 0.0,
                    "name": "Brukskonto",
                    "ownerCustomerId": "01017012345"
                },
                {
                    "accountId": "124",
                    "accountNumber": "97101399999",
                    "accountType": "High interest account",
                    "available": 101739.21,
                    "balance": 101739.21,
                    "creditLimit": 0.0,
                    "name": "Sparekonto",
                    "ownerCustomerId": "01017012345"
                },
                {
                    "accountId": "125",
                    "accountNumber": "97231499999",
                    "accountType": "BSU account",
                    "available": 41769.49,
                    "balance": 530245.07,
                    "creditLimit": 0.0,
                    "name": "BSU-konto",
                    "ownerCustomerId": "01017012345"
                },
                {
                    "accountId": "126",
                    "accountNumber": "98001599999",
                    "accountType": "High interest account",
                    "available": 1003940.27,
                    "balance": 1003940.27,
                    "creditLimit": 0.0,
                    "name": "Data counter widget",
                    "ownerCustomerId": "01017012345"
                }
            ]
        }
