import os

import telebot
import config

WAIT_MSG = "Please wait finish of the build process.."
FILE_SIZE_LIMIT = 2 ** 20
PAUSE = 10
SCENARIO = [
        'name',
        'id',
        'file',
        'confirmation',
        'waiting',
        'backup'
        ]  # name of the next step
TEMP_DIR = config.TEMP_DIR
os.makedirs(TEMP_DIR, exist_ok=True)


db = [] # todo: remove it
bot = telebot.TeleBot(config.TOKEN)
orders = dict()


def read_backup():
    # todo: check database, read orders if possible
    for record in db:
        orders[record['user_id']] = order = dict()
        order['name'] = record['name']
        order['id'] = record['app_id']
        order['file'] = record['icon_file']
        order['stage'] = SCENARIO[5]


def write_into_db(userid, name, app_id, icon_file):
    pass # todo


@bot.message_handler(content_types=['text'])
def handle_text(message):
    time_to_build = False

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

                # only confirmation causes db update
                write_into_db(user_id, record['name'], record['id'], record['file'])
                time_to_build = True
                record['stage'] = SCENARIO[4]   # waiting
            else:
                del orders[user_id]
                bot.send_message(user_id, "Your order cancelled.")
        # SCENARIO[4] case means just one more message from non-patient user, ignore it
        elif record['stage'] == SCENARIO[5]:     # backup - recovery mode
            time_to_build = True
            record['stage'] = SCENARIO[4]  # waiting

    if time_to_build:
        pass
        # todo:
        # while queue_non_empty: wait
        # call build script
        # while build not ready: wait
        # remove order
        # from queue
        # send build to user


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

        icon_file = bot.download_file(bot.get_file(document.file_id).file_path)
        local_file_name = os.path.join(TEMP_DIR, '-'.join(("icon", str(user_id), document.file_name)))

        with open(local_file_name, "wb") as _file:
            _file.write(icon_file)
        record["file"] = local_file_name


read_backup()
bot.polling(none_stop=True, interval=0)
