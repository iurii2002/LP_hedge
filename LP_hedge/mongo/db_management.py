import copy
import json
from typing import List, Dict

from LP_hedge.mongo.db_collections import col_users, col_position, col_processes, col_shorts


def check_if_user_exist_in_db(cid: int) -> bool:
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


def get_user_data(cid) -> Dict:
    result = col_users.find_one({"cid": cid})
    return result


def get_all_users_data() -> List[Dict]:
    return [user for user in col_users.find()]


def get_all_active_users() -> List[Dict]:
    return [user for user in col_users.find() if user['status'] == 'active']


def delete_user(cid: int) -> None:
    if check_if_user_exist_in_db(cid):
        user = col_users.find_one({"cid": cid})
        col_users.delete_one(user)


def get_user_position(cid: int) -> Dict:
    myquery = {"cid": cid}
    if col_position.find_one(myquery) is not None:
        return col_position.find_one(myquery)
    else:
        return {}


def get_user_pivot_position(cid: int) -> Dict:
    full_position = get_user_position(cid)
    if full_position:
        return full_position['position']
    else:
        return {}


def print_user_pivot_data(cid: int):
    shorts = get_shorts_from_db(cid) if get_shorts_from_db(cid) else {}
    position = get_user_position(cid)['position'] if get_user_position(cid)['position'] else {}

    user_total_data = ''
    pivot_data = {**shorts, **position}
    for coin in pivot_data.keys():
        try:
            shorts_data = shorts[coin]
        except KeyError:
            shorts_data = 'None'
        try:
            position_data = position[coin]
        except KeyError:
            position_data = 'None'

        data = f"\n{coin.ljust(5)} \nShort: {shorts_data}. \nPosition: {position_data} \n"
        user_total_data += data

    message = f"""
You current data:{user_total_data}
        """

    return message


def print_user_pools(cid: int) -> (str, int):
    number_of_pools = 0

    user_data = get_user_position(cid)
    if user_data == {}:
        return "", number_of_pools

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
Pools:
{pools}
    """
    return message, number_of_pools


def return_specific_pool_data(cid: int, pool: int) -> (str, str):
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


def delete_pool(cid: int, pool: int) -> None:
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


def update_position_pivot_data(cid: int) -> None:
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


def edit_pool_in_db(cid: int, pool_nb: int, pool) -> None:
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


def update_all_pools_in_db(cid: int, old_position, new_position) -> None:
    newvalues = {"$set": new_position}
    col_position.update_one(old_position, newvalues)

    update_position_pivot_data(cid)


def add_running_process_to_db(pid: int, name: str) -> None:
    if check_if_process_exist_in_db(pid):
        return
    else:
        new_process = {'pid': pid, 'name': name}
        col_processes.insert_one(new_process)


def get_all_running_process() -> List:
    running_processes = [process['pid'] for process in col_processes.find()]
    return running_processes


def check_if_process_exist_in_db(pid: int) -> bool:
    if pid in get_all_running_process():
        return True
    else:
        return False


def get_process_pid_by_name(name: str):
    myquery = {'name': name}
    if response := col_processes.find_one(myquery):
        return response['pid']
    else:
        return None


def delete_process_from_db(pid: int) -> None:
    if check_if_process_exist_in_db(pid):
        process = col_processes.find_one({"pid": pid})
        col_processes.delete_one(process)


def get_shorts_from_db(cid: int) -> dict or None:
    myquery = {'cid': cid}
    if response := col_shorts.find_one(myquery):
        return response['shorts']
    else:
        return None


def check_if_user_shorts_exist_in_db(cid: int) -> bool:
    if get_shorts_from_db(cid):
        return True
    else:
        return False


def add_new_shorts_to_db(cid: int, shorts: dict) -> None:
    new_shorts = {'cid': cid, 'shorts': shorts}
    col_shorts.insert_one(new_shorts)


def correct_current_shorts_in_db(cid: int, new_shorts: dict, old_shorts: dict) -> None:
    new_shorts = {"$set": {"cid": cid, "shorts": new_shorts}}
    col_shorts.update_one(old_shorts, new_shorts)


def update_shorts_in_db(cid: int, new_shorts: dict) -> None:
    if current_shorts := get_shorts_from_db(cid):
        correct_current_shorts_in_db(cid, new_shorts, current_shorts)
    else:
        add_new_shorts_to_db(cid, new_shorts)


def delete_shorts_from_db(cid: int) -> None:
    if current_shorts := get_shorts_from_db(cid):
        user_data = {'cid': cid, 'shorts': current_shorts}
        col_shorts.delete_one(user_data)
