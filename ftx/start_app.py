# start process at the background https://stackoverflow.com/questions/1196074/how-to-start-a-background-process-in-python

from app import MyBot
from data import api_k, api_s, subaccount_name
from apscheduler.schedulers.blocking import BlockingScheduler
import logging
import concurrent.futures

# there are two possible scenarios:
# 1. We overall think that the price will go up.
#   In this case we should have short a bit bigger than tokens in pool
# 2. We overall think that the price will go down.
#   In this case we should have short a bit lower than tokens in pool
#   target - target difference between position and hedge, in +% scenario 2, -% scenario 1
#   rebalance - what should be the difference to execute rebalance
#   e.g. if target 5% and rebalance 3%, position will rebalance when difference will be less than 2 or more than 8%

# first token = stablecoin - USDC, USDT

m = [
    {'market': 'BNB', 'first token amount': 3973.4549, 'second token amount': 13.398, 'target': -15, 'rebalance': 10},
    {'market': 'FTM', 'first token amount': 3831.8, 'second token amount': 16600, 'target': -15, 'rebalance': 10},
    {'market': 'STEP', 'first token amount': 1249.491, 'second token amount': 4748.085, 'target': 20, 'rebalance': 10},
]


def create_bot(markets):
    bots = []
    for market in markets:
        bots.append(MyBot(api_k, api_s, subaccount_name, market['market'], market['target'], market['rebalance'],
                          market['first token amount'] * market['second token amount']))
    return bots


def thread_function(bot):
    scheduler = BlockingScheduler()
    scheduler.add_job(bot.check_if_need_rebalance, 'interval', minutes=1)
    scheduler.add_job(bot.send_log, 'interval', hours=12)
    scheduler.add_job(bot.liquidation_soon, 'interval', hours=1)
    scheduler.start()


if __name__ == "__main__":
    format = "%(asctime)s: %(message)s"
    logging.basicConfig(format=format, level=logging.INFO,
                        datefmt="%H:%M:%S")

    bots = create_bot(m)

    with concurrent.futures.ThreadPoolExecutor(max_workers=len(bots)) as executor:
        executor.map(thread_function, bots)
