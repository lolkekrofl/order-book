import os.path
import time

import telebot
import config

WAIT_MSG = "Please wait finish of the build process.."
FILE_SIZE_LIMIT = 2 ** 20
PAUSE = 10

bot = telebot.TeleBot(config.TOKEN)
orders = set()


def get_file(name, pic):
    expected_file = add_to_queue(name, pic)
    while True:
        if os.path.exists(expected_file):
            return expected_file
        time.sleep(PAUSE)


def add_to_queue(name, picture):
    # just template
    # call build queue, add name, pic to it, return generated name
    return "/tmp/build.me"


@bot.message_handler(content_types=['photo'])
def handle_photo(message):
    user_id = message.from_user.id
    pic = message.photo[-1]

    if not message.caption:
        bot.send_message(user_id, f"Don't forget to add a caption")
    elif pic.file_size > FILE_SIZE_LIMIT:
        bot.send_message(user_id, f"File is too big, only 1Mb is allowed")
    else:
        bot.send_message(user_id, WAIT_MSG)
        orders.add(user_id)
        file_name = get_file(name=message.caption, pic=pic.file_id)
        with open(file_name, 'rb') as data:
            bot.send_document(user_id, data)

        orders.remove(user_id)


@bot.message_handler(content_types=['text'])
def handle_text(message):
    user_id = message.from_user.id

    if user_id not in orders:
        bot.send_message(message.from_user.id, "Please attach pic with required name")
    else:
        bot.send_message(user_id, WAIT_MSG)


bot.polling(none_stop=True, interval=0)
