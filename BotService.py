# -*- coding: utf-8 -*-
import flask
import re
import telebot
from flask import Flask
from Const import helptext
from DBMethods import DB
from MainClasses import Task, Validations


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

    # refactored
    @bot.message_handler(commands=['ask_for_permission'])
    def ask_for_permission(message):
        main_chat_ids, _ = DB.get_allowed_chat_ids()
        if message.chat.id in main_chat_ids:
            bot.send_message(message.chat.id, 'Данный чат уже разрешен для работы с ботом')
            return
        text = '<b>%s</b> запрашивает разрешение на работу с ботом из чата "%s"\r\nchat_id: %s' % \
               (str(message.from_user.username.encode('utf-8')), str(message.chat.title.encode('utf-8')),
                str(message.chat.id))
        bot.send_message(45839899, text, parse_mode='HTML')

    # refactored
    @bot.message_handler(commands=['join'])
    def join_session(message):
        allowed, main_chat_ids, add_chat_ids = Validations.check_permission(message.chat.id, bot)
        if allowed \
                and Validations.check_session_available(message.chat.id, bot, main_vars.sessions_dict.keys()) \
                and Validations.check_join_possible(message.chat.id, bot, message.from_user.id, message.message_id, add_chat_ids):
            join_task = Task(message.chat.id, 'join', message_id=message.message_id, user_id=message.from_user.id)
            main_vars.task_queue.append(join_task)

    # refactored
    @bot.message_handler(commands=['reset_join'])
    def reset_join(message):
        allowed, main_chat_ids, add_chat_ids = Validations.check_permission(message.chat.id, bot)
        if allowed \
                and Validations.check_session_available(message.chat.id, bot, main_vars.sessions_dict.keys()) \
                and Validations.check_reset_join_possible(message.chat.id, bot, message.from_user.id, message.message_id, add_chat_ids):
            reset_join_task = Task(message.chat.id, 'reset_join', message_id=message.message_id, user_id=message.from_user.id)
            main_vars.task_queue.append(reset_join_task)

    # refactored
    @bot.message_handler(commands=['add'])
    def add_chat_to_allowed(message):
        if message.chat.id != 45839899:
            bot.send_message(message.chat.id, 'Данная команда не доступна из этого чата')
            return
        chat_id = int(re.search(r'[-\d]+', str(message.text.encode('utf-8'))).group(0))
        DB.insert_main_chat_id(chat_id)
        main_chat_ids, _ = DB.get_allowed_chat_ids()
        if chat_id in main_chat_ids:
            bot.send_message(chat_id, 'Этот чат добавлен в список разрешенных для работы с ботом')
        else:
            bot.send_message(chat_id, 'Этот чат не добавлен в список разрешенных для работы с ботом'
                                      '\r\nДля повторного запроса введите /ask_for_permission')

    # refactored
    @bot.message_handler(commands=['start'])
    def start(message):
        allowed, _, _ = Validations.check_permission(message.chat.id, bot)
        if allowed:
            start_task = Task(message.chat.id, 'start', sessions_dict=main_vars.sessions_dict)
            main_vars.task_queue.append(start_task)

    # refactored
    @bot.message_handler(commands=['help'])
    def help(message):
        allowed, _, _ = Validations.check_permission(message.chat.id, bot)
        if allowed:
            bot.send_message(message.chat.id, helptext)

    # refactored
    @bot.message_handler(commands=['start_session'])
    def start_session(message):
        allowed, main_chat_ids, add_chat_ids = Validations.check_permission(message.chat.id, bot)
        if allowed and Validations.check_session_available(message.chat.id, bot, main_vars.sessions_dict.keys()):
            session = Task.get_session(message.chat.id, add_chat_ids, main_vars.sessions_dict)
            start_session_task = Task(message.chat.id, 'start_sesion', session=session)
            main_vars.task_queue.append(start_session_task)

    # refactored
    @bot.message_handler(commands=['stop_session'])
    def stop_session(message):
        allowed, main_chat_ids, add_chat_ids = Validations.check_permission(message.chat.id, bot)
        if allowed and Validations.check_session_available(message.chat.id, bot, main_vars.sessions_dict.keys()) \
                and Validations.check_from_main_chat(message.chat.id, bot, main_chat_ids, message.message_id):

            session = Task.get_session(message.chat.id, add_chat_ids, main_vars.sessions_dict)
            stop_session_task = Task(message.chat.id, 'start_sesion', session=session,
                                     add_chat_ids_per_session=DB.get_add_chat_ids_for_main(message.chat.id))
            main_vars.task_queue.append(stop_session_task)

    # refactored
    @bot.message_handler(commands=['config'])
    def config(message):
        allowed, main_chat_ids, add_chat_ids = Validations.check_permission(message.chat.id, bot)
        if allowed and Validations.check_session_available(message.chat.id, bot, main_vars.sessions_dict.keys()) \
                and Validations.check_from_main_chat(message.chat.id, bot, main_chat_ids, message.message_id):

            session = Task.get_session(message.chat.id, add_chat_ids, main_vars.sessions_dict)
            config_task = Task(message.chat.id, 'config', session=session)
            main_vars.task_queue.append(config_task)

    # refactored
    @bot.message_handler(commands=['login'])
    def save_login(message):
        allowed, main_chat_ids, add_chat_ids = Validations.check_permission(message.chat.id, bot)
        if allowed and Validations.check_session_available(message.chat.id, bot, main_vars.sessions_dict.keys()) \
                and Validations.check_from_main_chat(message.chat.id, bot, main_chat_ids, message.message_id):

            session = Task.get_session(message.chat.id, add_chat_ids, main_vars.sessions_dict)
            new_login = re.findall(r'/login\s*(.+)', str(message.text.encode('utf-8')))[0]
            set_login_task = Task(message.chat.id, 'login', session=session, new_login=new_login)
            main_vars.task_queue.append(set_login_task)

    # refactored
    @bot.message_handler(commands=['password'])
    def save_password(message):
        allowed, main_chat_ids, add_chat_ids = Validations.check_permission(message.chat.id, bot)
        if allowed and Validations.check_session_available(message.chat.id, bot, main_vars.sessions_dict.keys()) \
                and Validations.check_from_main_chat(message.chat.id, bot, main_chat_ids, message.message_id):

            session = Task.get_session(message.chat.id, add_chat_ids, main_vars.sessions_dict)
            new_password = re.findall(r'/password\s*(.+)', str(message.text.encode('utf-8')))[0]
            set_password_task = Task(message.chat.id, 'password', session=session, new_password=new_password)
            main_vars.task_queue.append(set_password_task)

    # refactored
    @bot.message_handler(commands=['domain'])
    def save_en_domain(message):
        allowed, main_chat_ids, add_chat_ids = Validations.check_permission(message.chat.id, bot)
        if allowed and Validations.check_session_available(message.chat.id, bot, main_vars.sessions_dict.keys()) \
                and Validations.check_from_main_chat(message.chat.id, bot, main_chat_ids, message.message_id):

            session = Task.get_session(message.chat.id, add_chat_ids, main_vars.sessions_dict)
            new_domain = re.findall(r'/domain\s*(.+)', str(message.text.encode('utf-8')))[0]
            set_domain_task = Task(message.chat.id, 'domain', session=session, new_domain=new_domain)
            main_vars.task_queue.append(set_domain_task)

    # refactored
    @bot.message_handler(commands=['gameid'])
    def save_game_id(message):
        allowed, main_chat_ids, add_chat_ids = Validations.check_permission(message.chat.id, bot)
        if allowed and Validations.check_session_available(message.chat.id, bot, main_vars.sessions_dict.keys()) \
                and Validations.check_from_main_chat(message.chat.id, bot, main_chat_ids, message.message_id):

            session = Task.get_session(message.chat.id, add_chat_ids, main_vars.sessions_dict)
            new_game_id = re.search(r'[\d]+', str(message.text.encode('utf-8'))).group(0)
            set_game_id_task = Task(message.chat.id, 'game_id', session=session, new_game_id=new_game_id)
            main_vars.task_queue.append(set_game_id_task)

    # refactored
    @bot.message_handler(commands=['login_to_en'])
    def login_to_en(message):
        allowed, main_chat_ids, add_chat_ids = Validations.check_permission(message.chat.id, bot)
        if allowed and Validations.check_session_available(message.chat.id, bot, main_vars.sessions_dict.keys()) \
                and Validations.check_from_main_chat(message.chat.id, bot, main_chat_ids, message.message_id):

            session = Task.get_session(message.chat.id, add_chat_ids, main_vars.sessions_dict)
            login_to_en_task = Task(message.chat.id, 'login_to_en', session=session)
            main_vars.task_queue.append(login_to_en_task)

    # refactored
    @bot.message_handler(commands=['task'])
    def send_task(message):
        allowed, main_chat_ids, add_chat_ids = Validations.check_permission(message.chat.id, bot)
        if allowed and Validations.check_session_available(message.chat.id, bot, main_vars.sessions_dict.keys()):

            session = Task.get_session(message.chat.id, add_chat_ids, main_vars.sessions_dict)
            storm_level = int(re.search(r'[\d]+', str(message.text.encode('utf-8'))).group(0)) if \
                re.findall(r'[\d]+', str(message.text.encode('utf-8'))) else None
            send_task_task = Task(message.chat.id, 'send_task', session=session, storm_level_number=storm_level)
            main_vars.task_queue.append(send_task_task)

    # refactored
    @bot.message_handler(commands=['task_images'])
    def send_task_images(message):
        allowed, main_chat_ids, add_chat_ids = Validations.check_permission(message.chat.id, bot)
        if allowed and Validations.check_session_available(message.chat.id, bot, main_vars.sessions_dict.keys()) \
                and Validations.check_from_main_chat(message.chat.id, bot, main_chat_ids, message.message_id):

            session = Task.get_session(message.chat.id, add_chat_ids, main_vars.sessions_dict)
            send_task_images_task = Task(message.chat.id, 'task_images', session=session)
            main_vars.task_queue.append(send_task_images_task)

    @bot.message_handler(commands=['sectors'])
    def send_all_sectors(message):
        storm_level = int(re.search(r'[\d]+', str(message.text.encode('utf-8'))).group(0)) if \
            re.findall(r'[\d]+', str(message.text.encode('utf-8'))) else None
        if message.chat.id in main_vars.allowed_chats:
            send_all_sectors_task = {
                'task_type': 'send_sectors',
                'chat_id': message.chat.id,
                'additional_chat_id': None,
                'storm_level': storm_level
            }
            main_vars.task_queue.append(send_all_sectors_task)
        elif message.chat.id in main_vars.additional_ids.keys():
            send_all_sectors_task = {
                'task_type': 'send_sectors',
                'chat_id': None,
                'additional_chat_id': message.chat.id,
                'storm_level': storm_level
            }
            main_vars.task_queue.append(send_all_sectors_task)
        else:
            bot.send_message(message.chat.id,
                             'Данный чат не является ни основным, ни дополнительным разрешенным для работы с ботом\r\n'
                             'Для отправки запроса на разрешение введите /ask_for_permission')

    @bot.message_handler(commands=['hints'])
    def send_all_helps(message):
        storm_level = int(re.search(r'[\d]+', str(message.text.encode('utf-8'))).group(0)) if \
            re.findall(r'[\d]+', str(message.text.encode('utf-8'))) else None
        if message.chat.id in main_vars.allowed_chats:
            send_all_helps_task = {
                'task_type': 'send_helps',
                'chat_id': message.chat.id,
                'additional_chat_id': None,
                'storm_level': storm_level
            }
            main_vars.task_queue.append(send_all_helps_task)
        elif message.chat.id in main_vars.additional_ids.keys():
            send_all_helps_task = {
                'task_type': 'send_helps',
                'chat_id': None,
                'additional_chat_id': message.chat.id,
                'storm_level': storm_level
            }
            main_vars.task_queue.append(send_all_helps_task)
        else:
            bot.send_message(message.chat.id,
                             'Данный чат не является ни основным, ни дополнительным разрешенным для работы с ботом\r\n'
                             'Для отправки запроса на разрешение введите /ask_for_permission')

    @bot.message_handler(commands=['last_hint'])
    def send_last_help(message):
        storm_level = int(re.search(r'[\d]+', str(message.text.encode('utf-8'))).group(0)) if \
            re.findall(r'[\d]+', str(message.text.encode('utf-8'))) else None
        if message.chat.id in main_vars.allowed_chats:
            send_last_help_task = {
                'task_type': 'send_last_help',
                'chat_id': message.chat.id,
                'additional_chat_id': None,
                'storm_level': storm_level
            }
            main_vars.task_queue.append(send_last_help_task)
        elif message.chat.id in main_vars.additional_ids.keys():
            send_last_help_task = {
                'task_type': 'send_last_help',
                'chat_id': None,
                'additional_chat_id': message.chat.id,
                'storm_level': storm_level
            }
            main_vars.task_queue.append(send_last_help_task)
        else:
            bot.send_message(message.chat.id,
                             'Данный чат не является ни основным, ни дополнительным разрешенным для работы с ботом\r\n'
                             'Для отправки запроса на разрешение введите /ask_for_permission')

    @bot.message_handler(commands=['bonuses'])
    def send_all_bonuses(message):
        storm_level = int(re.search(r'[\d]+', str(message.text.encode('utf-8'))).group(0)) if \
            re.findall(r'[\d]+', str(message.text.encode('utf-8'))) else None
        if message.chat.id in main_vars.allowed_chats:
            send_all_bonuses_task = {
                'task_type': 'send_bonuses',
                'chat_id': message.chat.id,
                'additional_chat_id': None,
                'storm_level': storm_level
            }
            main_vars.task_queue.append(send_all_bonuses_task)
        elif message.chat.id in main_vars.additional_ids.keys():
            send_all_bonuses_task = {
                'task_type': 'send_bonuses',
                'chat_id': None,
                'additional_chat_id': message.chat.id,
                'storm_level': storm_level
            }
            main_vars.task_queue.append(send_all_bonuses_task)
        else:
            bot.send_message(message.chat.id,
                             'Данный чат не является ни основным, ни дополнительным разрешенным для работы с ботом\r\n'
                             'Для отправки запроса на разрешение введите /ask_for_permission')

    @bot.message_handler(commands=['unclosed_bonuses'])
    def send_unclosed_bonuses(message):
        storm_level = int(re.search(r'[\d]+', str(message.text.encode('utf-8'))).group(0)) if \
            re.findall(r'[\d]+', str(message.text.encode('utf-8'))) else None
        if message.chat.id in main_vars.allowed_chats:
            send_unclosed_bonuses_task = {
                'task_type': 'unclosed_bonuses',
                'chat_id': message.chat.id,
                'additional_chat_id': None,
                'storm_level': storm_level
            }
            main_vars.task_queue.append(send_unclosed_bonuses_task)
        elif message.chat.id in main_vars.additional_ids.keys():
            send_unclosed_bonuses_task = {
                'task_type': 'unclosed_bonuses',
                'chat_id': None,
                'additional_chat_id': message.chat.id,
                'storm_level': storm_level
            }
            main_vars.task_queue.append(send_unclosed_bonuses_task)
        else:
            bot.send_message(message.chat.id,
                             'Данный чат не является ни основным, ни дополнительным разрешенным для работы с ботом\r\n'
                             'Для отправки запроса на разрешение введите /ask_for_permission')

    @bot.message_handler(commands=['messages'])
    def send_auth_messages(message):
        storm_level = int(re.search(r'[\d]+', str(message.text.encode('utf-8'))).group(0)) if \
            re.findall(r'[\d]+', str(message.text.encode('utf-8'))) else None
        if message.chat.id in main_vars.allowed_chats:
            send_auth_messages_task = {
                'task_type': 'send_messages',
                'chat_id': message.chat.id,
                'additional_chat_id': None,
                'storm_level': storm_level
            }
            main_vars.task_queue.append(send_auth_messages_task)
        elif message.chat.id in main_vars.additional_ids.keys():
            send_auth_messages_task = {
                'task_type': 'send_messages',
                'chat_id': None,
                'additional_chat_id': message.chat.id,
                'storm_level': storm_level
            }
            main_vars.task_queue.append(send_auth_messages_task)
        else:
            bot.send_message(message.chat.id,
                             'Данный чат не является ни основным, ни дополнительным разрешенным для работы с ботом\r\n'
                             'Для отправки запроса на разрешение введите /ask_for_permission')

    @bot.message_handler(commands=['start_updater'])
    def start_updater(message):
        if message.chat.id not in main_vars.allowed_chats:
            bot.send_message(message.chat.id, 'Данный чат не является разрешенным для работы с ботом\r\n'
                                              'Для отправки запроса на разрешение введите /ask_for_permission')
            return
        start_updater_task = {
            'task_type': 'start_updater',
            'chat_id': message.chat.id
        }
        main_vars.task_queue.append(start_updater_task)

    @bot.message_handler(commands=['delay'])
    def set_updater_delay(message):
        if message.chat.id not in main_vars.allowed_chats:
            bot.send_message(message.chat.id, 'Данный чат не является разрешенным для работы с ботом\r\n'
                                              'Для отправки запроса на разрешение введите /ask_for_permission')
            return
        set_delay_task = {
            'task_type': 'delay',
            'chat_id': message.chat.id,
            'new_delay': int(re.search(r'[\d]+', str(message.text.encode('utf-8'))).group(0))
        }
        main_vars.task_queue.append(set_delay_task)

    @bot.message_handler(commands=['stop_updater'])
    def stop_updater(message):
        if message.chat.id not in main_vars.allowed_chats:
            bot.send_message(message.chat.id, 'Данный чат не является разрешенным для работы с ботом\r\n'
                                              'Для отправки запроса на разрешение введите /ask_for_permission')
            return
        stop_updater_task = {
            'task_type': 'stop_updater',
            'chat_id': message.chat.id
        }
        main_vars.task_queue.append(stop_updater_task)

    @bot.message_handler(commands=['set_channel_name'])
    def set_channel_name(message):
        if message.chat.id not in main_vars.allowed_chats:
            bot.send_message(message.chat.id, 'Данный чат не является разрешенным для работы с ботом\r\n'
                                              'Для отправки запроса на разрешение введите /ask_for_permission')
            return
        set_channel_name_task = {
            'task_type': 'channel_name',
            'chat_id': message.chat.id,
            'new_channel_name': re.findall(r'/set_channel_name\s*(.+)', str(message.text.encode('utf-8')))[0]
        }
        main_vars.task_queue.append(set_channel_name_task)
        main_vars.id += 1

    @bot.message_handler(commands=['start_channel'])
    def start_channel(message):
        if message.chat.id not in main_vars.allowed_chats:
            bot.send_message(message.chat.id, 'Данный чат не является разрешенным для работы с ботом\r\n'
                                              'Для отправки запроса на разрешение введите /ask_for_permission')
            return
        start_channel_task = {
            'task_type': 'start_channel',
            'chat_id': message.chat.id
        }
        main_vars.task_queue.append(start_channel_task)

    @bot.message_handler(commands=['stop_channel'])
    def stop_channel(message):
        if message.chat.id not in main_vars.allowed_chats:
            bot.send_message(message.chat.id, 'Данный чат не является разрешенным для работы с ботом\r\n'
                                              'Для отправки запроса на разрешение введите /ask_for_permission')
            return
        stop_channel_task = {
            'task_type': 'stop_channel',
            'chat_id': message.chat.id
        }
        main_vars.task_queue.append(stop_channel_task)

    @bot.message_handler(commands=['codes_on'])
    def enable_codes(message):
        if message.chat.id not in main_vars.allowed_chats:
            bot.send_message(message.chat.id, 'Данный чат не является разрешенным для работы с ботом\r\n'
                                              'Для отправки запроса на разрешение введите /ask_for_permission')
            return
        enable_codes_task = {
            'task_type': 'codes_on',
            'chat_id': message.chat.id
        }
        main_vars.task_queue.append(enable_codes_task)

    @bot.message_handler(commands=['codes_off'])
    def disable_codes(message):
        if message.chat.id not in main_vars.allowed_chats:
            bot.send_message(message.chat.id, 'Данный чат не является разрешенным для работы с ботом\r\n'
                                              'Для отправки запроса на разрешение введите /ask_for_permission')
            return
        disable_codes_task = {
            'task_type': 'codes_off',
            'chat_id': message.chat.id
        }
        main_vars.task_queue.append(disable_codes_task)

    @bot.message_handler(commands=['add_tag'])
    def add_tag(message):
        if message.chat.id != 45839899:
            bot.send_message(message.chat.id, 'Данная команда не доступна из этого чата')
            return
        tag_to_add = re.findall(r'/add_tag\s*(.+)', str(message.text.encode('utf-8')))[0]
        DB.insert_tag_in_tags_list(tag_to_add)
        if tag_to_add in DB.get_tags_list():
            bot.send_message(message.chat.id, 'Тег успешно добавлен в обработчик')
        else:
            bot.send_message(message.chat.id, 'Тег не добавлен в обработчикб повторите попытку')

    @bot.message_handler(commands=['send_ll'])
    def send_live_location(message):
        coords = re.findall(r'\d\d\.\d{4,7},\s{0,3}\d\d\.\d{4,7}|'
                            r'\d\d\.\d{4,7}\s{0,3}\d\d\.\d{4,7}|'
                            r'\d\d\.\d{4,7}\r\n\d\d\.\d{4,7}|'
                            r'\d\d\.\d{4,7},\r\n\d\d\.\d{4,7}', message.text)
        seconds = re.findall(r'\ss(\d+)', str(message.text.encode('utf-8')))[0]
        if message.chat.id in main_vars.allowed_chats:
            send_live_location_task = {
                'task_type': 'live_location',
                'chat_id': message.chat.id,
                'additional_chat_id': None,
                'coords': coords,
                'duration': int(seconds) if seconds else None
            }
            main_vars.task_queue.append(send_live_location_task)
        elif message.chat.id in main_vars.additional_ids.keys():
            send_live_location_task = {
                'task_type': 'live_location',
                'chat_id': None,
                'additional_chat_id': message.chat.id,
                'coords': coords,
                'duration': int(seconds) if seconds else None
            }
            main_vars.task_queue.append(send_live_location_task)
        else:
            bot.send_message(message.chat.id,
                             'Данный чат не является ни основным, ни дополнительным разрешенным для работы с ботом\r\n'
                             'Для отправки запроса на разрешение введите /ask_for_permission')

    @bot.message_handler(commands=['stop_ll'])
    def stop_live_location(message):
        point_number = re.search(r'\s(\d{1,2})\s', str(message.text.encode('utf-8')))
        if message.chat.id in main_vars.allowed_chats:
            stop_live_location_task = {
                'task_type': 'stop_live_location',
                'chat_id': message.chat.id,
                'additional_chat_id': None,
                'point': int(point_number.group(0)) if point_number else None
            }
            main_vars.task_queue.append(stop_live_location_task)
        elif message.chat.id in main_vars.additional_ids.keys():
            stop_live_location_task = {
                'task_type': 'stop_live_location',
                'chat_id': None,
                'additional_chat_id': message.chat.id,
                'point': int(point_number.group(0)) if point_number else None,
            }
            main_vars.task_queue.append(stop_live_location_task)
        else:
            bot.send_message(message.chat.id,
                             'Данный чат не является ни основным, ни дополнительным разрешенным для работы с ботом\r\n'
                             'Для отправки запроса на разрешение введите /ask_for_permission')

    @bot.message_handler(commands=['edit_ll'])
    def edit_live_location(message):
        if message.chat.id not in main_vars.allowed_chats and message.chat.id not in main_vars.additional_ids.keys():
            bot.send_message(message.chat.id,
                             'Данный чат не является ни основным, ни дополнительным разрешенным для работы с ботом\r\n'
                             'Для отправки запроса на разрешение введите /ask_for_permission')
            return
        coords = re.findall(r'\d\d\.\d{4,7},\s{0,3}\d\d\.\d{4,7}|'
                            r'\d\d\.\d{4,7}\s{0,3}\d\d\.\d{4,7}|'
                            r'\d\d\.\d{4,7}\r\n\d\d\.\d{4,7}|'
                            r'\d\d\.\d{4,7},\r\n\d\d\.\d{4,7}', message.text)
        point_number = re.search(r'\s(\d{1,2})\s', str(message.text.encode('utf-8')))
        if message.chat.id in main_vars.allowed_chats:
            edit_live_location_task = {
                'task_type': 'edit_live_location',
                'chat_id': message.chat.id,
                'additional_chat_id': None,
                'point': int(point_number.group(0)) if point_number else None,
                'coords': coords
            }
            main_vars.task_queue.append(edit_live_location_task)
        if message.chat.id in main_vars.additional_ids.keys():
            edit_live_location_task = {
                'task_type': 'edit_live_location',
                'chat_id': None,
                'additional_chat_id': message.chat.id,
                'point': int(point_number.group(0)) if point_number else None,
                'coords': coords
            }
            main_vars.task_queue.append(edit_live_location_task)

    @bot.message_handler(commands=['add_points_ll'])
    def add_points_live_location(message):
        points_dict = dict()
        points = re.findall(r'\d{1,2}\s*-\s*\d\d\.\d{4,7},\s{,3}\d\d\.\d{4,7}|'
                            r'\d{1,2}\s*-\s*\d\d\.\d{4,7}\s{1,3}\d\d\.\d{4,7}', str(message.text.encode('utf-8')))
        for point in points:
            i = int(re.findall(r'(\d{1,2})\s*-', point)[0])
            points_dict[i] = re.findall(r'\d\d\.\d{4,7},\s{,3}\d\d\.\d{4,7}|'
                                        r'\d\d\.\d{4,7}\s{1,3}\d\d\.\d{4,7}', point)[0]
        if not points_dict:
            bot.send_message(message.chat.id, 'Нет точек, для отправки live_locations. Верный формат:\n'
                                              '1 - корды\n2 - корды\n...\nn - корды')
        seconds = re.findall(r'\ss(\d+)', str(message.text.encode('utf-8')))[0]
        if message.chat.id in main_vars.allowed_chats:
            add_points_ll_task = {
                'task_type': 'add_points_ll',
                'chat_id': message.chat.id,
                'additional_chat_id': None,
                'points_dict': points_dict,
                'duration': int(seconds) if seconds else None
            }
            main_vars.task_queue.append(add_points_ll_task)
        elif message.chat.id in main_vars.additional_ids.keys():
            add_points_ll_task = {
                'task_type': 'add_points_ll',
                'chat_id': None,
                'additional_chat_id': message.chat.id,
                'points_dict': points_dict,
                'duration': int(seconds) if seconds else None
            }
            main_vars.task_queue.append(add_points_ll_task)
        else:
            bot.send_message(message.chat.id,
                             'Данный чат не является ни основным, ни дополнительным разрешенным для работы с ботом\r\n'
                             'Для отправки запроса на разрешение введите /ask_for_permission')

    @bot.message_handler(content_types=['text'])
    def text_processor(message):
        if message.chat.id not in main_vars.allowed_chats and message.chat.id not in main_vars.additional_ids.keys():
            bot.send_message(message.chat.id,
                             'Данный чат не является ни основным, ни дополнительным разрешенным для работы с ботом\r\n'
                             'Для отправки запроса на разрешение введите /ask_for_permission')
            return
        coords = re.findall(r'\d\d\.\d{4,7},\s{0,3}\d\d\.\d{4,7}|'
                            r'\d\d\.\d{4,7}\s{0,3}\d\d\.\d{4,7}|'
                            r'\d\d\.\d{4,7}\r\n\d\d\.\d{4,7}|'
                            r'\d\d\.\d{4,7},\r\n\d\d\.\d{4,7}', message.text)
        if message.text[0] == '!':
            code = re.findall(r'!\s*(.+)', str(message.text.lower().encode('utf-8')))[0]
            if message.chat.id in main_vars.allowed_chats:
                send_code_main_task = {
                    'task_type': 'send_code_main',
                    'chat_id': message.chat.id,
                    'additional_chat_id': None,
                    'message_id': message.message_id,
                    'code': code
                }
                main_vars.task_queue.append(send_code_main_task)
            else:
                send_code_main_task = {
                    'task_type': 'send_code_main',
                    'chat_id': None,
                    'additional_chat_id': message.chat.id,
                    'message_id': message.message_id,
                    'code': code
                }
                main_vars.task_queue.append(send_code_main_task)
            return
        if message.text[0] == '?':
            code = re.findall(r'\?\s*(.+)', str(message.text.lower().encode('utf-8')))[0]
            if message.chat.id in main_vars.allowed_chats:
                send_code_bonus_task = {
                    'task_type': 'send_code_bonus',
                    'chat_id': message.chat.id,
                    'additional_chat_id': None,
                    'message_id': message.message_id,
                    'code': code
                }
                main_vars.task_queue.append(send_code_bonus_task)
            else:
                send_code_bonus_task = {
                    'task_type': 'send_code_bonus',
                    'chat_id': None,
                    'additional_chat_id': message.chat.id,
                    'message_id': message.message_id,
                    'code': code
                }
                main_vars.task_queue.append(send_code_bonus_task)
            return
        if coords and message.chat.id in main_vars.allowed_chats:
            send_coords_task = {
                'task_type': 'send_coords',
                'chat_id': message.chat.id,
                'coords': coords
            }
            main_vars.task_queue.append(send_coords_task)

    # Remove webhook, it fails sometimes the set if there is a previous webhook
    bot.remove_webhook()

    # Set webhook
    # bot.set_webhook(url='https://powerful-shelf-32284.herokuapp.com/webhook')
    bot.set_webhook(url='https://25286a0a.ngrok.io/webhook')

    @app.route("/", methods=['GET', 'POST'])
    def hello():
        return 'Hello world!'

    @app.route("/develop/DB/connectorcheck", methods=['GET', 'POST'])
    def db_conn_check():
        list_of_tags = 'List of tags:'
        for tag in DB.get_tags_list():
            list_of_tags += '<br>' + tag
        return list_of_tags

    return app
