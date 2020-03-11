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
