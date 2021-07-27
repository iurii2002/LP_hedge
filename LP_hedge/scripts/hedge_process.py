import sys
import logging
import time

from LP_hedge.app import MyBot
from LP_hedge.mongo.db_management import get_user_data


cid = sys.argv[1]

log_file = f"logging/log_{cid}.txt"


format_log = "%(asctime)s: %(process)d %(levelname)s %(message)s"
logging.basicConfig(format=format_log, level=logging.INFO, filename=log_file, datefmt="%H:%M:%S")


user_data = get_user_data(int(cid))
# {'_id': ObjectId('60fe7aeec639e830117c470e'), 'cid': 1440189840, 'status': 'active',
# 'api': {'api-key': 'mu9Zuxq9xJyUsKrqhk2igqYChvFgjTDA2hZ-G9O8',
# 'api-secret': 'VmIcl_MGiVqlLFsqJFoHDtQBvQq5AOoqGvi2PTx6', 'sub-account': 'bot_test'}}


bot = MyBot(api_key=user_data['api']['api-key'], api_secret=user_data['api']['api-secret'],
            subaccount_name=user_data['api']['sub-account'], cid=cid)

while True:
    logging.info(f'Check positions for user {cid}')
    bot.check_positions()
    time.sleep(60)
