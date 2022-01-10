import os.path
import time

import telebot
import config

bot = telebot.TeleBot(config.TOKEN)
FILE_SIZE_LIMIT = 2 ** 20
PAUSE = 10


def get_file(name, pic):
    expected_file = add_to_queue(name, pic)
    while True:
        if os.path.exists(expected_file):
            return expected_file
        time.sleep(PAUSE)


def add_to_queue(name, picture):
    # template
    # call build queue, add name, pic to it, return generated name
    return ""


@bot.message_handler(content_types=['photo'])
def handle_photo(message):
    user_id = message.from_user.id
    pic = message.photo[-1]

    if not message.caption:
        bot.send_message(user_id, f"Don't forget to add a caption")
    elif pic.file_size > FILE_SIZE_LIMIT:
        bot.send_message(user_id, f"File is too big, only 1Mb is allowed")
    else:
        bot.send_message(user_id, "Please wait finish of the build process..")
        file_name = get_file(name=message.caption, pic=pic['file_id'])
        with open(file_name, 'rb') as data:
            bot.send_document(user_id, data)


@bot.message_handler(content_types=['text'])
def handle_text(message):
    bot.send_message(message.from_user.id, "Please attach pic with required name")


bot.polling(none_stop=True, interval=0)
