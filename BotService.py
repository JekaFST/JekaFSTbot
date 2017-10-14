# -*- coding: utf-8 -*-
import threading
import flask
import re
import telebot
from flask import Flask
from BotSession import BotSession
from Updater import Updater

allowed_chat_ids = [45839899, -1001145974445, -1001076545820, -1001116652124, -1001126631174]
session = BotSession()
updater = Updater()
bot = telebot.TeleBot('370362982:AAH5ojKT0LSw8jS-vLfDF1bDE8rWWDyTeso')
app = Flask(__name__)


#Process webhook calls
@app.route('/webhook', methods=['GET', 'POST'])
def webhook():
    if flask.request.headers.get('content-type') == 'application/json':
        json_string = flask.request.get_data().decode('utf-8')
        update = telebot.types.Update.de_json(json_string)
        bot.process_new_updates([update])
        return ''
    else:
        flask.abort(403)


@bot.message_handler(commands=['start'])
def start(message):
    if message.chat.id not in allowed_chat_ids:
        bot.send_message(message.chat.id, 'Данный чат не является разрешенным для работы с ботом')
        return
    bot.send_message(message.chat.id, 'Чтобы начать использовать бота, необходимо задать конфигурацию игры:\n'
                                      'ввести домен игры (/domain http://deadline.en.cx)\n'
                                      'ввести game id игры (/gameid 59833)\n'
                                      'и залогиниться в движок (/login)\n'
                                      'Краткое описание доступно по команде /help', disable_web_page_preview=True)
    session.active = True


@bot.message_handler(commands=['help'])
def help(message):
    if message.chat.id not in allowed_chat_ids:
        bot.send_message(message.chat.id, 'Данный чат не является разрешенным для работы с ботом')
        return
    bot.send_message(message.chat.id, 'Коды сдавать в виде !код или ! код\n'
                                      'Сдавать коды в бонусное окно в виде ?код или ? код\n'
                                      'Если бот перестал присылать обновления - '
                                      'попробуйте презапустить слежение: /start_updater\n'
                                      '/task - прислать задание\n'
                                      '/sectors - прислать список секторов\n'
                                      '/helps - прислать все подсказки\n'
                                      '/last_help - прислать последнюю пришедшую подсказку\n'
                                      '/bonuses - прислать бонусы\n'
                                      '/start_updater - запустить слежение\n'
                                      '/stop_updater - остановить слежение\n'
                                      '/set_channel_name - задать имя канала для репостинга (через пробел)\n'
                                      '/start_channel - запустить постинг в канал\n'
                                      '/stop_channel - остановить постинг в канал\n'
                                      '/stop - выключить бота и сбросить настройки\n'
                                      '/config - прислать конфигурацию,\n'
                                      '/delay - выставить интервал слежения')


@bot.message_handler(commands=['stop'])
def stop(message):
    if message.chat.id not in allowed_chat_ids:
        bot.send_message(message.chat.id, 'Данный чат не является разрешенным для работы с ботом')
        return
    bot.send_message(message.chat.id, 'Бот выключен. Настройки сброшены')
    session.active = False
    session.config['en_domain'] = ''
    session.config['game_id'] = ''
    # session.channel_name = ''
    session.updater.stop_updater = True
    session.use_channel = False


@bot.message_handler(commands=['config'])
def config(message):
    if message.chat.id not in allowed_chat_ids:
        bot.send_message(message.chat.id, 'Данный чат не является разрешенным для работы с ботом')
        return
    session_condition = 'Сессия активна' if session.active else 'Сессия не активна'
    reply = '\r\nДомен: ' + session.config['en_domain'] + '\r\nID игры: ' + session.config['game_id'] +\
            '\r\nЛогин: ' + session.config['Login']
    bot.send_message(message.chat.id, session_condition + reply, disable_web_page_preview=True)


# @bot.message_handler(commands=['login'])
# def save_login(message):
#     if message.chat.id not in allowed_chat_ids:
#         bot.send_message(message.chat.id, 'Данный чат не является разрешенным для работы с ботом')
#         return
#     if session.active:
#         session.config['Login'] = str(message.text[7:])
#
#
# @bot.message_handler(commands=['password'])
# def save_password(message):
#     if message.chat.id not in allowed_chat_ids:
#         bot.send_message(message.chat.id, 'Данный чат не является разрешенным для работы с ботом')
#         return
#     if session.active:
#         session.config['Password'] = str(message.text[10:])


@bot.message_handler(commands=['domain'])
def save_en_domain(message):
    if message.chat.id not in allowed_chat_ids:
        bot.send_message(message.chat.id, 'Данный чат не является разрешенным для работы с ботом')
        return
    if session.active:
        session.config['en_domain'] = str(message.text[8:])
        reply = 'Домен успешно задан' if session.config else 'Домен не задан, повторите (/domain http://demo.en.cx)'
        bot.send_message(message.chat.id, reply)


@bot.message_handler(commands=['gameid'])
def save_game_id(message):
    if message.chat.id not in allowed_chat_ids:
        bot.send_message(message.chat.id, 'Данный чат не является разрешенным для работы с ботом')
        return
    if session.active:
        session.config['game_id'] = str(message.text[8:])
        reply = 'Игра успешно задана' if session.config else 'Игра не задана, повторите (/gameid 26991)'
        bot.send_message(message.chat.id, reply)


@bot.message_handler(commands=['login'])
def login(message):
    if message.chat.id not in allowed_chat_ids:
        bot.send_message(message.chat.id, 'Данный чат не является разрешенным для работы с ботом')
        return
    if session.active:
        session.make_urls()
        session.updater = updater
        reply = session.login_to_en(bot, message.chat.id)
        bot.send_message(message.chat.id, reply)


@bot.message_handler(commands=['task'])
def send_task(message):
    if message.chat.id not in allowed_chat_ids:
        bot.send_message(message.chat.id, 'Данный чат не является разрешенным для работы с ботом')
        return
    if session.active:
        session.send_task(bot, message.chat.id)


@bot.message_handler(commands=['sectors'])
def send_all_sectors(message):
    if message.chat.id not in allowed_chat_ids:
        bot.send_message(message.chat.id, 'Данный чат не является разрешенным для работы с ботом')
        return
    if session.active:
        session.send_all_sectors(bot, message.chat.id)


@bot.message_handler(commands=['helps'])
def send_all_helps(message):
    if message.chat.id not in allowed_chat_ids:
        bot.send_message(message.chat.id, 'Данный чат не является разрешенным для работы с ботом')
        return
    if session.active:
        session.send_all_helps(bot, message.chat.id)


@bot.message_handler(commands=['last_help'])
def send_last_help(message):
    if session.active:
        session.send_last_help(bot, message.chat.id)


@bot.message_handler(commands=['bonuses'])
def send_all_bonuses(message):
    if session.active:
        session.send_all_bonuses(bot, message.chat.id)


@bot.message_handler(commands=['start_updater'])
def start_updater(message):
    if message.chat.id not in allowed_chat_ids:
        bot.send_message(message.chat.id, 'Данный чат не является разрешенным для работы с ботом')
        return
    if session.active:
        session.updater.stop_updater = False
        th1 = threading.Thread(name='th1', target=session.updater.updater, args=(session, bot, message.chat.id))
        th1.start()
        th1.join()


@bot.message_handler(commands=['delay'])
def start_updater(message):
    if message.chat.id not in allowed_chat_ids:
        bot.send_message(message.chat.id, 'Данный чат не является разрешенным для работы с ботом')
        return
    if session.active:
        session.updater.delay = int(message.text[7:])


@bot.message_handler(commands=['stop_updater'])
def stop_updater(message):
    if message.chat.id not in allowed_chat_ids:
        bot.send_message(message.chat.id, 'Данный чат не является разрешенным для работы с ботом')
        return
    if session.active:
        session.updater.stop_updater = True


@bot.message_handler(commands=['set_channel_name'])
def set_channel_name(message):
    if message.chat.id not in allowed_chat_ids:
        bot.send_message(message.chat.id, 'Данный чат не является разрешенным для работы с ботом')
        return
    if session.active:
        session.channel_name = str(message.text[18:])


@bot.message_handler(commands=['start_channel'])
def use_channel_true(message):
    if message.chat.id not in allowed_chat_ids:
        bot.send_message(message.chat.id, 'Данный чат не является разрешенным для работы с ботом')
        return
    if session.active:
        session.use_channel = True
        bot.send_message(message.chat.id, 'Постинг в канал запущен')


@bot.message_handler(commands=['stop_channel'])
def use_channel_false(message):
    if message.chat.id not in allowed_chat_ids:
        bot.send_message(message.chat.id, 'Данный чат не является разрешенным для работы с ботом')
        return
    if session.active:
        session.use_channel = False
        bot.send_message(message.chat.id, 'Постинг в канал остановлен')


@bot.message_handler(content_types=['text'])
def text_processor(message):
    if message.chat.id not in allowed_chat_ids:
        bot.send_message(message.chat.id, 'Данный чат не является разрешенным для работы с ботом')
        return
    if session.active:
        coords = re.findall(r'\d\d\.\d{4,7},\s\d\d\.\d{4,7}|\d\d\.\d{4,7}\s\d\d\.\d{4,7}|\d\d\.\d{4,7}\r\n\d\d\.\d{4,7}',
                           message.text)
        if message.text[0] == '!':
            code = (message.text[1:]).lower().encode('utf-8') if message.text[1] != ' ' \
                else (message.text[2:]).lower().encode('utf-8')
            session.send_code_to_level(code, bot, message.chat.id, message.message_id)
        elif message.text[0] == '?':
            code = (message.text[1:]).lower().encode('utf-8') if message.text[1] != ' ' \
                else (message.text[2:]).lower().encode('utf-8')
            session.send_code_to_level(code, bot, message.chat.id, message.message_id, bonus_only=True)
        elif coords:
            for coord in coords:
                latitude = re.findall(r'\d\d\.\d{4,7}', coord)[0]
                longitude = re.findall(r'\d\d\.\d{4,7}', coord)[1]
                bot.send_location(message.chat.id, latitude, longitude)
        else:
            return


# Remove webhook, it fails sometimes the set if there is a previous webhook
bot.remove_webhook()

# Set webhook
bot.set_webhook(url='https://f7dc30da.ngrok.io/webhook')


@app.route("/", methods=['GET', 'POST'])
def hello():
    return "Hello World!"


@app.route("/config", methods=['GET', 'POST'])
def config():
    return flask.jsonify(session.config)


@app.route("/urls", methods=['GET', 'POST'])
def urls():
    return flask.jsonify(session.urls)


# @app.route("/game_model_current", methods=['GET', 'POST'])
# def current_game_model():
#     game_url_js = make_game_url_js(config_dict)
#     cookie = get_cookie(config_dict)
#     current_game_model = get_current_game_model(game_url_js, cookie)
#     return flask.jsonify(current_game_model)


@app.route("/current_level_info", methods=['GET', 'POST'])
def current_level_info():
    return flask.jsonify(session.current_level)


if __name__ == "__main__":
    app.run(host='0.0.0.0', port=443, debug=False)
