import telebot
import config
from subprocess import Popen, PIPE

bot = telebot.TeleBot(config.TOKEN)

orders = dict()
C = 1

FILE_SIZE_LIMIT = 2 ** 20
WAIT_MSG = "Please wait finish of the build process.."


def unload_orders():
    while orders:
        order = orders.pop()


def add_to_queue(name, picture):
    args = ["scipts/build.sh", name, picture]
    return Popen(args, shell=True, stdout=PIPE)


@bot.message_handler(content_types=['photo'])
def handle_photo(message):
    user_id = message.from_user.id
    pic = message.photo[-1]
    global C
    C = 2
    if not message.caption:
        bot.send_message(user_id, f"Don't forget to add a caption")
    elif pic.file_size > FILE_SIZE_LIMIT:
        bot.send_message(user_id, f"File is too big, only 1Mb is allowed")
    else:
        bot.send_message(user_id, f"I see the photo of {message.caption}")
        if user_id in orders:
            msg = "Your prev order is replaced"
        else:
            msg = "Your order is recorded"

        bot.send_message(user_id, f"{msg}. {WAIT_MSG}")

        orders[user_id] = {'caption': message.caption, 'file_id': pic['file_id']}


@bot.message_handler(content_types=['text'])
def handle_text(message):
    user_id = message.from_user.id
    if user_id in orders:
        bot.send_message(user_id, WAIT_MSG)
    else:
        bot.send_message(message.from_user.id, "Please attach pic with required name")


bot.polling(none_stop=True, interval=0)
