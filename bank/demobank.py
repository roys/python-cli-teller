from .ibank import IBank


class DemoBank(IBank):
    def get_id(self):
        return 'demo'

    def get_accounts(self):
        pass
