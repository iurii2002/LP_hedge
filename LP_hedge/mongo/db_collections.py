import pymongo

myclient = pymongo.MongoClient("mongodb://localhost:27017/")
mydb = myclient["farm_hedge"]

col_users = mydb["users"]
"""
    user collection scheme = {
        "cid": 47805431514, "status": "active/passive",
        "api": {"api-key": "text", "api-secret": "text", "sub-account": "text"}
        }
"""


col_position = mydb["user position"]
"""
    user position collection scheme = {
        "cid": 47805431514,
        "position": {"FTM": 3550, "ETH": 1},
        "pools":
        [{"pool": "single", "tokens": {"FTM" : 2550, "USD": 1000}, "target": 1.15, "fluctuation": 10},
        {"pool": "double",  "tokens": {"FTM" : 1000, "ETH": 1}, "product": 1000.00, 
        'target': [120.0, 150.0], 'fluctuation': [10.0, 15.0]}
        }
"""

col_current_processes = mydb["processes"]
"""
    current processes collection scheme = {
        "price update": process1, 
        "cid1": process2,
        "cid2": process3,
        }
"""