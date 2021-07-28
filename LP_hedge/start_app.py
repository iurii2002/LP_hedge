import subprocess

from LP_hedge.mongo.db_management import add_running_process_to_db, get_all_running_process, delete_process_from_db, get_all_active_users
from LP_hedge.scripts.hedge_start_stop import start_hedge_process

if __name__ == "__main__":

    for pid in get_all_running_process():
        print('stop process:', pid)
        subprocess.run(['kill', str(pid)], stdout=subprocess.PIPE)
        delete_process_from_db(pid=pid)

    for user in get_all_active_users():
        start_hedge_process(user['cid'])

    price_update = subprocess.Popen(['python3', 'scripts/price_update_process.py'], stdout=subprocess.PIPE)
    add_running_process_to_db(pid=price_update.pid, name='price update')

    tg_bot = subprocess.Popen(['python3', 'tg/tg_bot.py'], stdout=subprocess.PIPE)
    add_running_process_to_db(pid=tg_bot.pid, name='tg bot')
