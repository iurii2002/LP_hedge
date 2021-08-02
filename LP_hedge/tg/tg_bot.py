# -*- coding: utf-8 -*-

import telebot
import json
from telebot import types

from LP_hedge.tg.config_tg import TOKEN
from LP_hedge.tg.instances import User, Position
from LP_hedge.mongo.db_management import update_user_db, check_if_user_exist_in_db, delete_user, add_hedge, \
    print_user_pools, return_specific_pool_data, delete_pool, edit_pool_in_db, get_user_data, print_user_pivot_data
from LP_hedge.scripts.parse_ftx_data import check_if_perp_market_on_ftx
from LP_hedge.scripts.hedge_start_stop import start_hedge_process, stop_hedge_process
from LP_hedge.ftx.check_API_correctness import check_ftx_api

bot = telebot.TeleBot(TOKEN)

users_temp = {}
user_position_temp = {}
user_pool_temp = {}

main_menu_buttons = ['🔥 Total Data', '🐋 Account', '📖 Current Pools', '📝 Add New Pool', '🚦 Start/Stop Bot', 'ℹ Help']


@bot.message_handler(commands=['start'])
def welcome(message):
    """
    Main menu keyboard buttons
    """
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=3)
    item1 = types.KeyboardButton('🔥 Total Data')
    item2 = types.KeyboardButton('📖 Current Pools')
    item3 = types.KeyboardButton('📝 Add New Pool')
    item4 = types.KeyboardButton('🐋 Account')
    item5 = types.KeyboardButton('🚦 Start/Stop Bot')
    item6 = types.KeyboardButton('ℹ Help')

    markup.add(item1, item2, item3, item4, item5, item6)

    bot.send_message(message.chat.id,
                     "Hi there, {0.first_name}!\nI am a <b>{1.first_name}</b>, bot that will help you to hedge your LPs."
                     .format(message.from_user, bot.get_me()),
                     parse_mode='html', reply_markup=markup)


@bot.message_handler(regexp='🔥 Total Data')
def total_data_button(message) -> None:
    cid = message.chat.id

    if not check_if_user_exist_in_db(cid):
        bot.send_message(cid, 'Register account before you can perform this action')
        return

    user_position = print_user_pivot_data(cid)
    bot.send_message(cid, user_position)


@bot.message_handler(regexp='🐋 Account')
def account_button(message) -> None:
    cid = message.chat.id
    if user_data := get_user_data(cid):
        """Update existing user"""
        user = User(cid, api_s=user_data["api"]["api-secret"], api_k=user_data["api"]["api-key"],
                    subaccount=user_data["api"]["sub-account"])
        users_temp[cid] = user
        markup = types.InlineKeyboardMarkup(row_width=2)
        item1 = types.InlineKeyboardButton("Update", callback_data='update account')
        item2 = types.InlineKeyboardButton("Delete", callback_data='delete account')
        markup.add(item1, item2)
        bot.send_message(cid, user.print_user_data(), reply_markup=markup)

    else:
        """Register new user"""
        markup = types.InlineKeyboardMarkup(row_width=1)
        item1 = types.InlineKeyboardButton("Register", callback_data='register account')
        markup.add(item1)
        bot.send_message(cid, 'Press to start registration 👇', reply_markup=markup)


@bot.message_handler(regexp='📖 Current Pools')
def current_hedge_button(message) -> None:
    cid = message.chat.id

    if not check_if_user_exist_in_db(cid):
        bot.send_message(cid, 'Register account before you can perform this action')
        return

    user_pools = print_user_pools(cid)
    if user_pools[1] == 0:
        """
        Number of pools = 0
        """
        message = "You do not have active pools\nPlease use the 'Add New Pool' button"
        bot.send_message(cid, message)
    if user_pools[1] != 0:
        """
        Number of pools more than 0
        """
        markup = types.InlineKeyboardMarkup(row_width=1)
        item1 = types.InlineKeyboardButton("Edit pools", callback_data='edit pools')
        markup.add(item1)
        bot.send_message(cid, user_pools[0], reply_markup=markup)


@bot.message_handler(regexp='📝 Add New Pool')
def add_new_hedge_button(message) -> None:
    cid = message.chat.id

    if not check_if_user_exist_in_db(cid):
        bot.send_message(cid, 'Register account before you can perform this action')
        return

    markup = types.InlineKeyboardMarkup(row_width=2)
    item1 = types.InlineKeyboardButton("Coin - Stable LP", callback_data='single LP')
    item2 = types.InlineKeyboardButton("Coin - Coin LP", callback_data='double LP')
    markup.add(item1, item2)
    bot.send_message(cid, 'Choose the type of pool', reply_markup=markup)


@bot.message_handler(regexp='🚦 Start/Stop Bot')
def stop_bot_button(message) -> None:
    cid = message.chat.id

    if not check_if_user_exist_in_db(cid):
        bot.send_message(cid, 'Register account before you can perform this action')
        return

    data = get_user_data(cid)
    user = User(cid, status=data['status'], api_s=data['api']['api-secret'], api_k=data['api']['api-key'],
                subaccount=data['api']['sub-account'])
    users_temp[cid] = user

    current_status = user.status
    if current_status == 'passive':
        message = 'Current status: Stopped'
        item1 = types.InlineKeyboardButton("🚀 Start Bot", callback_data='Start bot')
        markup = types.InlineKeyboardMarkup(row_width=1)
        markup.add(item1)
        bot.send_message(cid, message, reply_markup=markup)

    if current_status == 'active':
        message = 'Current status: Working'
        item1 = types.InlineKeyboardButton("⛔ Stop bot", callback_data='Stop bot')
        markup = types.InlineKeyboardMarkup(row_width=1)
        markup.add(item1)
        bot.send_message(cid, message, reply_markup=markup)


@bot.message_handler(regexp='ℹ Help')
def help_button(message) -> None:
    cid = message.chat.id
    bot.send_message(cid, 'Pressed Help Button')


#     todo add help handler


@bot.callback_query_handler(lambda query: query.data in ["Start bot", "Stop bot"])
def new_hedge_callback_inline(call):
    try:
        if call.message:
            cid = call.message.chat.id
            if call.data == 'Start bot':
                user = users_temp[cid]
                user.set_status('active')
                update_user_db(user=user)
                start_hedge_process(cid)
                users_temp.pop(cid)
                bot.send_message(cid, 'Bot started')

            if call.data == 'Stop bot':
                user = users_temp[cid]
                user.set_status('passive')
                update_user_db(user=user)
                stop_hedge_process(cid)
                users_temp.pop(cid)
                bot.send_message(cid, 'Bot stopped')

    except Exception as e:
        print(repr(e))


@bot.callback_query_handler(
    lambda query: query.data in ["register account", "update account", "save account", "delete account"])
def registration_callback_inline(call) -> None:
    """
    Handler of queries from the '🐋 Account' button
    """
    try:
        if call.message:
            cid = call.message.chat.id
            if call.data == 'register account':
                # todo frequency of reporting
                user = User(cid)
                users_temp[cid] = user
                msg_api_key = bot.send_message(cid, 'Provide your FTX api key :')
                bot.register_next_step_handler(msg_api_key, registration_step_api_key)

            elif call.data == 'update account':
                msg_api_key = bot.send_message(cid, 'Provide your FTX api key :')
                bot.register_next_step_handler(msg_api_key, registration_step_api_key)

            elif call.data == 'delete account':
                # todo "Are you sure question" and stop bot function and description that bot will stop
                delete_user(cid)
                bot.send_message(cid, 'Account deleted!')
                users_temp.pop(cid)

            elif call.data == 'save account':
                user = users_temp[cid]
                if check_ftx_api(api_k=user.get_api_k(), api_s=user.get_api_s(), sub_a=user.get_subaccount()):
                    update_user_db(user=users_temp[cid])
                    users_temp.pop(cid)
                    bot.send_message(cid, 'Account saved!')
                else:
                    users_temp.pop(cid)
                    markup = types.InlineKeyboardMarkup(row_width=1)
                    item1 = types.InlineKeyboardButton("Register", callback_data='register account')
                    markup.add(item1)
                    bot.send_message(cid, 'API data is incorrect. Please try again 👇', reply_markup=markup)

    except Exception as e:
        print(repr(e))


def registration_step_api_key(message) -> None:
    cid = message.chat.id
    user = users_temp[cid]
    user.set_api_k(message.text)
    msg_api_secret = bot.send_message(cid, 'Provide your FTX api secret :')
    bot.register_next_step_handler(msg_api_secret, registration_step_api_secret)


def registration_step_api_secret(message) -> None:
    cid = message.chat.id
    user = users_temp[cid]
    user.set_api_s(message.text)
    msg_subaccount = bot.send_message(cid, 'Provide your FTX subaccount name:')
    bot.register_next_step_handler(msg_subaccount, registration_step_subaccount)


def registration_step_subaccount(message) -> None:
    cid = message.chat.id
    user = users_temp[cid]
    user.set_subaccount(message.text)

    item1 = types.InlineKeyboardButton(u'\U00002705' + " Correct", callback_data='save account')
    item2 = types.InlineKeyboardButton(u'\U0000274C' + " Incorrect", callback_data='register account')

    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.add(item1, item2)

    bot.send_message(cid, user.print_user_data(), reply_markup=markup)


@bot.callback_query_handler(lambda query: query.data in ["single LP", "double LP", "save hedge"])
def new_hedge_callback_inline(call) -> None:
    try:
        if call.message:
            cid = call.message.chat.id
            if call.data == 'single LP':
                position = Position(cid)
                user_position_temp[cid] = position
                msg_first_coin = bot.send_message(cid, 'What coin do you want to hedge (for example, "ETH"): ')
                bot.register_next_step_handler(msg_first_coin, new_single_hedge_step_coins)

            elif call.data == 'double LP':
                position = Position(cid)
                user_position_temp[cid] = position
                msg_first_coin = bot.send_message(cid, 'First coin you want to hedge (for example, "ETH"):')
                bot.register_next_step_handler(msg_first_coin, new_double_hedge_step_coin_one)

            elif call.data == 'save hedge':
                if user_pool_temp:
                    position = user_position_temp[cid]
                    pool_number = list(user_pool_temp[cid].keys())[0]
                    edit_pool_in_db(cid, pool_number, position)
                    user_pool_temp.pop(cid)
                    bot.send_message(cid, 'Pool updated')
                else:
                    position = user_position_temp[cid]
                    add_hedge(position=position)
                    bot.send_message(cid, 'Hedge added')
                user_position_temp.pop(cid)

    except Exception as e:
        print(repr(e))


@bot.callback_query_handler(lambda query: query.data in ["edit pools", "delete pool", "edit pool"])
def edit_pools_callback_inline(call) -> None:
    """
    Handler of queries from the '📖 Current Pools' button
    """
    try:
        if call.message:
            cid = call.message.chat.id
            if call.data == 'edit pools':
                msg_edit_pool = bot.send_message(cid, 'What pool to edit :')
                bot.register_next_step_handler(msg_edit_pool, edit_pool_step)

            elif call.data == 'delete pool':
                pool = list(user_pool_temp[cid].keys())[0]
                delete_pool(cid, pool)
                user_pool_temp.pop(cid)
                bot.send_message(cid, f'Pool {pool} has been deleted!')

            elif call.data == 'edit pool':
                pool = list(user_pool_temp[cid].keys())[0]
                position = Position(cid)
                position.set_coin_one(list(user_pool_temp[cid][pool]['tokens'].keys())[0])
                position.set_coin_two(list(user_pool_temp[cid][pool]['tokens'].keys())[1])
                user_position_temp[cid] = position
                if user_pool_temp[cid][pool]['pool'] == 'single':
                    msg_edit_pool = bot.send_message(cid, f'Amount of the {position.get_coin_one()} in pool:')
                    bot.register_next_step_handler(msg_edit_pool, new_single_hedge_step_amount_coin_one)
                if user_pool_temp[cid][pool]['pool'] == 'double':
                    msg_edit_pool = bot.send_message(cid, f'Amount of the {position.get_coin_one()} in pool:')
                    bot.register_next_step_handler(msg_edit_pool, new_double_hedge_step_amount_coin_one)

    except Exception as e:
        print(repr(e))


@bot.message_handler(func=lambda message: True)
def unknown_message_handler(message) -> None:
    cid = message.chat.id
    bot.send_message(cid, 'Sorry, I don\'t understand. Please use /start')


def edit_pool_step(message) -> None:
    cid = message.chat.id
    try:
        pool_number = int(message.text)
    except ValueError:
        error_msg = bot.send_message(cid, 'Please provide pool number as a digit')
        bot.register_next_step_handler(error_msg, edit_pool_step)
        return
    pool_text, pool_data = return_specific_pool_data(cid, pool_number)
    user_pool_temp[cid] = {pool_number: json.loads(pool_data)}

    item1 = types.InlineKeyboardButton("Edit", callback_data='edit pool')
    item2 = types.InlineKeyboardButton("Delete", callback_data='delete pool')

    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.add(item1, item2)
    bot.send_message(cid, pool_text, reply_markup=markup)


def new_double_hedge_step_coin_one(message) -> None:
    cid = message.chat.id
    position = user_position_temp[cid]
    user_input = message.text.upper()
    if not check_if_perp_market_on_ftx(user_input):
        error_msg = bot.send_message(cid, f'There is no {user_input} perp market on FTX. Please use another one.')
        bot.register_next_step_handler(error_msg, new_double_hedge_step_coin_one)
        return
    position.set_coin_one(user_input)
    msg_second_coin = bot.send_message(cid, 'Second coin you want to hedge (for example, "BTC"):')
    bot.register_next_step_handler(msg_second_coin, new_double_hedge_step_coin_two)


def new_double_hedge_step_coin_two(message) -> None:
    cid = message.chat.id
    position = user_position_temp[cid]
    user_input = message.text.upper()
    if not check_if_perp_market_on_ftx(user_input):
        error_msg = bot.send_message(cid,
                                     f'There is no {user_input} perp market on FTX. Please use another one. Please use another one.')
        bot.register_next_step_handler(error_msg, new_double_hedge_step_coin_two)
        return
    if user_input == position.get_coin_one():
        error_msg = bot.send_message(cid, f'Coin two should be different from the coin one.')
        bot.register_next_step_handler(error_msg, new_double_hedge_step_coin_two)
        return
    position.set_coin_two(user_input)
    msg_first_coin_amount = bot.send_message(cid, f'Amount of the {position.get_coin_one()} in pool:')
    bot.register_next_step_handler(msg_first_coin_amount, new_double_hedge_step_amount_coin_one)


def new_double_hedge_step_amount_coin_one(message) -> None:
    cid = message.chat.id
    position = user_position_temp[cid]
    user_input = message.text
    user_input = check_coma_in_number(user_input)
    try:
        amount = float(user_input)
    except ValueError:
        error_msg = bot.send_message(cid, 'Please provide amount as a digit')
        bot.register_next_step_handler(error_msg, new_double_hedge_step_amount_coin_one)
        return
    position.set_coin_one_amount(amount)
    msg_second_coin_amount = bot.send_message(cid, f'Amount of the {position.get_coin_two()} in pool:')
    bot.register_next_step_handler(msg_second_coin_amount, new_double_hedge_step_amount_coin_two)


def new_double_hedge_step_amount_coin_two(message) -> None:
    cid = message.chat.id
    position = user_position_temp[cid]
    user_input = message.text
    user_input = check_coma_in_number(user_input)
    try:
        amount = float(user_input)
    except ValueError:
        error_msg = bot.send_message(cid, 'Please provide amount as a digit')
        bot.register_next_step_handler(error_msg, new_double_hedge_step_amount_coin_two)
        return
    position.set_coin_two_amount(amount)
    msg_first_coin_target = bot.send_message(cid,
                                             f'What is you target short position for {position.get_coin_one()}, in %?\n'
                                             ' >100% when generally short about the coin, \n'
                                             '<100% when generally long about the coin')
    bot.register_next_step_handler(msg_first_coin_target, new_double_hedge_step_target_one)


def new_double_hedge_step_target_one(message) -> None:
    cid = message.chat.id
    position = user_position_temp[cid]
    user_input = message.text
    user_input = check_coma_in_number(user_input)
    try:
        amount = float(user_input)
    except ValueError:
        error_msg = bot.send_message(cid, 'Please provide amount as a digit')
        bot.register_next_step_handler(error_msg, new_double_hedge_step_target_one)
        return
    position.set_coin_one_target(amount)
    msg_fluctuation_position_coin_two = bot.send_message(cid, f'What fluctuation for {position.get_coin_one()}, in %?')
    bot.register_next_step_handler(msg_fluctuation_position_coin_two, new_double_hedge_step_fluctuation_one)


def new_double_hedge_step_fluctuation_one(message) -> None:
    cid = message.chat.id
    position = user_position_temp[cid]
    user_input = message.text
    user_input = check_coma_in_number(user_input)
    try:
        amount = float(user_input)
    except ValueError:
        error_msg = bot.send_message(cid, 'Please provide amount as a digit')
        bot.register_next_step_handler(error_msg, new_double_hedge_step_fluctuation_one)
        return
    position.set_coin_one_fluctuation(amount)
    msg_second_coin_target = bot.send_message(cid,
                                              f'What is you target short position for {position.get_coin_two()}, in %?\n'
                                              ' >100% when generally short about the coin,\n '
                                              '<100% when generally long about the coin')
    bot.register_next_step_handler(msg_second_coin_target, new_double_hedge_step_target_two)


def new_double_hedge_step_target_two(message) -> None:
    cid = message.chat.id
    position = user_position_temp[cid]
    user_input = message.text
    user_input = check_coma_in_number(user_input)
    try:
        amount = float(user_input)
    except ValueError:
        error_msg = bot.send_message(cid, 'Please provide amount as a digit')
        bot.register_next_step_handler(error_msg, new_double_hedge_step_target_two)
        return
    position.set_coin_two_target(amount)
    msg_fluctuation_position_coin_two = bot.send_message(cid, f'What fluctuation for {position.get_coin_two()}, in %?')
    bot.register_next_step_handler(msg_fluctuation_position_coin_two, new_double_hedge_step_fluctuation_two)


def new_double_hedge_step_fluctuation_two(message) -> None:
    cid = message.chat.id
    position = user_position_temp[cid]
    user_input = message.text
    user_input = check_coma_in_number(user_input)
    try:
        amount = float(user_input)
    except ValueError:
        error_msg = bot.send_message(cid, 'Please provide amount as a digit')
        bot.register_next_step_handler(error_msg, new_double_hedge_step_fluctuation_two)
        return
    position.set_coin_two_fluctuation(amount)

    item1 = types.InlineKeyboardButton(u'\U00002705' + " Correct", callback_data='save hedge')
    item2 = types.InlineKeyboardButton(u'\U0000274C' + " Incorrect", callback_data='double LP')

    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.add(item1, item2)

    bot.send_message(cid, position.print_double_position_data(), reply_markup=markup)


def new_single_hedge_step_coins(message) -> None:
    cid = message.chat.id
    position = user_position_temp[cid]
    user_input = message.text.upper()
    if not check_if_perp_market_on_ftx(user_input):
        error_msg = bot.send_message(cid, f'There is no {user_input} perp market on FTX. Please use another one.')
        bot.register_next_step_handler(error_msg, new_single_hedge_step_coins)
        return
    position.set_coin_one(user_input)
    position.coin_two = 'USD'
    msg_first_coin_amount = bot.send_message(cid, f'Amount of the {position.get_coin_one()} in pool:')
    bot.register_next_step_handler(msg_first_coin_amount, new_single_hedge_step_amount_coin_one)


def new_single_hedge_step_amount_coin_one(message) -> None:
    cid = message.chat.id
    position = user_position_temp[cid]
    user_input = message.text
    user_input = check_coma_in_number(user_input)
    try:
        amount = float(user_input)
    except ValueError:
        error_msg = bot.send_message(cid, 'Please provide amount as a digit')
        bot.register_next_step_handler(error_msg, new_single_hedge_step_amount_coin_one)
        return
    position.set_coin_one_amount(amount)
    msg_second_coin_amount = bot.send_message(cid, f'Amount of the {position.get_coin_two()} in pool:')
    bot.register_next_step_handler(msg_second_coin_amount, new_single_hedge_step_amount_coin_two)


def new_single_hedge_step_amount_coin_two(message) -> None:
    cid = message.chat.id
    position = user_position_temp[cid]
    user_input = message.text
    user_input = check_coma_in_number(user_input)
    try:
        amount = float(user_input)
    except ValueError:
        error_msg = bot.send_message(cid, 'Please provide amount as a digit')
        bot.register_next_step_handler(error_msg, new_single_hedge_step_amount_coin_two)
        return
    position.set_coin_two_amount(amount)
    msg_target_position = bot.send_message(cid, 'What is you target short position, in %?\n'
                                                '>100 when generally short about the coin,\n'
                                                '<100 when generally long about the coin')
    bot.register_next_step_handler(msg_target_position, new_single_hedge_step_target)


def new_single_hedge_step_target(message) -> None:
    cid = message.chat.id
    position = user_position_temp[cid]
    user_input = message.text
    user_input = check_coma_in_number(user_input)
    try:
        amount = float(user_input)
    except ValueError:
        error_msg = bot.send_message(cid, 'Please provide amount as a digit')
        bot.register_next_step_handler(error_msg, new_single_hedge_step_target)
        return
    position.set_coin_one_target(amount)
    msg_fluctuation_position = bot.send_message(cid, 'Fluctuation range, in %?\n'
                                                     'How much can position deviate from the target short')
    bot.register_next_step_handler(msg_fluctuation_position, new_single_hedge_step_fluctuation)


def new_single_hedge_step_fluctuation(message) -> None:
    cid = message.chat.id
    position = user_position_temp[cid]
    user_input = message.text
    user_input = check_coma_in_number(user_input)
    try:
        amount = float(user_input)
    except ValueError:
        error_msg = bot.send_message(cid, 'Please provide amount as a digit')
        bot.register_next_step_handler(error_msg, new_single_hedge_step_fluctuation)
        return
    position.set_coin_one_fluctuation(amount)

    item1 = types.InlineKeyboardButton(u'\U00002705' + " Correct", callback_data='save hedge')
    item2 = types.InlineKeyboardButton(u'\U0000274C' + " Incorrect", callback_data='single LP')

    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.add(item1, item2)

    bot.send_message(cid, position.print_single_position_data(), reply_markup=markup)


def check_coma_in_number(number: str) -> str:
    if ',' in number:
        number = number.replace(",", ".")
    return number


# RUN
def start_bot() -> None:
    bot.polling(none_stop=True)


start_bot()
