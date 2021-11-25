from .ibank import IBank


class DemoBank(IBank):

    accounts = [
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
                    "name": "teller.py",
                    "ownerCustomerId": "01017012345"
                }
            ]
            
    def get_id(self):
        return 'demo'

    def get_name(self):
        return 'Demo'

    def get_customer_info(self, ttl_hash=None):
        return {'customerId': '01017012345', 'firstName': 'Jane', 'lastName': 'Doe', 'emailAddress': 'jane.doe@example.com', 'dateOfBirth': '1970-01-01T00:00:00', 'postalAddress': {'addressLine1': '526 Hunter Street', 'addressLine2': '', 'addressLine3': 'Newcastle 2300 NSW', 'addressLine4': 'Australia', 'country': None, 'zipCode': None, 'city': None}, 'streetAddress': {'addressLine1': '526 Hunter Street', 'addressLine2': '', 'addressLine3': 'Newcastle 2300 NSW', 'addressLine4': 'Australia', 'country': None, 'zipCode': None, 'city': None}, 'phoneNumbers': [{'countryCode': '1', 'number': '800-555-2368'}]}

    def get_accounts(self):
        pass

    def get_account_data(self, ttl_hash=None):
        return {
            "items": self.accounts
        }

    def get_efaktura_data(self, ttl_hash=None):
        return {
            "items": [
                {
                    "creditAccountNumber": "97121499999",
                    "documentType": "INVOICE",
                    "eFakturaId": "161718",
                    "eFakturaReference": "192021",
                    "issuerId": "222324",
                    "issuerName": "Student loan",
                    "kid": "40",
                    "minimumAmount": 0.0,
                    "notificationDate": "2020-12-21T00:00:00",
                    "originalAmount": 1747.0,
                    "originalDueDate": "2021-01-15T00:00:00",
                    "status": "PROCESSED",
                    "updatedAmount": 1800.0,
                    "updatedDueDate": "2021-01-15T00:00:00"
                },
                {
                    "creditAccountNumber": "97121399999",
                    "documentType": "INVOICE",
                    "eFakturaId": "101112",
                    "eFakturaReference": "131415",
                    "issuerId": "252627",
                    "issuerName": "Credit card",
                    "kid": "41",
                    "minimumAmount": 633.91,
                    "notificationDate": "2021-01-06T00:00:00",
                    "originalAmount": 15847.78,
                    "originalDueDate": "2021-01-20T00:00:00",
                    "status": "NEW",
                    "updatedAmount": 0.0,
                    "updatedDueDate": None
                },
                {
                    "creditAccountNumber": "97101299999",
                    "documentType": "INVOICE_WITH_AVTALEGIRO",
                    "eFakturaId": "123",
                    "eFakturaReference": "456",
                    "issuerId": "789",
                    "issuerName": "roysolberg.com",
                    "kid": "42",
                    "minimumAmount": 0.0,
                    "notificationDate": "2021-01-05T00:00:00",
                    "originalAmount": 1337.0,
                    "originalDueDate": "2021-01-21T00:00:00",
                    "status": "NEW",
                    "updatedAmount": 0.0,
                    "updatedDueDate": None
                },
            ]
        }

    def get_inbox(self, ttl_hash=None):
        return {
            "availableItems": 3,
            "items": [
                {
                    "attachmentId": None,
                    "category": 0,
                    "flag": 0,
                    "id": 541797,
                    "linkName": None,
                    "linkUrl": None,
                    "receivedDate": "2021-11-19T13:02:30.553",
                    "source": "Banken",
                    "status": 0,
                    "subject": "Varsel om endring i avtalevilk\u00e5r - ny prismodell for fond p\u00e5 IPS"
                },
                {
                    "attachmentId": 8297,
                    "category": 1,
                    "flag": 1,
                    "id": 806022,
                    "linkName": None,
                    "linkUrl": None,
                    "receivedDate": "2021-08-07T01:01:45.013",
                    "source": "Banken",
                    "status": 1,
                    "subject": "Kredittvurdering"
                },
                {
                    "attachmentId": None,
                    "category": 0,
                    "flag": 1,
                    "id": 801776,
                    "linkName": None,
                    "linkUrl": None,
                    "receivedDate": "2021-08-05T23:25:21.503",
                    "source": "Banken",
                    "status": 1,
                    "subject": "Kredittvurdering"
                }
            ]
        }
