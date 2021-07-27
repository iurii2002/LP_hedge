import subprocess
from LP_hedge.mongo.db_management import add_running_process_to_db, get_all_running_process, delete_process_from_db

if __name__ == "__main__":

    for process in get_all_running_process():
        print('stop process:', process)
        subprocess.run(['kill', str(process)], stdout=subprocess.PIPE)
        delete_process_from_db(process)

    price_update = subprocess.Popen(['python3', 'scripts/price_update_process.py'], stdout=subprocess.PIPE)
    add_running_process_to_db(price_update.pid)

    tg_bot = subprocess.Popen(['python3', 'tg/tg_bot.py'], stdout=subprocess.PIPE)
    add_running_process_to_db(tg_bot.pid)
