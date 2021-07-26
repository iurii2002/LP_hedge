import copy
import json
from typing import List, Dict

from LP_hedge.mongo.db_collections import col_users, col_position, col_current_processes


def check_if_user_exist_in_db(cid: str) -> bool:
    myquery = {"cid": cid}
    if col_users.find_one(myquery) is not None:
        return col_users.find_one(myquery)
    else:
        return False


def add_user(user) -> None:
    new_user = {"cid": user.get_cid(), "status": user.get_status(),
                "api": {"api-key": user.get_api_k(), "api-secret": user.get_api_s(), "sub-account": user.get_subaccount()}}
    col_users.insert_one(new_user)


def update_user(user, old_user) -> None:
    col_users.delete_one(old_user)
    new_user = {"cid": user.get_cid(), "status": user.get_status(),
                "api": {"api-key": user.get_api_k(), "api-secret": user.get_api_s(), "sub-account": user.get_subaccount()}}
    col_users.insert_one(new_user)


def update_user_db(user) -> None:
    if check_if_user_exist_in_db(user.get_cid()):
        old_user = col_users.find_one({"cid": user.get_cid()})
        update_user(user, old_user)
    else:
        add_user(user)


def get_user_data(cid: str) -> Dict:
    result = col_users.find_one({"cid": cid})
    return result


def get_all_users_data() -> List[Dict]:
    users = []
    for x in col_users.find():
        users.append(x)
    return users


def delete_user(cid: str) -> None:
    if check_if_user_exist_in_db(cid):
        user = col_users.find_one({"cid": cid})
        col_users.delete_one(user)


def get_user_position(cid: str) -> Dict:
    myquery = {"cid": int(cid)}
    if col_position.find_one(myquery) is not None:
        return col_position.find_one(myquery)
    else:
        return {}


def get_user_pivot_position(cid: str) -> Dict:
    full_position = get_user_position(cid)
    if full_position:
        return full_position['position']
    else:
        return {}


def print_user_position(cid: str) -> (str, int):
    number_of_pools = 0

    user_data = get_user_position(cid)
    if user_data == {}:
        return "", number_of_pools

    user_position = ''
    for coin, position in user_data['position'].items():
        user_position += f"{coin}: {position};  \n"

    pools = ""
    for pool in user_data['pools']:
        number_of_pools += 1
        coin_one, coin_two = list(pool['tokens'].keys())[0], list(pool['tokens'].keys())[1]
        if pool['pool'] == 'single':
            text = str(number_of_pools) + '.  ' + json.dumps(pool['tokens']).ljust(40) + "\n" + \
                   f'Target {coin_one}: ' + str(pool['target']) + "%" + ' +- ' + str(pool['fluctuation']) + "%\n\n"
            pools += text
        if pool['pool'] == 'double':
            text = str(number_of_pools) + '.  ' + json.dumps(pool['tokens']).ljust(40) + "\n" + \
                   f'Target {coin_one}: ' + str(pool['target'][0]) + "%" + ' +- ' + str(pool['fluctuation'][0]) + "%\n" + \
                   f'Target {coin_two}: ' + str(pool['target'][1]) + "%" + ' +- ' + str(pool['fluctuation'][1]) + "%\n\n"
            pools += text
    message = f"""
Total in pools: 
{user_position}
    
Pools:
{pools}
    """
    return message, number_of_pools


def return_specific_pool_data(cid: str, pool: int) -> (str, str):
    pool = get_user_position(cid)["pools"][pool - 1]
    pool_data = json.dumps(pool)
    coin_one, coin_two = list(pool['tokens'].keys())[0], list(pool['tokens'].keys())[1]

    text = ''
    if pool['pool'] == 'single':
        text = json.dumps(pool['tokens']).ljust(40) + "\n" + \
               f'Target {coin_one}: ' + str(pool['target']) + "%" + ' +- ' + str(pool['fluctuation']) + "%\n\n"
    if pool['pool'] == 'double':
        text = json.dumps(pool['tokens']).ljust(40) + "\n" + \
               f'Target {coin_one}: ' + str(pool['target'][0]) + "%" + ' +- ' + str(pool['fluctuation'][0]) + "%\n" + \
               f'Target {coin_two}: ' + str(pool['target'][1]) + "%" + ' +- ' + str(pool['fluctuation'][1]) + "%\n\n"

    return text, pool_data


def delete_pool(cid: str, pool: int) -> None:
    user_position_old = get_user_position(cid)
    pool_data = user_position_old["pools"][pool - 1]
    user_position_new = copy.deepcopy(user_position_old)
    user_position_new['pools'].remove(pool_data)

    newvalues = {"$set": user_position_new}

    col_position.update_one(user_position_old, newvalues)

    update_position_pivot_data(cid)


def add_hedge(position) -> None:

    pool = 'single' if position.get_coin_two() == 'USD' else 'double'

    if pool == 'single':
        """
        pool schema:
        {'pool': 'single', 'tokens': {'STEP': 4500.0, 'USD': 1150.0}, 'product': 1000.00, 'target': 120.0, 'fluctuation': 15}
        """
        if len(get_user_position(position.cid)) > 0:
            """
            update hedge
            """
            new_pool = {"pool": pool, "tokens": {
                position.coin_one: position.get_coin_one_amount(),
                position.coin_two: position.get_coin_two_amount()
            },
                "product": position.get_coin_one_amount() * position.get_coin_two_amount(),
                "target": position.coin_one_target, "fluctuation": position.coin_one_fluctuation}
            user_data = get_user_position(position.cid)
            new_user_data = copy.deepcopy(user_data)
            new_user_data['pools'].append(new_pool)
            newvalues = {"$set": new_user_data}
            col_position.update_one(user_data, newvalues)
            update_position_pivot_data(position.cid)
        else:
            """
            add new hedge
            """
            new_position = {"cid": position.cid,
                            "position": {},
                            "pools": [{"pool": pool, "tokens": {
                                position.coin_one: position.get_coin_one_amount(),
                                position.coin_two: position.get_coin_two_amount()
                            },
                                "product": position.get_coin_one_amount() * position.get_coin_two_amount(),
                                "target": position.coin_one_target, "fluctuation": position.coin_one_fluctuation}]
                            }
            col_position.insert_one(new_position)
            update_position_pivot_data(position.cid)
    elif pool == 'double':
        """
        pool schema:
        {'pool': 'double', 'tokens': {'FTM': '5000', 'ETH': '1'}, 'product': 1000.00, 'target': [120.0, 150.0], 'fluctuation': [10.0, 15.0]}
        """
        if len(get_user_position(position.cid)) > 0:
            """
            update hedge
            """
            new_pool = {"pool": pool, "tokens": {
                position.get_coin_one(): position.get_coin_one_amount(),
                position.get_coin_two(): position.get_coin_two_amount()
            },
                        "product": position.get_coin_one_amount() * position.get_coin_two_amount(),
                        "target": [position.get_coin_one_target(), position.get_coin_two_target()],
                        "fluctuation": [position.get_coin_one_fluctuation(), position.get_coin_two_fluctuation()]}
            user_data = get_user_position(position.cid)
            new_user_data = copy.deepcopy(user_data)
            new_user_data['pools'].append(new_pool)
            newvalues = {"$set": new_user_data}
            col_position.update_one(user_data, newvalues)

            update_position_pivot_data(position.get_cid())

        else:
            """
            add new hedge
            """
            new_position = {"cid": position.cid,
                            "position": {},
                            "pools": [{"pool": pool, "tokens": {
                                position.get_coin_one(): position.get_coin_one_amount(),
                                position.get_coin_two(): position.get_coin_two_amount()
                            },
                                       "product": position.get_coin_one_amount() * position.get_coin_two_amount(),
                                       "target": [position.get_coin_one_target(), position.get_coin_two_target()],
                                       "fluctuation": [position.get_coin_one_fluctuation(), position.get_coin_two_fluctuation()]}]
                            }
            col_position.insert_one(new_position)
            update_position_pivot_data(position.get_cid())


def update_position_pivot_data(cid: str) -> None:
    """
    This data will be updated based on the new pools -> "position":
        {'STEP': {'amount': 4456.39, 'floor': -401.0751, 'ceiling': 490.2029},
        'BNB': {'amount': 21.509999999999998, 'floor': 7.528499999999999, 'ceiling......}
    """
    data = get_user_position(cid)
    new_data = copy.deepcopy(data)
    new_data['position'] = {}
    for pool in data['pools']:

        if pool['pool'] == 'single':
            for token, amount in pool['tokens'].items():

                if token in new_data['position']:
                    old_amount = new_data['position'][token]['amount']
                    new_amount = amount
                    old_floor = new_data['position'][token]['floor']
                    old_ceiling = new_data['position'][token]['ceiling']
                    new_floor = new_amount * (pool['target'] - pool['fluctuation']) / 100
                    new_ceiling = new_amount * (pool['target'] + pool['fluctuation']) / 100

                    details = {'amount': round(old_amount + new_amount, 2),
                               'floor': round(old_floor + new_floor, 2),
                               'ceiling': round(old_ceiling + new_ceiling, 2)}

                    new_data['position'][token] = details

                elif token == 'USD':
                    continue

                else:
                    floor = amount * (pool['target'] - pool['fluctuation']) / 100
                    ceiling = amount * (pool['target'] + pool['fluctuation']) / 100
                    details = {'amount': round(amount, 2),
                               'floor': round(floor, 2),
                               'ceiling': round(ceiling, 2)}
                    new_data['position'][token] = details

        elif pool['pool'] == 'double':

            for count, (token, amount) in enumerate(pool['tokens'].items()):

                if token in new_data['position']:
                    old_amount = new_data['position'][token]['amount']
                    new_amount = amount
                    old_floor = new_data['position'][token]['floor']
                    old_ceiling = new_data['position'][token]['ceiling']
                    new_floor = new_amount * (pool['target'][count] - pool['fluctuation'][count]) / 100
                    new_ceiling = new_amount * (pool['target'][count] + pool['fluctuation'][count]) / 100

                    details = {'amount': round(old_amount + new_amount, 2),
                               'floor': round(old_floor + new_floor, 2),
                               'ceiling': round(old_ceiling + new_ceiling, 2)}

                    new_data['position'][token] = details

                elif token == 'USD' or token == 'USDT' or token == 'USDC' or token == 'DAI':
                    continue

                else:
                    floor = amount * (pool['target'][count] - pool['fluctuation'][count]) / 100
                    ceiling = amount * (pool['target'][count] + pool['fluctuation'][count]) / 100
                    details = {'amount': round(amount, 2),
                               'floor': round(floor, 2),
                               'ceiling': round(ceiling, 2)}
                    new_data['position'][token] = details

    newvalues = {"$set": new_data}
    col_position.update_one(data, newvalues)


def edit_pool_in_db(cid: str, pool_nb: int, pool) -> None:
    user_position_old = get_user_position(cid)
    pool_data = user_position_old["pools"][pool_nb - 1]
    if pool_data['pool'] == 'single':
        new_pool = {
            'pool': 'single', 'tokens':
                {pool.get_coin_one(): pool.get_coin_one_amount(), pool.get_coin_two(): pool.get_coin_two_amount()},
            "product": pool.get_coin_one_amount() * pool.get_coin_two_amount(),
            'target': pool.get_coin_one_target(), 'fluctuation': pool.get_coin_one_fluctuation()
        }
        user_position_new = copy.deepcopy(user_position_old)
        user_position_new['pools'].remove(pool_data)
        user_position_new['pools'].append(new_pool)

        newvalues = {"$set": user_position_new}

        col_position.update_one(user_position_old, newvalues)
    if pool_data['pool'] == 'double':
        new_pool = {
            'pool': 'double', 'tokens':
                {pool.get_coin_one(): pool.get_coin_one_amount(), pool.get_coin_two(): pool.get_coin_two_amount()},
            "product": pool.get_coin_one_amount() * pool.get_coin_two_amount(),
            'target': [pool.get_coin_one_target(), pool.get_coin_two_target()],
            'fluctuation': [pool.get_coin_one_fluctuation(), pool.get_coin_two_fluctuation()]
        }

        user_position_new = copy.deepcopy(user_position_old)
        user_position_new['pools'].remove(pool_data)
        user_position_new['pools'].append(new_pool)

        newvalues = {"$set": user_position_new}

        col_position.update_one(user_position_old, newvalues)

    update_position_pivot_data(cid)


def update_all_pools_in_db(cid: str, old_position, new_position) -> None:
    newvalues = {"$set": new_position}
    col_position.update_one(old_position, newvalues)

    update_position_pivot_data(cid)
