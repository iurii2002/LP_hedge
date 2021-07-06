import pymongo
import copy
import json
from typing import DefaultDict, Deque, List, Dict, Tuple, Optional, ClassVar

myclient = pymongo.MongoClient("mongodb://localhost:27017/")
mydb = myclient["farm_hedge"]

col_users = mydb["users"]
# user collection scheme = {"cid": 47805431514, "status": "active/passive",
#                           "api": {"api-key": "text", "api-secret": "text", "sub-account": "text"}}

col_position = mydb["user position"]
# postision scheme = {"cid": 47805431514,
# "position": {"FTM": 3550, "ETH": 1},
# "pools":
# [{"pool": "single", "tokens": {"FTM" : 2550, "USD": 1000}, "target": 1.15, "fluctuation": 10},
# {"pool": "double",  "tokens": {"FTM" : 1000, "ETH": 1}, "target": 1.15, "fluctuation": 10}]}
# todo target 1 and target 2??


def check_if_user_exist(cid: str):
    myquery = {"cid": cid}
    if col_users.find_one(myquery) is not None:
        return col_users.find_one(myquery)
    else:
        return False


def add_user(user) -> None:
    new_user = {"cid": user.cid, "status": user.status,
                "api": {"api-key": user.api_k, "api-secret": user.api_s, "sub-account": user.subaccount}}
    col_users.insert_one(new_user)


def update_user(user, old_user) -> None:
    col_users.delete_one(old_user)
    new_user = {"cid": user.cid, "status": user.status,
                "api": {"api-key": user.api_k, "api-secret": user.api_s, "sub-account": user.subaccount}}
    col_users.insert_one(new_user)


def update_user_db(user) -> None:
    print(user)
    if check_if_user_exist(user.cid):
        old_user = col_users.find_one({"cid": user.cid})
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


def delete_user(cid: str):
    if check_if_user_exist(cid):
        user = col_users.find_one({"cid": cid})
        col_users.delete_one(user)


def get_user_position(cid: str):
    myquery = {"cid": cid}
    if col_position.find_one(myquery) is not None:
        return col_position.find_one(myquery)
    else:
        return False


def print_user_position(cid: str) -> (str, int):
    user_data = get_user_position(cid)
    user_position = ''
    for coin, position in user_data['position'].items():
        user_position += f"{coin}: {position};  "
    pools = "\n"
    i = 1
    for pool in user_data['pools']:
        text = str(i) + '.  ' + json.dumps(pool['tokens']).ljust(40) + "\n" 'Target: ' + str(pool['target']) \
               + "%" + ', fluctuation: ' + str(pool['fluctuation']) + "%\n\n"
        pools += text
        i += 1
    message = f"""
Total in pools: 
{user_position}
    
Pools:{pools}
    """
    return message, i


def print_specific_pool(cid: str, pool: int):
    pool_data = json.dumps(get_user_position(cid)["pools"][pool - 1])
    return pool_data


def delete_pool(cid: str, pool: int):
    user_position_old = get_user_position(cid)
    pool_data = user_position_old["pools"][pool - 1]
    user_position_new = copy.deepcopy(user_position_old)
    user_position_new['pools'].remove(pool_data)

    newvalues = {"$set": user_position_new}

    col_position.update_one(user_position_old, newvalues)

    update_position_pivot_data(cid)


def add_hedge(position) -> None:
    pool = 'single' if position.coin_two == 'USD' else 'double'
    if get_user_position(position.cid):
        new_pool = {"pool": pool, "tokens": {
                                position.coin_one: position.coin_one_amount,
                                position.coin_two: position.coin_two_amount
                            }, "target": position.target, "fluctuation": position.fluctuation}
        user_data = get_user_position(position.cid)
        new_user_data = copy.deepcopy(user_data)
        new_user_data['pools'].append(new_pool)
        newvalues = {"$set": new_user_data}
        col_position.update_one(user_data, newvalues)
        update_position_pivot_data(position.cid)
    else:
        new_position = {"cid": position.cid,
                        "position": {},
                        "pools": [{"pool": pool, "tokens": {
                            position.coin_one: position.coin_one_amount,
                            position.coin_two: position.coin_two_amount
                        }, "target": position.target, "fluctuation": position.fluctuation}]
                        }
        col_position.insert_one(new_position)
        update_position_pivot_data(position.cid)
    print(get_user_position(position.cid))


def update_position_pivot_data(cid):
    # This data will be updated based on the new pools -> "position": {"FTM": 3550, "ETH": 1}
    data = get_user_position(cid)
    new_data = copy.deepcopy(data)
    new_data['position'] = {}
    for pool in data['pools']:
        for token, amount in pool['tokens'].items():
            if token in new_data['position']:
                new_amount = new_data['position'][token] + amount
                new_data['position'][token] = new_amount
            elif token == 'USD':
                continue
            else:
                new_data['position'][token] = amount
    newvalues = {"$set": new_data}
    col_position.update_one(data, newvalues)


def edit_pool_in_db(cid: str, pool_nb: int, pool):
    user_position_old = get_user_position(cid)
    pool_data = user_position_old["pools"][pool_nb - 1]
    new_pool = {
        'pool': 'single', 'tokens':
            {pool.coin_one: pool.coin_one_amount, pool.coin_two: pool.coin_two_amount},
        'target': pool.target, 'fluctuation': pool.fluctuation
    }
    user_position_new = copy.deepcopy(user_position_old)
    user_position_new['pools'].remove(pool_data)
    user_position_new['pools'].append(new_pool)

    newvalues = {"$set": user_position_new}

    col_position.update_one(user_position_old, newvalues)

    update_position_pivot_data(cid)
