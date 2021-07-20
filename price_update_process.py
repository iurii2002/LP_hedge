import logging
import time
from ftx.update_pools_script import update_all_user_pools


format_log = "%(asctime)s: %(message)s"
logging.basicConfig(format=format_log, level=logging.INFO, filename="price_update_log.txt",
                    datefmt="%H:%M:%S")

i = 0

# while True:
while i < 60:
    update_all_user_pools()
    logging.info('Prices updated')
    time.sleep(60)
    i += 1
