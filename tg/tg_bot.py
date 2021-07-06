# https://pypi.org/project/pyTelegramBotAPI/0.3.0/
# https://github.com/eternnoir/pyTelegramBotAPI#general-api-documentation
# emoji - https://apps.timwhitlock.info/emoji/tables/unicode
# threading https://stackoverflow.com/questions/33655229/initiate-a-parallel-process-from-within-a-python-script
# todo add threading

import telebot
import config
import random
import re
import json

from mongo.mongo import update_user_db, check_if_user_exist, delete_user, add_hedge, print_user_position, print_specific_pool, \
    delete_pool, edit_pool_ib_db
from telebot import types
from telebot.types import InlineKeyboardMarkup

bot = telebot.TeleBot(config.TOKEN)

user_dict = {}
user_position = {}
user_pool = {}


class User:
    def __init__(self, cid):
        self.cid = cid
        self.api_s = None
        self.api_k = None
        self.subaccount = None

    def get_data(self):
        text = f"""
    Your data:
Api key: {self.api_k}
Api secret: {self.api_s}
Subaccount: {self.subaccount}
            """
        return text


class Position:
    def __init__(self, cid):
        self.cid = cid
        self.coin_one = ""
        self.coin_two = ""
        self.coin_one_amount = None
        self.coin_two_amount = None
        self.target = None
        self.fluctuation = None

    def get_data(self):
        text = f"""
    Your data:
Pool: {self.coin_one} - {self.coin_two}
Amount: {self.coin_one_amount} - {self.coin_two_amount}
Target: {self.target} +- {self.fluctuation}%
            """
        return text


@bot.message_handler(commands=['start'])
def welcome(message):
    snowman = u'\U000026C4'
    info = u'\U00002139'
    computer = u'\U0001F4BB'
    whale = u'\U0001F40B'
    correct = u'\U00002705'
    incorrect = u'\U0000274C'
    down = u'\U0001F447'

    # keyboard
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=3)
    item1 = types.KeyboardButton(computer + " Total data")
    item2 = types.KeyboardButton(snowman + " Current Hedge")
    item3 = types.KeyboardButton(computer + " Add New Hedge")
    item4 = types.KeyboardButton(whale + " Account")
    item5 = types.KeyboardButton(computer + " Start/Stop Bot")

    item6 = types.KeyboardButton(info + " Help")

    markup.add(item1, item2, item3, item4, item5, item6)

    bot.send_message(message.chat.id,
                     "Добро пожаловать, {0.first_name}!\nЯ - <b>{1.first_name}</b>, бот созданный чтобы быть подопытным кроликом.".format(
                         message.from_user, bot.get_me()),
                     parse_mode='html', reply_markup=markup)


# todo change the welcome text


@bot.message_handler(regexp='Account')
def account_button(message):
    cid = message.chat.id
    if check_if_user_exist(cid) is False:
        markup = types.InlineKeyboardMarkup(row_width=1)
        item1 = types.InlineKeyboardButton("Register", callback_data='register account')
        markup.add(item1)
        bot.send_message(cid, 'Press to start registration \U0001F447', reply_markup=markup)
    else:
        user_data = check_if_user_exist(cid)
        user = User(cid)
        user.api_s = user_data["api"]["api-secret"]
        user.api_k = user_data["api"]["api-key"]
        user.subaccount = user_data["api"]["sub-account"]
        user_dict[cid] = user
        markup = types.InlineKeyboardMarkup(row_width=2)
        item2 = types.InlineKeyboardButton("Update", callback_data='update account')
        item3 = types.InlineKeyboardButton("Delete", callback_data='delete account')
        markup.add(item2, item3)

        bot.send_message(cid, user.get_data(), reply_markup=markup)


@bot.message_handler(regexp='Current Hedge')
def current_hedge_button(message):
    cid = message.chat.id
    if check_if_user_exist(cid) is False:
        bot.send_message(cid, 'Register user before you can perform this action')
    markup = types.InlineKeyboardMarkup(row_width=1)
    item1 = types.InlineKeyboardButton("Edit pools", callback_data='edit pools')
    markup.add(item1)
    bot.send_message(cid, print_user_position(cid)[0], reply_markup=markup)
#     todo add help handler


@bot.message_handler(regexp='Add New Hedge')
def add_new_hedge_button(message):
    cid = message.chat.id
    if check_if_user_exist(cid) is False:
        bot.send_message(cid, 'Register user before you can perform this action')
    else:
        markup = types.InlineKeyboardMarkup(row_width=2)
        item1 = types.InlineKeyboardButton("Coin - Stable LP", callback_data='single LP')
        item2 = types.InlineKeyboardButton("Coin - Coin LP", callback_data='double LP')
        markup.add(item1, item2)
        bot.send_message(cid, 'Choose the type of pool', reply_markup=markup)


@bot.message_handler(regexp='Stop Bot')
def stop_bot_button(message):
    cid = message.chat.id
    if check_if_user_exist(cid) is False:
        bot.send_message(cid, 'Register user before you can perform this action')
    bot.send_message(cid, 'Pressed Stop Bot Button')
#     todo add help handler


@bot.message_handler(regexp='Help')
def help_button(message):
    cid = message.chat.id
    bot.send_message(cid, 'Pressed Help Button')
#     todo add help handler


@bot.callback_query_handler(lambda query: query.data in ["register account", "update account", "save account", "delete account"])
def registration_callback_inline(call):
    try:
        if call.message:
            cid = call.message.chat.id
            if call.data == 'register account':
                user = User(cid)
                user_dict[cid] = user
                msg_api_key = bot.send_message(cid, 'Provide your FTX api key :')
                bot.register_next_step_handler(msg_api_key, registration_step_api_key)
            #     https://github.com/eternnoir/pyTelegramBotAPI/blob/master/examples/step_example.py

            elif call.data == 'update account':
                msg_api_key = bot.send_message(cid, 'Provide your FTX api key :')
                bot.register_next_step_handler(msg_api_key, registration_step_api_key)
            elif call.data == 'delete account':
                # todo "Are you sure question" and stop bot function and description that bot will stop
                delete_user(cid)
                bot.send_message(cid, 'Account deleted!')
            elif call.data == 'save account':
                update_user_db(user=user_dict[cid])
                bot.send_message(cid, 'Account saved!')
                user_dict.pop(cid)

    except Exception as e:
        print(repr(e))


def registration_step_api_key(message):
    cid = message.chat.id
    user = user_dict[cid]
    user.api_k = message.text
    msg_api_secret = bot.send_message(cid, 'Provide your FTX api secret :')
    bot.register_next_step_handler(msg_api_secret, registration_step_api_secret)


def registration_step_api_secret(message):
    cid = message.chat.id
    user = user_dict[cid]
    user.api_s = message.text
    msg_subaccount = bot.send_message(cid, 'Provide your FTX subaccount :')
    bot.register_next_step_handler(msg_subaccount, registration_step_subaccount)


def registration_step_subaccount(message):
    cid = message.chat.id
    user = user_dict[cid]
    user.subaccount = message.text

    item1 = types.InlineKeyboardButton(u'\U00002705' + " Correct", callback_data='save account')
    item2 = types.InlineKeyboardButton(u'\U0000274C' + " Incorrect", callback_data='register account')

    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.add(item1, item2)

    bot.send_message(cid, user.get_data(), reply_markup=markup)


# @bot.callback_query_handler(func=lambda call: True)
@bot.callback_query_handler(lambda query: query.data in ["single LP", "double LP", "save hedge"])
def new_hedge_callback_inline(call):
    try:
        if call.message:
            cid = call.message.chat.id
            if call.data == 'single LP':
                position = Position(cid)
                user_position[cid] = position
                msg_first_coin = bot.send_message(cid, 'What coin do you want to hedge (for example, "ETH"): ')
                bot.register_next_step_handler(msg_first_coin, new_single_hedge_step_coins)

            elif call.data == 'double LP':
                bot.send_message(cid, 'not ready yet, do not know how to handle 2 target, 2 flucuation')
                # position = Position(cid)
                # user_position[cid] = position
                # msg_first_coin = bot.send_message(cid, 'First coin you want to hedge:')
                # bot.register_next_step_handler(msg_first_coin, new_double_hedge_step_coin_one)

            elif call.data == 'save hedge':
                if user_pool:
                    position = user_position[cid]
                    pool = list(user_pool.keys())[0]
                    edit_pool_ib_db(cid, pool, position)
                    user_pool.pop(pool)
                    bot.send_message(cid, 'Pool updated')
                else:
                    add_hedge(position=user_position[cid])
                    bot.send_message(cid, 'Hedge added')
                user_position.pop(cid)

    except Exception as e:
        print(repr(e))


@bot.callback_query_handler(lambda query: query.data in ["edit pools", "delete pool", "edit pool"])
def edit_pools_callback_inline(call, message=None):
    try:
        if call.message:
            cid = call.message.chat.id
            if call.data == 'edit pools':
                msg_edit_pool = bot.send_message(cid, 'What pool to edit :')
                bot.register_next_step_handler(msg_edit_pool, edit_pool_step)

            elif call.data == 'delete pool':
                pool = list(user_pool.keys())[0]
                delete_pool(cid, pool)
                user_pool.pop(pool)
                bot.send_message(cid, f'Pool {pool} has been deleted!')

            elif call.data == 'edit pool':
                pool = list(user_pool.keys())[0]
                position = Position(cid)
                position.coin_one = list(user_pool[pool]['tokens'].keys())[0]
                position.coin_two = list(user_pool[pool]['tokens'].keys())[1]
                user_position[cid] = position
                msg_edit_pool = bot.send_message(cid, f'Amount of the {position.coin_one} in pool:')
                bot.register_next_step_handler(msg_edit_pool, new_hedge_step_amount_coin_one)

    except Exception as e:
        print(repr(e))


def edit_pool_step(message):
    cid = message.chat.id
    pool_number = int(message.text)
    result = print_specific_pool(cid, pool_number)
    user_pool[pool_number] = json.loads(result)

    item1 = types.InlineKeyboardButton("Edit", callback_data='edit pool')
    item2 = types.InlineKeyboardButton("Delete", callback_data='delete pool')

    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.add(item1, item2)
    bot.send_message(cid, result, reply_markup=markup)


def new_double_hedge_step_coin_one(message):
    cid = message.chat.id
    position = user_position[cid]
    position.coin_one = message.text.upper()
    msg_second_coin = bot.send_message(cid, 'Second coin you want to hedge (for example, "BTC"):')
    bot.register_next_step_handler(msg_second_coin, new_double_hedge_step_coin_two)


def new_double_hedge_step_coin_two(message):
    cid = message.chat.id
    position = user_position[cid]
    position.coin_two = message.text.upper()
    msg_first_coin_amount = bot.send_message(cid, f'Amount of the {position.coin_one} in pool:')
    bot.register_next_step_handler(msg_first_coin_amount, new_hedge_step_amount_coin_one)
#     todo 2 target, 2 flucuation


def new_single_hedge_step_coins(message):
    cid = message.chat.id
    position = user_position[cid]
    position.coin_one = message.text.upper()
    position.coin_two = 'USD'
    msg_first_coin_amount = bot.send_message(cid, f'Amount of the {position.coin_one} in pool:')
    bot.register_next_step_handler(msg_first_coin_amount, new_hedge_step_amount_coin_one)


def new_hedge_step_amount_coin_one(message):
    cid = message.chat.id
    position = user_position[cid]
    text = message.text
    if ',' in text:
        text = text.replace(",", ".")
    position.coin_one_amount = float(text)
    msg_second_coin_amount = bot.send_message(cid, f'Amount of the {position.coin_two} in pool:')
    bot.register_next_step_handler(msg_second_coin_amount, new_hedge_step_amount_coin_two)


def new_hedge_step_amount_coin_two(message):
    cid = message.chat.id
    position = user_position[cid]
    text = message.text
    if ',' in text:
        text = text.replace(",", ".")
    position.coin_two_amount = float(text)
    msg_target_position = bot.send_message(cid, 'What is you target short position? in % of pool. >100% when generally short about the coin, <100% when generally long about the coin')
    bot.register_next_step_handler(msg_target_position, new_hedge_step_target)


def new_hedge_step_target(message):
    cid = message.chat.id
    position = user_position[cid]
    text = message.text
    if ',' in text:
        text = text.replace(",", ".")
    position.target = float(text)
    msg_fluctuation_position = bot.send_message(cid, 'What fluctuation? In percent')
    bot.register_next_step_handler(msg_fluctuation_position, new_hedge_step_fluctuation)
#     todo add information about fluctuation


def new_hedge_step_fluctuation(message):
    cid = message.chat.id
    position = user_position[cid]
    position.fluctuation = int(message.text)

    item1 = types.InlineKeyboardButton(u'\U00002705' + " Correct", callback_data='save hedge')
    item2 = types.InlineKeyboardButton(u'\U0000274C' + " Incorrect", callback_data='single LP')

    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.add(item1, item2)

    bot.send_message(cid, position.get_data(), reply_markup=markup)







# @bot.message_handler(content_types=['text'])
# def keyboard_handler(message):
#     if message.chat.type == 'private':
#         if re.search('status', message.text.lower()):
#             bot.send_message(message.chat.id, 'Pressed status button')
#         elif re.search('registration', message.text.lower()):
#             bot.send_message(message.chat.id, 'Pressed registration button')
#         elif re.search('help', message.text.lower()):
#             bot.send_message(message.chat.id, 'Pressed help button')
#         elif message.text == '😊 Как дела?':
#
#             markup = types.InlineKeyboardMarkup(row_width=2)
#             item1 = types.InlineKeyboardButton("Хорошо", callback_data='good')
#             item2 = types.InlineKeyboardButton("Не очень", callback_data='bad')
#
#             markup.add(item1, item2)
#
#             bot.send_message(message.chat.id, 'Отлично, сам как?', reply_markup=markup)
#         else:
#             bot.send_message(message.chat.id, 'I don\'t understand. Please call /help')


# RUN
bot.polling(none_stop=True)
