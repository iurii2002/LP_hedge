import datetime
import re
import json
import logging
import decimal
import time

from LP_hedge.mongo.db_management import get_user_pivot_position
from LP_hedge.tg.reporting import telegram_bot_sendtext
from LP_hedge.scripts.parse_ftx_data import get_middle_price_for_futures_order
from LP_hedge.ftx.rest_client import FtxClient


class MyBot(FtxClient):

    def __init__(self, api_key, api_secret, subaccount_name, cid):
        super().__init__(api_key, api_secret, subaccount_name)
        self.cid = cid

        self.pools_positions = None
        """ 
            "position": {'STEP': {'amount': 4456.39, 'floor': -401.0751, 'ceiling': 490.2029}, 'BNB': {'amount': 21.509999999999998, 'floor': 7.528499999999999, 'ceiling
        """
        self.short_positions_data = None  # todo we can use this for liquidation check
        """
            [{'future': 'BNB-PERP', 'size': 11.0, 'side': 'sell', 'netSize': -11.0, 'longOrderSize': 0.0, 'shortOrderSize': 0.0, 'cost': -3244.505, 'entryPrice': 294.955, 'unrealizedPnl': 0.0, 'realizedPnl': 28.46051467, 'initialMarginRequirement': 0.1, 'maintenanceMarginRequirement': 0.03, 'openSize': 11.0, 'collateralUsed': 324.4505, 'estimatedLiquidationPrice': 1322.1065659345227, 'recentAverageOpenPrice': 301.7902272727273, 'recentPnl': 75.1875, 'recentBreakEvenPrice': 301.7902272727273, 'cumulativeBuySize': 0.0, 'cumulativeSellSize': 11.0}, {'future': 'RAY-PERP', 'size': 0.0, 'side': 'buy', 'netSize': 0.0, 'longOrderSize': 0.0, 'shortOrderSize': 0.0, 'cost': 0.0, 'entryPrice': None, 'unrealizedPnl': 0.0, 'realizedPnl': 833.36570523, 'initialMarginRequirement': 0.1, 'maintenanceMarginRequirement': 0.03, 'openSize': 0.0, 'collateralUsed': 0.0, 'estimatedLiquidationPrice': None, 'recentAverageOpenPrice': None, 'recentPnl': None, 'recentBreakEvenPrice': None, 'cumulativeBuySize': None, 'cumulativeSellSize': None}, {'future': 'FTM-PERP', 'size': 13562.0, 'side': 'sell', 'netSize': -13562.0, 'longOrderSize': 0.0, 'shortOrderSize': 0.0, 'cost': -2869.7192, 'entryPrice': 0.2116, 'unrealizedPnl': 0.0, 'realizedPnl': 1030.18294052, 'initialMarginRequirement': 0.1, 'maintenanceMarginRequirement': 0.03493680008243457, 'openSize': 13562.0, 'collateralUsed': 286.97192, 'estimatedLiquidationPrice': 1.0447121682111598, 'recentAverageOpenPrice': 0.289728304366876, 'recentPnl': 1061.4872, 'recentBreakEvenPrice': 0.28986922282849137, 'cumulativeBuySize': 132.0, 'cumulativeSellSize': 13694.0}, {'future': 'STEP-PERP', 'size': 6462.9, 'side': 'sell', 'netSize': -6462.9, 'longOrderSize': 0.0, 'shortOrderSize': 0.0, 'cost': -1147.16475, 'entryPrice': 0.1775, 'unrealizedPnl': 0.0, 'realizedPnl': 1023.6865725, 'initialMarginRequirement': 0.1, 'maintenanceMarginRequirement': 0.048235298278335545, 'openSize': 6462.9, 'collateralUsed': 114.716475, 'estimatedLiquidationPrice': 1.9257348829905692, 'recentAverageOpenPrice': 0.39323863900106765, 'recentPnl': 1394.29725, 'recentBreakEvenPrice': 0.39323863900106765, 'cumulativeBuySize': 0.0, 'cumulativeSellSize': 6462.9}, {'future': 'MER-PERP', 'size': 0.0, 'side': 'buy', 'netSize': 0.0, 'longOrderSize': 0.0, 'shortOrderSize': 0.0, 'cost': 0.0, 'entryPrice': None, 'unrealizedPnl': 0.0, 'realizedPnl': 850.97933921, 'initialMarginRequirement': 0.1, 'maintenanceMarginRequirement': 0.03, 'openSize': 0.0, 'collateralUsed': 0.0, 'estimatedLiquidationPrice': None, 'recentAverageOpenPrice': None, 'recentPnl': None, 'recentBreakEvenPrice': None, 'cumulativeBuySize': None, 'cumulativeSellSize': None}]
        """
        self.short_positions = self.update_short_position()
        """
            {'BNB': 11.0, 'FTM': 13562.0, 'STEP': 6462.9}
        """
        logging.basicConfig(filename=f"log_user_{self.cid}.txt", level=logging.INFO)

    def update_short_position(self):
        self.short_positions_data = self.get_positions()
        try:
            positions = {position['future'].split('-')[0]: -position['netSize']
                         for position in self.short_positions_data if position['netSize'] != 0.0}
        except TypeError as err:
            positions = {}
        return positions

    def check_positions(self):
        self.pools_positions = get_user_pivot_position(self.cid)
        """
        self.pools_positions = {'BTC': {'amount': 8.33, 'floor': 8.8, 'ceiling': 11.19}, 'BNB': {'amount': 21.2, 'floor': 17.43, 'ceiling': 23.98}, 'YFI': {'amount': 3.37, 'floor': 3.98, 'ceiling': 4.65}, 'RAY': {'amount': 389.68, 'floor': 515.54, 'ceiling': 653.5}, 'MER': {'amount': 328.13, 'floor': 426.57, 'ceiling': 557.82}, 'STEP': {'amount': 5399.5, 'floor': 5669.48, 'ceiling': 7289.32}, 'FTT': {'amount': 559.25, 'floor': 675.35, 'ceiling': 891.15}, 'ETH': {'amount': 8.65, 'floor': 3.87, 'ceiling': 5.37}}
        """
        for token, position in self.pools_positions.items():
            if token in self.short_positions:
                self.check_if_need_rebalance(token)
            else:
                self.rebalance_position('sell', position['floor'], token)

        not_needed_shorts = [k for k in self.short_positions.keys() if k not in self.pools_positions]
        if len(not_needed_shorts) != 0:
            for short in not_needed_shorts:
                self.create_log(activity='Close unnecessary short')
                self.rebalance_position('buy', self.short_positions[short], short)

    def check_if_need_rebalance(self, token):
        short = self.short_positions[token]
        floor = self.pools_positions[token]['floor']
        ceiling = self.pools_positions[token]['ceiling']
        if floor <= short <= ceiling:
            """do nothing"""
            pass
        elif short > ceiling:
            diff = short - ceiling
            diff = diff if diff < short * 0.1 else short * 0.1
            self.rebalance_position('buy', diff, token)
        elif short < floor:
            diff = floor - short
            diff = diff if diff < short * 0.1 else short * 0.1
            self.rebalance_position('sell', diff, token)

    # todo add this to thread because it may execute long time
    def rebalance_position(self, side, size, token):
        start_time = time.time()
        future_market = token + '-PERP'

        while (filled_size := sum([order['filledSize'] for order in
                                   self.get_order_history(future_market, start_time=start_time)])) < size:
            self.cancel_orders(future_market, limit_orders=True)
            price = get_middle_price_for_futures_order(token)
            remained_size = size - filled_size
            self.prepare_order(side, remained_size, future_market, price)
            time.sleep(60)

        self.short_positions = self.update_short_position()
        self.create_log(activity='Position rebalanced', side=side, filled_size=filled_size, token=token)

    def prepare_order(self, side, size, future_market, price):
        if self.liquidation_soon():
            # todo add if liquidation is soon
            pass
        else:
            # todo as we add bigger order, we need to adjust liquidation check
            # https://docs.google.com/spreadsheets/d/1tIegr-Y7flkOk5VJEbC6W9pN8CTkr0O4kFniR338FO0/edit#gid=1609882044
            try:
                self.place_order(market=future_market, side=side, price=price, size=size, type='limit')
                self.create_log(activity=f'Placed {side} order for {size} on {future_market.split("-")[0]} at {price}')
            except Exception as err:
                if str(err) == 'Size too small':
                    r = -decimal.Decimal(str(size)).as_tuple().exponent
                    size = float(str(size)[:-1] + '9')
                    size = round(size, r - 1)
                    self.prepare_order(side, size, future_market, price)
                else:
                    print(err)

    def liquidation_soon(self):
        return False
        # try:
        #     liquidation_price = self.get_position(self.future_market)['estimatedLiquidationPrice']
        # except TypeError:
        #     liquidation_price = float('inf')
        # if liquidation_price < self.second_token_price * 3:  # todo liquidation treshold??
        #     self.create_log('liquidation soon')
        #     message = f'Liquidation price is {liquidation_price}, token price is {self.second_token_price}. Consider adding more liquidity to the account'
        #     telegram_bot_sendtext(message)
        #     return True
    
    def create_log(self, activity: str, side=None, filled_size=None, token=None):

        log_file = f"logging/log_{self.cid}.txt"

        format_log = "%(asctime)s: %(message)s"
        logging.basicConfig(format=format_log, level=logging.INFO, filename=log_file, datefmt="%H:%M:%S")

        if filled_size:
            log = {
                "activity": activity,
                f"{token} in pool:": self.pools_positions[token]['amount'],
                "short position: ": self.short_positions[token],
                "rebalance_corridor": f"{self.pools_positions[token]['floor']} - {self.pools_positions[token]['ceiling']}",
            }

        else:
            log = {
                "activity": activity,
            }

        if re.match(r'Placed', activity):
            telegram_bot_sendtext(activity)
        log = json.dumps(log)
        logging.info(log)

    # def send_common_log(self):
    #     coverage = round(self.short_position / self.second_token_amount_pool, 2)
    #     message = f'{self.second_token} market. Short position: {round(self.short_position, 0)}, ' \
    #               f'token in pool: {round(self.second_token_amount_pool, 0)}. ' \
    #               f'Coverage: {coverage}. Target: {1 + (self.target - self.rebalance) / 100} - {1 + (self.target + self.rebalance) / 100}'
    #     telegram_bot_sendtext(message)
