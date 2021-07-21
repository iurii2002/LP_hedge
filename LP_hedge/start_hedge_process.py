import sys
import logging
import time

from LP_hedge.ftx.app import MyBot


api_key = sys.argv[1]
api_secret = sys.argv[2]
subaccount_name = sys.argv[3]
cid = int(sys.argv[4])

bot = MyBot(api_key=api_key, api_secret=api_secret, subaccount_name=subaccount_name, cid=cid)

format_log = "%(asctime)s: %(message)s"
logging.basicConfig(format=format_log, level=logging.INFO, filename=f"log {cid}.txt",
                    datefmt="%H:%M:%S")


i = 0

# while True:
while i < 60:
    print(i)
    bot.check_positions()
    logging.info('short_positions ', bot.short_positions)
    logging.info('pools_positions ', bot.pools_positions)
    time.sleep(60)
    i += 1

