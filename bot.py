import os.path
import time

import telebot
import config

WAIT_MSG = "Please wait finish of the build process.."
FILE_SIZE_LIMIT = 2 ** 20
PAUSE = 10
SCENARIO = 'name', 'id', 'file', 'confirmation', 'waiting'

bot = telebot.TeleBot(config.TOKEN)
orders = dict()


@bot.message_handler(content_types=['text'])
def handle_text(message):
    user_id = message.from_user.id

    if user_id not in orders:   # hello stage
        orders[user_id] = {'stage': SCENARIO[0]}
        bot.send_message(user_id, "Hello. Please give me name of app..")
    else:
        text = message.text
        record = orders[user_id]
        if record['stage'] == SCENARIO[0]:    # name
            record['name'] = text
            bot.send_message(user_id, "..id of app..")
            record['stage'] = SCENARIO[1]
        elif record['stage'] == SCENARIO[1]:  # id
            record['id'] = text
            bot.send_message(user_id, "..and attach icon file please")
            record['stage'] = SCENARIO[2]
        elif record['stage'] == SCENARIO[2]:    # icon
            bot.send_message(user_id, "Wrong input")
        elif record['stage'] == SCENARIO[3]:    # confirmation
            if text.lower() in ('y', 'yes'):
                bot.send_message(user_id, "Your order added to queue")
                # todo: save base (use for recovery)

                record['stage'] = SCENARIO[4]   # waiting
            else:
                del orders[user_id]
                bot.send_message(user_id, "Your order cancelled.")


@bot.message_handler(content_types=['document'])
def handle_document(message):
    user_id = message.from_user.id
    if user_id not in orders:
        return

    record = orders[user_id]
    if record["stage"] != SCENARIO[2]:
        return

    document = message.document
    if document.file_size > FILE_SIZE_LIMIT:
        bot.send_message(user_id, f"File is too big, only 1Mb is allowed")
    else:
        # todo: download document.file_id and write it to disk
        msg = f"Your order is recorded({record['name']}:{record['id']}).\nPlease confirm it (Yes/No)"
        bot.send_message(user_id, msg)
        record["stage"] = SCENARIO[3]

        #with open(file_name, "rb") as data:
        #    bot.send_document(user_id, data, caption="Your order is ready")


bot.polling(none_stop=True, interval=0)
