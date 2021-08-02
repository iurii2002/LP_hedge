from LP_hedge.ftx.rest_client import FtxClient


def check_ftx_api(api_k, api_s, sub_a=None):
    bot = FtxClient(api_key=api_k, api_secret=api_s, subaccount_name=sub_a)
    try:
        bot.get_account_info()
        return True
    except Exception as err:
        if str(err) == 'Not logged in':
            """wrong account data"""
            return False
        else:
            """Some other mistake"""
            return False
