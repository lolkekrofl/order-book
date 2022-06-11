import os
import shutil
import time
import multiprocessing as mp
from concurrent.futures import ThreadPoolExecutor
import re

import telebot
from telebot import types

import config
from orders import OrdersQueue

FILE_SIZE_LIMIT = 2 ** 20
os.makedirs(config.TEMP_DIR, exist_ok=True)

bot = telebot.TeleBot(config.TOKEN)
db = OrdersQueue(os.path.join(config.TEMP_DIR, config.DB_FILE))


def build_orders(db: OrdersQueue):
    print(f'Build daemon started')
    while True:
        args = ((o,
                 os.path.abspath(config.BUILD_SCRIPT),
                 config.TEMP_DIR)
                for o in db.get_orders(status='queued'))
        with mp.Pool() as p:
            p.starmap(db.build_order, args)

        time.sleep(1)


def send_apks(db: OrdersQueue):
    print('Send apk daemon started')

    def send_apk(order):
        filepath = os.path.join(
            config.TEMP_DIR,
            str(order.userid),
            'TMessagesProj',
            'build', 'outputs', 'apk', 'afat', 'release', 'app.apk')
        with open(filepath, 'rb') as apkfile:
            bot.send_document(order.userid, apkfile,
                              visible_file_name=f'{order.appname}.apk')
            print(f'Sending apk to {order.userid}')
        order.status = 'completed'
        db.update_order(order)

    while True:
        with ThreadPoolExecutor() as executor:
            executor.map(send_apk, db.get_orders(status='built'))
        time.sleep(1)


def clean_orders_queue(db):
    print('Clean daemon started')
    while True:
        for order in db.get_orders():
            if order.status in ['completed', 'canceled']:
                print(f'Cleaning data for order {order}')
                db.remove_order(order.userid)
                build_dir = os.path.join(config.TEMP_DIR, str(order.userid))
                if os.path.isdir(build_dir):
                    shutil.rmtree(build_dir)
        time.sleep(1)


def send_confirmation_request(bot, order):
    msg = f"Your order {order.appname}, ID={order.appid}" \
          "\nPlease confirm it:"
    markup = types.ReplyKeyboardMarkup(row_width=2,
                                       selective=True,
                                       one_time_keyboard=True)
    yesbutton = types.KeyboardButton('Yes')
    nobutton = types.KeyboardButton('No')
    markup.add(yesbutton, nobutton)
    bot.send_message(order.userid, msg, reply_markup=markup)


@bot.message_handler(commands=['help'])
def get_help(message):
    bot.reply_to(message, """ 
    Supported commands:
    /status - get your order status
    /cancel - cancel your order
    /help - get this help
    """)


@bot.message_handler(commands=['status'])
def get_order_status(message):
    userid = message.from_user.id
    if userid not in db.get_users():
        bot.reply_to(message, 'You have made no orders yet')
        return
    order = db.get_order(userid)
    status = 'customizing'
    if order.status is not None:
        status = order.status
    bot.reply_to(message, f"""
    {order.appname} ID {order.appid}: {status}
    """)


@bot.message_handler(commands=['cancel'])
def cancel_order(message):
    userid = message.from_user.id
    if userid not in db.get_users():
        bot.reply_to(message, 'You have made no orders yet')
        return
    order = db.get_order(userid)
    order.status = 'canceled'
    db.update_order(order)
    bot.reply_to(message, 'Your order is canceled')


@bot.message_handler(content_types=['text', 'document'])
def customize_order(message):

    userid = message.from_user.id

    if userid not in db.get_users():   # hello stage
        db.record_user(userid)
        bot.send_message(userid, "Hello! Please give me name of the app")
        return
    order = db.get_order(userid)

    if order.appname is None:
        order.appname = message.text
        bot.send_message(userid, f'App name is "{order.appname}".\n'
                                 f'Now please provide the app ID '
                                 f'in the form {config.APPID_EXAMPLE}')
    elif order.appid is None:
        appid_mask = re.compile(r"^\w{2,3}\.\w+\.\w+$")
        if not appid_mask.fullmatch(message.text):
            bot.send_message(userid, 'Invalid input.\n'
                                     f'Example: {config.APPID_EXAMPLE}')
        else:
            appid = message.text.lower()
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
        order.appicon = bot.download_file(
            bot.get_file(message.document.file_id).file_path
        )
        order.status = 'confirmation'
        send_confirmation_request(bot, order)

    elif order.status == 'confirmation':
        if message.text.lower() not in ['y', 'yes']:
            order.status = 'canceled'
            bot.send_message(userid, 'Your order is cancelled')
        else:
            bot.send_message(userid, 'Your order is confirmed and queued for build')
            order.status = 'queued'
    elif order.status == 'queued':
        bot.send_message(userid, f'Your order is awaiting build.\n'
                                 f' If you want to cancel build please send /cancel')
        return

    db.update_order(order)


if __name__ == '__main__':
    build_proc = mp.Process(target=build_orders, args=(db,))
    send_proc = mp.Process(target=send_apks, args=(db,))
    clean_proc = mp.Process(target=clean_orders_queue, args=(db,))
    build_proc.start()
    send_proc.start()
    clean_proc.start()
    bot.polling(non_stop=True)
