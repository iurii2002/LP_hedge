import subprocess

from LP_hedge.mongo.db_management import add_running_process_to_db, delete_process_from_db


def start_hedge_process(cid):
    process = subprocess.Popen(['python3', 'scripts/hedge_process.py', str(cid)], stdout=subprocess.PIPE)
    add_running_process_to_db(process.pid)


def stop_hedge_process(cid):
    pass

