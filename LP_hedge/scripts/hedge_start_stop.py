import subprocess
import logging

from LP_hedge.mongo.db_management import add_running_process_to_db, delete_process_from_db, get_process_pid_by_name


def start_hedge_process(cid):
    # todo added block to not start any hedge
    return
    process = subprocess.Popen(['python3', 'scripts/hedge_process.py', str(cid)], stdout=subprocess.PIPE)
    add_running_process_to_db(pid=process.pid, name=cid)


def stop_hedge_process(cid):
    # todo added block to not start any hedge
    return
    log_file = f"logging/log_{cid}.txt"

    format_log = "%(asctime)s: %(process)d %(levelname)s %(message)s"
    logging.basicConfig(format=format_log, level=logging.INFO, filename=log_file, datefmt="%H:%M:%S")

    pid = get_process_pid_by_name(cid)
    subprocess.Popen(['kill', pid], stdout=subprocess.PIPE)
    delete_process_from_db(pid=pid)

    logging.info(f'Bot stopped, process {pid} killed')
