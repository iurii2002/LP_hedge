import requests

# todo correct reporting


def telegram_bot_sendtext(bot_message):
    bot_token = '1635932722:AAEUIQ27kTpUKF_57FJtAeTS3cnkmaxDa3Y'
    bot_chatID = '486767090'
    send_text = 'https://api.telegram.org/bot' + bot_token + '/sendMessage?chat_id=' + \
                bot_chatID + '&parse_mode=Markdown&text=' + bot_message

    response = requests.get(send_text)

    return response.json()


