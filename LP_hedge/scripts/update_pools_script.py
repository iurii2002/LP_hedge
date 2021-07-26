import copy

from LP_hedge.mongo.db_management import get_all_users_data, get_user_position, update_all_pools_in_db
from LP_hedge.scripts.parse_ftx_data import get_price_ftx, calculate_token_amount_in_pool, calculate_token_amount_in_double_pool


token_prices = {}


def update_all_user_pools() -> None:
    users = get_all_users_data()
    for user in users:
        cid = user['cid']
        if user['status'] == "active":
            data = get_user_position(cid)
            new_data = copy.deepcopy(data)
            pools = data['pools']
            new_pools = []
            for pool in pools:
                if pool['pool'] == 'single':
                    updated_pool = update_single_pool(pool)
                    new_pools.append(updated_pool)
                if pool['pool'] == 'double':
                    updated_pool = update_double_pool(pool)
                    new_pools.append(updated_pool)
            new_data['pools'] = new_pools
            update_all_pools_in_db(cid, data, new_data)
            token_prices.clear()
        else:
            """don't need this for non-active users"""
            continue


def update_single_pool(pool):
    token_one = list(pool['tokens'].keys())[0]
    token_two = 'USD'
    first_token_price = None
    pool_product = pool['product']
    if token_one not in token_prices:
        while first_token_price is None:
            try:
                first_token_price = get_price_ftx(token_one)
                token_prices[token_one] = first_token_price
            except Exception as err:
                print('Something went wrong', err)
    else:
        first_token_price = token_prices[token_one]
    token_one_amount = round(calculate_token_amount_in_pool(pool_product, first_token_price), 2)
    token_two_amount = round(token_one_amount * first_token_price, 2)
    updated_pool = {'pool': 'single', 'tokens': {token_one: token_one_amount, token_two: token_two_amount},
                    'product': pool_product, 'target': pool['target'], 'fluctuation': pool['fluctuation']}
    return updated_pool


def update_double_pool(pool):
    token_one = list(pool['tokens'].keys())[0]
    token_two = list(pool['tokens'].keys())[1]
    first_token_price = None
    second_token_price = None
    pool_product = pool['product']

    if token_one not in token_prices:
        while first_token_price is None:
            try:
                first_token_price = get_price_ftx(token_one)
                token_prices[token_one] = first_token_price
            except Exception as err:
                print('Something went wrong', err)
    else:
        first_token_price = token_prices[token_one]

    if token_two not in token_prices:
        while second_token_price is None:
            try:
                second_token_price = get_price_ftx(token_two)
                token_prices[token_two] = second_token_price
            except Exception as err:
                print('Something went wrong', err)
    else:
        second_token_price = token_prices[token_two]

    token_one_amount, token_two_amount = \
        calculate_token_amount_in_double_pool(pool_product, first_token_price, second_token_price)

    token_one_amount = round(token_one_amount, 2)
    token_two_amount = round(token_two_amount, 2)

    updated_pool = {'pool': 'double', 'tokens': {token_one: token_one_amount, token_two: token_two_amount},
                    'product': pool_product, 'target': pool['target'], 'fluctuation': pool['fluctuation']}

    return updated_pool
