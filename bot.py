import os
import telebot

import config
from orders import OrdersQueue

WAIT_MSG = "Please wait finish of the build process.."
FILE_SIZE_LIMIT = 2 ** 20
TEMP_DIR = config.TEMP_DIR
DB_FILE = config.DB_FILE
os.makedirs(TEMP_DIR, exist_ok=True)

bot = telebot.TeleBot(config.TOKEN)
db = OrdersQueue(DB_FILE)


@bot.message_handler(content_types=['text', 'document'])
def handle_input(message):

    userid = message.from_user.id

    if userid not in db.get_users():   # hello stage
        db.record_user(userid)
        bot.send_message(userid, "Hello! Please give me name of the app")
        return
    order = db.get_order(userid)

    if order.appname is None:
        order.appname = message.text
        bot.send_message(userid, f'App name is "{order.appname}".\n'
                                 f'Now please provide the numeric ID for the app')
    elif order.appid is None:
        try:
            appid = int(message.text)
        except ValueError:
            bot.send_message(userid, 'Please provide a numeric value for the app ID')
        else:
            order.appid = appid
            bot.send_message(userid, f'App ID is {order.appid}.\n'
                                     f'Please send the icon for the app')
    elif order.appicon is None:
        if message.document is None:
            bot.send_message(userid, 'Please send the app icon as a document')
            return
        if message.document.file_size > FILE_SIZE_LIMIT:
            bot.send_message(userid, f"Your file is too big."
                                     f" Please send a file smaller than 1MB")
            return
        # todo: download document.file_id and write it to disk
        msg = f"Your order {order.appname}, ID={order.appname}" \
              "\nPlease confirm it (yes/[no])"
        bot.send_message(userid, msg)
        order.appicon = bot.download_file(
            bot.get_file(message.document.file_id).file_path
        )
    elif order.status is None:
        if message.text.lower() not in ['y', 'yes']:
            bot.send_message(userid, 'Your order is cancelled')
            order.status = 'cancelled'
            # TODO: remove cancelled and built orders in a separate async coroutine
            db.remove_order(userid)
        else:
            bot.send_message(userid, 'Your order is confirmed and queued for building')
            order.status = 'queued'

    elif order.status == 'queued':
        bot.send_message(userid, f'Your order {order} is awaiting build.')
        return

    db.update_order(order)


if __name__ == '__main__':
    bot.polling(none_stop=True, interval=0)
