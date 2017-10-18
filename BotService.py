# -*- coding: utf-8 -*-
import flask
import telebot
from flask import Flask


def run_app(bot, main_vars):
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
        if message.chat.id not in main_vars.allowed_chat_ids:
            main_vars.bot.send_message(message.chat.id, 'Данный чат не является разрешенным для работы с ботом')
            return
        start_task = {
            'task_id': main_vars.id,
            'task_type': 'start',
            'chat_id': message.chat.id
        }
        main_vars.task_queue.append(start_task)
        main_vars.id += 1

    @bot.message_handler(commands=['help'])
    def help(message):
        if message.chat.id not in main_vars.allowed_chat_ids:
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
        if message.chat.id not in main_vars.allowed_chat_ids:
            bot.send_message(message.chat.id, 'Данный чат не является разрешенным для работы с ботом')
            return
        stop_task = {
            'task_id': main_vars.id,
            'task_type': 'stop',
            'chat_id': message.chat.id
        }
        main_vars.task_queue.append(stop_task)
        main_vars.id += 1

    @bot.message_handler(commands=['config'])
    def config(message):
        if message.chat.id not in main_vars.allowed_chat_ids:
            bot.send_message(message.chat.id, 'Данный чат не является разрешенным для работы с ботом')
            return
        config_task = {
            'task_id': main_vars.id,
            'task_type': 'config',
            'chat_id': message.chat.id
        }
        main_vars.task_queue.append(config_task)
        main_vars.id += 1

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

    # @bot.message_handler(commands=['domain'])
    # def save_en_domain(message):
    #     if message.chat.id not in allowed_chat_ids:
    #         bot.send_message(message.chat.id, 'Данный чат не является разрешенным для работы с ботом')
    #         return
    #     if session.active:
    #         session.config['en_domain'] = str(message.text[8:])
    #         reply = 'Домен успешно задан' if session.config else 'Домен не задан, повторите (/domain http://demo.en.cx)'
    #         bot.send_message(message.chat.id, reply)

    # @bot.message_handler(commands=['gameid'])
    # def save_game_id(message):
    #     if message.chat.id not in allowed_chat_ids:
    #         bot.send_message(message.chat.id, 'Данный чат не является разрешенным для работы с ботом')
    #         return
    #     if session.active:
    #         session.config['game_id'] = str(message.text[8:])
    #         reply = 'Игра успешно задана' if session.config else 'Игра не задана, повторите (/gameid 26991)'
    #         bot.send_message(message.chat.id, reply)

    @bot.message_handler(commands=['login'])
    def login(message):
        if message.chat.id not in main_vars.allowed_chat_ids:
            bot.send_message(message.chat.id, 'Данный чат не является разрешенным для работы с ботом')
            return
        login_task = {
            'task_id': main_vars.id,
            'task_type': 'login',
            'chat_id': message.chat.id
        }
        main_vars.task_queue.append(login_task)
        main_vars.id += 1

    @bot.message_handler(commands=['task'])
    def send_task(message):
        if message.chat.id not in main_vars.allowed_chat_ids:
            bot.send_message(message.chat.id, 'Данный чат не является разрешенным для работы с ботом')
            return
        send_task_task = {
            'task_id': main_vars.id,
            'task_type': 'send_task',
            'chat_id': message.chat.id
        }
        main_vars.task_queue.append(send_task_task)
        main_vars.id += 1

    # @bot.message_handler(commands=['sectors'])
    # def send_all_sectors(message):
    #     if message.chat.id not in allowed_chat_ids:
    #         bot.send_message(message.chat.id, 'Данный чат не является разрешенным для работы с ботом')
    #         return
    #     if session.active:
    #         session.send_all_sectors(bot, message.chat.id)

    # @bot.message_handler(commands=['helps'])
    # def send_all_helps(message):
    #     if message.chat.id not in allowed_chat_ids:
    #         bot.send_message(message.chat.id, 'Данный чат не является разрешенным для работы с ботом')
    #         return
    #     if session.active:
    #         session.send_all_helps(bot, message.chat.id)
    #
    # @bot.message_handler(commands=['last_help'])
    # def send_last_help(message):
    #     if session.active:
    #         session.send_last_help(bot, message.chat.id)
    #
    # @bot.message_handler(commands=['bonuses'])
    # def send_all_bonuses(message):
    #     if session.active:
    #         session.send_all_bonuses(bot, message.chat.id)

    @bot.message_handler(commands=['start_updater'])
    def start_updater(message):
        if message.chat.id not in main_vars.allowed_chat_ids:
            bot.send_message(message.chat.id, 'Данный чат не является разрешенным для работы с ботом')
            return
        start_updater_task = {
            'task_id': main_vars.id,
            'task_type': 'start_updater',
            'chat_id': message.chat.id
        }
        main_vars.task_queue.append(start_updater_task)
        main_vars.id += 1

    # @bot.message_handler(commands=['delay'])
    # def updater_delay(message):
    #     if message.chat.id not in allowed_chat_ids:
    #         bot.send_message(message.chat.id, 'Данный чат не является разрешенным для работы с ботом')
    #         return
    #     if session.active:
    #         session.updater.delay = int(message.text[7:])

    @bot.message_handler(commands=['stop_updater'])
    def stop_updater(message):
        if message.chat.id not in main_vars.allowed_chat_ids:
            bot.send_message(message.chat.id, 'Данный чат не является разрешенным для работы с ботом')
            return
        stop_updater_task = {
            'task_id': main_vars.id,
            'task_type': 'stop_updater',
            'chat_id': message.chat.id
        }
        main_vars.task_queue.append(stop_updater_task)
        main_vars.id += 1

    # @bot.message_handler(commands=['set_channel_name'])
    # def set_channel_name(message):
    #     if message.chat.id not in allowed_chat_ids:
    #         bot.send_message(message.chat.id, 'Данный чат не является разрешенным для работы с ботом')
    #         return
    #     if session.active:
    #         session.channel_name = str(message.text[18:])
    #
    # @bot.message_handler(commands=['start_channel'])
    # def use_channel_true(message):
    #     if message.chat.id not in allowed_chat_ids:
    #         bot.send_message(message.chat.id, 'Данный чат не является разрешенным для работы с ботом')
    #         return
    #     if session.active:
    #         session.use_channel = True
    #         bot.send_message(message.chat.id, 'Постинг в канал запущен')
    #
    # @bot.message_handler(commands=['stop_channel'])
    # def use_channel_false(message):
    #     if message.chat.id not in allowed_chat_ids:
    #         bot.send_message(message.chat.id, 'Данный чат не является разрешенным для работы с ботом')
    #         return
    #     if session.active:
    #         session.use_channel = False
    #         bot.send_message(message.chat.id, 'Постинг в канал остановлен')

    # @bot.message_handler(content_types=['text'])
    # def text_processor(message):
    #     if message.chat.id not in allowed_chat_ids:
    #         bot.send_message(message.chat.id, 'Данный чат не является разрешенным для работы с ботом')
    #         return
    #     if session.active:
    #         coords = re.findall(
    #             r'\d\d\.\d{4,7},\s\d\d\.\d{4,7}|\d\d\.\d{4,7}\s\d\d\.\d{4,7}|\d\d\.\d{4,7}\r\n\d\d\.\d{4,7}',
    #             message.text)
    #         if message.text[0] == '!':
    #             code = (message.text[1:]).lower().encode('utf-8') if message.text[1] != ' ' \
    #                 else (message.text[2:]).lower().encode('utf-8')
    #             session.send_code_to_level(code, bot, message.chat.id, message.message_id)
    #         elif message.text[0] == '?':
    #             code = (message.text[1:]).lower().encode('utf-8') if message.text[1] != ' ' \
    #                 else (message.text[2:]).lower().encode('utf-8')
    #             session.send_code_to_level(code, bot, message.chat.id, message.message_id, bonus_only=True)
    #         elif coords:
    #             for coord in coords:
    #                 latitude = re.findall(r'\d\d\.\d{4,7}', coord)[0]
    #                 longitude = re.findall(r'\d\d\.\d{4,7}', coord)[1]
    #                 bot.send_location(message.chat.id, latitude, longitude)
    #         else:
    #             return

    # Remove webhook, it fails sometimes the set if there is a previous webhook
    bot.remove_webhook()

    # Set webhook
    bot.set_webhook(url='https://5d1aa3e2.ngrok.io/webhook')

    @app.route("/", methods=['GET', 'POST'])
    def hello():
        return "Hello World!"

    return app
