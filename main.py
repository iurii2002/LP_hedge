# from tg.tg_bot import start_bot
from mongo.mongo_db import get_all_users_data

import subprocess
import time

run_subprocess = []
# run_subprocess[0].terminate() to kill the process

if __name__ == "__main__":
    price_update = subprocess.Popen(['python', 'price_update_process.py'], shell=True, stdout=subprocess.PIPE)
    run_subprocess.append(price_update)

    for data in get_all_users_data():
        if data['status'] == 'active':
            print(data)
            bot = subprocess.run(
                ['python', 'start_hedge_process.py', data['api']['api-key'], data['api']['api-secret'],
                 data['api']['sub-account'], str(data['cid'])], shell=True)
            # , stdout=subprocess.PIPE
            run_subprocess.append(bot)

    # start_bot()
