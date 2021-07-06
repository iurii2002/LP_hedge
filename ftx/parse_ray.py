import requests


def get_price_ftx(coin):
    market = f'{coin}/USD'
    url = f'https://ftx.com/api/markets/{market}'
    try:
        response = requests.get(url).json()['result']
        return float(response['last'])
    except Exception as err:
        print('Something went wrong', err)


def calculate_token_amount_in_pool(product, price):
    # AMM_formula for USDC/Token pool
    # Token = Constant product / token price ^ ( 1 / 2 )
    # USDC = token * token price
    amount = (product / price) ** (1 / 2)
    return amount


def get_price_ftx_for_order(coin):
    market = f'{coin}-PERP'
    url = f'https://ftx.com/api/markets/{market}'
    try:
        response = requests.get(url).json()['result']
        bid = float(response['bid'])
        ask = float(response['ask'])
        return bid, ask
    except Exception as err:
        print('Something went wrong', err)
