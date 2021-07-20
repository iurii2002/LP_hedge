import requests


def get_price_ftx(coin):
    # print(coin)
    market = f'{coin}-PERP'
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


def calculate_token_amount_in_double_pool(product, price1, price2):
    # AMM_formula for token/Token pool
    # Token1 amount = (Constant product * token2 price / token1 price) ^ ( 1 / 2 )
    # Token2 amount = (Constant product * token1 price / token2 price) ^ ( 1 / 2 )
    token1_amount = (product * price2 / price1) ** (1 / 2)
    token2_amount = (product * price1 / price2) ** (1 / 2)
    return token1_amount, token2_amount


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


def get_middle_price_for_futures_order(token):
    middle_price = None
    while middle_price is None:
        try:
            bid, ask = get_price_ftx_for_order(token)
            middle_price = (bid + ask) / 2
        except Exception as err:
            print(err)
            pass
    return middle_price
