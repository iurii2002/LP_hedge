import datetime
import re
import json
import logging
import os
import sys
from time import sleep

BASE_PATH = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(BASE_PATH)

from tg.reporting import telegram_bot_sendtext
from parse_ftx_data import get_price_ftx, calculate_token_amount_in_pool, get_price_ftx_for_order
from rest.client import FtxClient


class MyBot(FtxClient):

    def __init__(self, api_key, api_secret, subaccount_name, token, target, rebalance, pool_compound):
        super().__init__(api_key, api_secret, subaccount_name)
        self.first_token = 'USDC'
        self.second_token = token
        self.first_token_price = 1
        self.second_token_price = get_price_ftx(self.second_token)
        self.future_market = self.second_token + '-PERP'
        self.pool_compound = pool_compound
        self.second_token_amount_pool = calculate_token_amount_in_pool(self.pool_compound, self.second_token_price)
        try:
            self.short_position = -self.get_position(self.future_market)['netSize']
        except:
            self.short_position = 0
        self.target = target
        self.rebalance = rebalance

        logging.basicConfig(filename=f"botlog{self.second_token}.txt", level=logging.INFO)

    def update_second_token_pool_data(self):
        self.second_token_price = None
        while self.second_token_price is None:
            try:
                self.second_token_price = get_price_ftx(self.second_token)
            except Exception as err:
                print(err)
        self.second_token_amount_pool = calculate_token_amount_in_pool(self.pool_compound, self.second_token_price)

    def update_short_position(self):
        try:
            self.short_position = -self.get_position(self.future_market)['netSize']
        except TypeError as err:
            self.short_position = 0

    def update_bot_data(self):
        self.update_short_position()
        self.update_second_token_pool_data()

    def check_if_need_rebalance(self):
        self.update_bot_data()
        bottom_position = self.second_token_amount_pool * (1 + self.target / 100) * (1 / (1 + self.rebalance / 100))
        ceiling_position = self.second_token_amount_pool * (1 + self.target / 100) * (1 + self.rebalance / 100)
        self.create_log('check if need rebalance', rebalance_corridor=str(bottom_position) + '-' + str(ceiling_position))
        if self.short_position < bottom_position:
            diff = bottom_position - self.short_position
            self.rebalance_position('sell', diff)
        elif self.short_position > ceiling_position:
            diff = self.short_position - ceiling_position
            self.rebalance_position('buy', diff)

    def rebalance_position(self, side, size):
        self.create_log('rebalance position')
        self.cancel_orders(self.future_market, limit_orders=True)
        middle_price = None
        size = round(size, 0)
        size = 1 if size == 0 else size
        while middle_price is None:
            try:
                bid, ask = get_price_ftx_for_order(self.second_token)
                middle_price = (bid + ask) / 2
            except Exception as err:
                print(err)
                pass
        if self.liquidation_soon() is None:
            # todo as we add bigger order, we need to adjust liquidation check
            try:
                self.place_order(market=self.future_market, side=side, price=middle_price, size=size, type='limit')
            except:
                pass
            self.create_log(f'place {side} order for {middle_price}')

    def liquidation_soon(self):
        try:
            liquidation_price = self.get_position(self.future_market)['estimatedLiquidationPrice']
        except TypeError:
            liquidation_price = float('inf')
        if liquidation_price < self.second_token_price * 3:  #  todo liquidation treshold??
            self.create_log('liquidation soon')
            message = f'Liquidation price is {liquidation_price}, token price is {self.second_token_price}. Consider adding more liquidity to the account'
            telegram_bot_sendtext(message)
            return True

    def create_log(self, activity, rebalance_corridor=None):
        date = datetime.datetime.now().strftime("%d-%m-%Y %H:%M:%S")
        log = {
            "date": date,
            "activity": activity,
            f"{self.second_token} price:": self.second_token_price,
            f"{self.second_token} in pool:": self.second_token_amount_pool,
            "short position: ": self.short_position,
            "rebalance_corridor": rebalance_corridor,
        }
        if re.match(r'place', activity):
            telegram_bot_sendtext(f'Rebalance {self.second_token} position ')
        log = json.dumps(log)
        print(log)
        logging.info(log)

    def send_log(self):
        coverage = round(self.short_position / self.second_token_amount_pool, 2)
        message = f'{self.second_token} market. Short position: {round(self.short_position,0)}, ' \
                  f'token in pool: {round(self.second_token_amount_pool,0)}. ' \
                  f'Coverage: {coverage}. Target: {1 + (self.target - self.rebalance)/100} - {1 + (self.target + self.rebalance)/100}'
        telegram_bot_sendtext(message)

    def update_all_user_pools(self):
        pass


# 1. Get Token Amount in Pool
# 2. Get the short position
# 3. Compare tokens to position
# 4. If position deviates from the tokens, correct it
# 5. Checks to not enter position if it will be liquidated soon
# 6. Notification tg
# 7. Logs
