
class User:
    def __init__(self, cid: str, status='passive', api_s: str = None, api_k: str = None, subaccount: str = None) -> None:
        self.cid = cid
        self.status = status
        self.api_s = api_s
        self.api_k = api_k
        self.subaccount = subaccount

    def print_user_data(self) -> str:
        hidden_api_k = self.api_k[0:4] + '*' * (len(self.api_k) - 4)
        hidden_api_s = self.api_s[0:4] + '*' * (len(self.api_s) - 4)
        text = f"""
    Your data:
Api key: {hidden_api_k}
Api secret: {hidden_api_s}
Subaccount: {self.subaccount}
            """
        return text

    def set_api_s(self, api_s) -> None:
        self.api_s = api_s

    def set_api_k(self, api_k) -> None:
        self.api_k = api_k

    def set_subaccount(self, subaccount) -> None:
        self.subaccount = subaccount

    def get_api_s(self) -> str:
        return self.api_s

    def get_api_k(self) -> str:
        return self.api_k

    def get_subaccount(self) -> str:
        return self.subaccount

    def get_cid(self) -> str:
        return self.cid

    def get_status(self) -> str:
        return self.status


class Position:
    def __init__(self, cid: int) -> None:
        self.cid = cid
        self.coin_one = ""
        self.coin_two = ""

        self.coin_one_amount = None
        self.coin_one_target = None
        self.coin_one_fluctuation = None

        self.coin_two_amount = None
        self.coin_two_target = None
        self.coin_two_fluctuation = None

    def print_single_position_data(self) -> str:
        text = f"""
    Your data:
Pool: {self.coin_one} - {self.coin_two}
Amount: {self.coin_one_amount} - {self.coin_two_amount}
Target: {self.coin_one_target}% +- {self.coin_one_fluctuation}%
            """
        return text

    def print_double_position_data(self) -> str:
        text = f"""
    Your data:
Pool: {self.coin_one} - {self.coin_two}
Amount: {self.coin_one_amount} - {self.coin_two_amount}
Target {self.coin_one} : {self.coin_one_target}% +- {self.coin_one_fluctuation}%
Target {self.coin_two} : {self.coin_two_target}% +- {self.coin_two_fluctuation}%
            """
        return text

    def set_coin_one(self, coin: str) -> None:
        self.coin_one = coin

    def set_coin_two(self, coin: str) -> None:
        self.coin_two = coin

    def set_coin_one_amount(self, amount: int) -> None:
        self.coin_one_amount = amount

    def set_coin_two_amount(self, amount: int) -> None:
        self.coin_two_amount = amount

    def set_coin_one_target(self, number: int) -> None:
        self.coin_one_target = number

    def set_coin_two_target(self, number: int) -> None:
        self.coin_two_target = number

    def set_coin_one_fluctuation(self, number: int) -> None:
        self.coin_one_fluctuation = number

    def set_coin_two_fluctuation(self, number: int) -> None:
        self.coin_two_fluctuation = number

    def get_cid(self) -> int:
        return self.cid

    def get_coin_one(self) -> str:
        return self.coin_one

    def get_coin_two(self) -> str:
        return self.coin_two

    def get_coin_one_amount(self) -> str:
        return self.coin_one_amount

    def get_coin_two_amount(self) -> str:
        return self.coin_two_amount

    def get_coin_one_target(self) -> str:
        return self.coin_one_target

    def get_coin_two_target(self) -> str:
        return self.coin_two_target

    def get_coin_one_fluctuation(self) -> str:
        return self.coin_one_fluctuation

    def get_coin_two_fluctuation(self) -> str:
        return self.coin_two_fluctuation
