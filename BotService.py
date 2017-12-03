# -*- coding: utf-8 -*-
import flask
import re
import telebot
from flask import Flask
from Config import tags_list


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

    @bot.message_handler(commands=['ask_for_permission'])
    def ask_for_permission(message):
        if message.chat.id in main_vars.allowed_chats.keys():
            bot.send_message(message.chat.id, 'Данный чат уже разрешен для работы с ботом')
            return
        text = '<b>%s</b> запрашивает разрешение на работу с ботом из чата "%s"\r\nchat_id: %s' % \
               (str(message.from_user.username.encode('utf-8')), str(message.chat.title.encode('utf-8')),
                str(message.chat.id))
        bot.send_message(45839899, text, parse_mode='HTML')

    @bot.message_handler(commands=['join'])
    def join_session(message):
        if message.chat.id not in main_vars.allowed_chats.keys():
            bot.send_message(message.chat.id, 'Данный чат не является разрешенным для работы с ботом\r\n'
                                              'Для отправки запроса на разрешение введите /ask_for_permission')
            return
        join_session_task = {
            'task_type': 'join',
            'chat_id': message.chat.id,
            'additional_chat_id': message.from_user.id,
            'message_id': message.message_id
        }
        main_vars.task_queue.append(join_session_task)

    @bot.message_handler(commands=['reset_join'])
    def reset_join(message):
        if message.chat.id in main_vars.allowed_chats.keys():
            reset_join_task = {
                'task_type': 'reset_join',
                'chat_id': message.chat.id,
                'additional_chat_id': message.from_user.id,
                'message_id': message.message_id
            }
            main_vars.task_queue.append(reset_join_task)
        elif message.chat.id in main_vars.additional_ids.keys():
            reset_join_task = {
                'task_type': 'reset_join',
                'chat_id': None,
                'additional_chat_id': message.chat.id,
                'message_id': message.message_id
            }
            main_vars.task_queue.append(reset_join_task)
        else:
            bot.send_message(message.chat.id,
                             'Данный чат не является ни основным, ни дополнительным разрешенным для работы с ботом\r\n'
                             'Для отправки запроса на разрешение введите /ask_for_permission')

    @bot.message_handler(commands=['add'])
    def add_chat_to_allowed(message):
        if message.chat.id != 45839899:
            bot.send_message(message.chat.id, 'Данная команда не доступна из этого чата')
            return
        chat_id = int(re.search(r'[-\d]+', str(message.text.encode('utf-8'))).group(0))
        main_vars.allowed_chats[chat_id] = {}
        if chat_id in main_vars.allowed_chats.keys():
            bot.send_message(chat_id, 'Этот чат добавлен в список разрешенных для работы с ботом')
        else:
            bot.send_message(chat_id, 'Этот чат не добавлен в список разрешенных для работы с ботом'
                                      '\r\nДля повторного запроса введите /ask_for_permission')

    @bot.message_handler(commands=['start'])
    def start(message):
        if message.chat.id in main_vars.allowed_chats.keys():
            start_task = {
                'task_type': 'start',
                'chat_id': message.chat.id
            }
            main_vars.task_queue.append(start_task)
        elif message.chat.id in main_vars.additional_ids.keys():
            bot.send_message(message.chat.id, 'Теперь вы можете работать с ботом через этот чат')
        else:
            bot.send_message(message.chat.id,
                             'Данный чат не является ни основным, ни дополнительным разрешенным для работы с ботом\r\n'
                             'Для отправки запроса на разрешение введите /ask_for_permission')

    @bot.message_handler(commands=['help'])
    def help(message):
        if message.chat.id not in main_vars.allowed_chats.keys():
            bot.send_message(message.chat.id, 'Данный чат не является разрешенным для работы с ботом\r\n'
                                              'Для отправки запроса на разрешение введите /ask_for_permission')
            return
        bot.send_message(message.chat.id, 'Коды сдавать в виде !код или ! код (штурм - !номер уровня!код)\n'
                                          'Сдавать коды в бонусное окно в виде ?код или ? код (штурм - ?номер уровня?код)\n'
                                          '/task - прислать задание (штурм - /task номер уровня)\n'
                                          '/task_images - прислать все картинки из задания\n'
                                          '/sectors - прислать список секторов (штурм - /sectors номер уровня)\n'
                                          '/hints - прислать все подсказки (штурм - /hints номер уровня)\n'
                                          '/last_hint - прислать последнюю пришедшую подсказку (штурм - /last_hint номер уровня)\n'
                                          '/bonuses - прислать бонусы(штурм - /bonuses номер уровня)\n'
                                          '/unclosed_bonuses - прислать не закрытые бонусы цифрой (штурм - /unclosed_bonuses номер уровня)\n'
                                          '/messages - прислать сообщения авторов (штурм - /messages номер уровня)\n'
                                          '/start_updater - запустить слежение\n'
                                          '/stop_updater - остановить слежение\n'
                                          '/set_channel_name - задать имя канала для репостинга (через пробел)\n'
                                          '/start_channel - запустить постинг в канал\n'
                                          '/stop_channel - остановить постинг в канал\n'
                                          '/stop_session - остановить сессию '
                                          '(остановить выполнение команд из чата, слежение и постинг в канал)\n'
                                          '/config - прислать конфигурацию,\n'
                                          '/delay - выставить интервал слежения\n'
                                          '/join - включить работу с ботом через личный чат\n'
                                          '/reset_join - выключить работу с ботом через личный чат\n'
                                          '/ask_for_permission - отправить запрос на разрешение использования бота\n'
                                          '/codes_off - выключить сдачу кодов\n'
                                          '/codes_on - включить сдачу кодов')

    @bot.message_handler(commands=['start_session'])
    def start_session(message):
        if message.chat.id not in main_vars.allowed_chats.keys():
            bot.send_message(message.chat.id, 'Данный чат не является разрешенным для работы с ботом\r\n'
                                              'Для отправки запроса на разрешение введите /ask_for_permission')
            return
        start_session_task = {
            'task_type': 'start_session',
            'chat_id': message.chat.id
        }
        main_vars.task_queue.append(start_session_task)

    @bot.message_handler(commands=['stop_session'])
    def stop_session(message):
        if message.chat.id not in main_vars.allowed_chats.keys():
            bot.send_message(message.chat.id, 'Данный чат не является разрешенным для работы с ботом\r\n'
                                              'Для отправки запроса на разрешение введите /ask_for_permission')
            return
        stop_session_task = {
            'task_type': 'stop_session',
            'chat_id': message.chat.id
        }
        main_vars.task_queue.append(stop_session_task)

    @bot.message_handler(commands=['config'])
    def config(message):
        if message.chat.id not in main_vars.allowed_chats.keys():
            bot.send_message(message.chat.id, 'Данный чат не является разрешенным для работы с ботом\r\n'
                                              'Для отправки запроса на разрешение введите /ask_for_permission')
            return
        config_task = {
            'task_type': 'config',
            'chat_id': message.chat.id
        }
        main_vars.task_queue.append(config_task)

    @bot.message_handler(commands=['login'])
    def save_login(message):
        if message.chat.id not in main_vars.allowed_chats.keys():
            bot.send_message(message.chat.id, 'Данный чат не является разрешенным для работы с ботом\r\n'
                                              'Для отправки запроса на разрешение введите /ask_for_permission')
            return
        set_login_task = {
            'task_type': 'login',
            'chat_id': message.chat.id,
            'new_login': re.findall(r'/login\s*(.+)', str(message.text.encode('utf-8')))[0]
        }
        main_vars.task_queue.append(set_login_task)

    @bot.message_handler(commands=['password'])
    def save_password(message):
        if message.chat.id not in main_vars.allowed_chats.keys():
            bot.send_message(message.chat.id, 'Данный чат не является разрешенным для работы с ботом\r\n'
                                              'Для отправки запроса на разрешение введите /ask_for_permission')
            return
        set_password_task = {
            'task_type': 'password',
            'chat_id': message.chat.id,
            'new_password': re.findall(r'/password\s*(.+)', str(message.text.encode('utf-8')))[0]
        }
        main_vars.task_queue.append(set_password_task)

    @bot.message_handler(commands=['domain'])
    def save_en_domain(message):
        if message.chat.id not in main_vars.allowed_chats.keys():
            bot.send_message(message.chat.id, 'Данный чат не является разрешенным для работы с ботом\r\n'
                                              'Для отправки запроса на разрешение введите /ask_for_permission')
            return
        set_domain_task = {
            'task_type': 'domain',
            'chat_id': message.chat.id,
            'new_domain': re.findall(r'/domain\s*(.+)', str(message.text.encode('utf-8')))[0]
        }
        main_vars.task_queue.append(set_domain_task)

    @bot.message_handler(commands=['gameid'])
    def save_game_id(message):
        if message.chat.id not in main_vars.allowed_chats.keys():
            bot.send_message(message.chat.id, 'Данный чат не является разрешенным для работы с ботом\r\n'
                                              'Для отправки запроса на разрешение введите /ask_for_permission')
            return
        set_game_id_task = {
            'task_type': 'game_id',
            'chat_id': message.chat.id,
            'new_game_id': re.search(r'[\d]+', str(message.text.encode('utf-8'))).group(0)
        }
        main_vars.task_queue.append(set_game_id_task)

    @bot.message_handler(commands=['login_to_en'])
    def login_to_en(message):
        if message.chat.id not in main_vars.allowed_chats.keys():
            bot.send_message(message.chat.id, 'Данный чат не является разрешенным для работы с ботом\r\n'
                                              'Для отправки запроса на разрешение введите /ask_for_permission')
            return
        login_to_en_task = {
            'task_type': 'login_to_en',
            'chat_id': message.chat.id
        }
        main_vars.task_queue.append(login_to_en_task)

    @bot.message_handler(commands=['task'])
    def send_task(message):
        storm_level = int(re.search(r'[\d]+', str(message.text.encode('utf-8'))).group(0)) if \
            re.findall(r'[\d]+', str(message.text.encode('utf-8'))) else None
        if message.chat.id in main_vars.allowed_chats.keys():
            send_task_task = {
                'task_type': 'send_task',
                'chat_id': message.chat.id,
                'additional_chat_id': None,
                'storm_level': storm_level
            }
            main_vars.task_queue.append(send_task_task)
        elif message.chat.id in main_vars.additional_ids.keys():
            send_task_task = {
                'task_type': 'send_task',
                'chat_id': None,
                'additional_chat_id': message.chat.id,
                'storm_level': storm_level
            }
            main_vars.task_queue.append(send_task_task)
        else:
            bot.send_message(message.chat.id,
                             'Данный чат не является ни основным, ни дополнительным разрешенным для работы с ботом\r\n'
                             'Для отправки запроса на разрешение введите /ask_for_permission')

    @bot.message_handler(commands=['task_images'])
    def send_task_images(message):
        if message.chat.id not in main_vars.allowed_chats.keys():
            bot.send_message(message.chat.id, 'Данный чат не является разрешенным для работы с ботом\r\n'
                                              'Для отправки запроса на разрешение введите /ask_for_permission')
            return
        send_task_images_task = {
            'task_type': 'task_images',
            'chat_id': message.chat.id
        }
        main_vars.task_queue.append(send_task_images_task)

    @bot.message_handler(commands=['sectors'])
    def send_all_sectors(message):
        storm_level = int(re.search(r'[\d]+', str(message.text.encode('utf-8'))).group(0)) if \
            re.findall(r'[\d]+', str(message.text.encode('utf-8'))) else None
        if message.chat.id in main_vars.allowed_chats.keys():
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
        if message.chat.id in main_vars.allowed_chats.keys():
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
        if message.chat.id in main_vars.allowed_chats.keys():
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
        if message.chat.id in main_vars.allowed_chats.keys():
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
        if message.chat.id in main_vars.allowed_chats.keys():
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
        if message.chat.id in main_vars.allowed_chats.keys():
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
        if message.chat.id not in main_vars.allowed_chats.keys():
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
        if message.chat.id not in main_vars.allowed_chats.keys():
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
        if message.chat.id not in main_vars.allowed_chats.keys():
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
        if message.chat.id not in main_vars.allowed_chats.keys():
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
        if message.chat.id not in main_vars.allowed_chats.keys():
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
        if message.chat.id not in main_vars.allowed_chats.keys():
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
        if message.chat.id not in main_vars.allowed_chats.keys():
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
        if message.chat.id not in main_vars.allowed_chats.keys():
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
        tags_list.append(tag_to_add)
        if tag_to_add in tags_list:
            bot.send_message(message.chat.id, 'Тег успешно добавлен в обработчик')
        else:
            bot.send_message(message.chat.id, 'Тег не добавлен в обработчикб повторите попытку')

    @bot.message_handler(content_types=['text'])
    def text_processor(message):
        if message.chat.id not in main_vars.allowed_chats.keys() and message.chat.id not in main_vars.additional_ids.keys():
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
            if message.chat.id in main_vars.allowed_chats.keys():
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
            if message.chat.id in main_vars.allowed_chats.keys():
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
        if coords and message.chat.id in main_vars.allowed_chats.keys():
            send_coords_task = {
                'task_type': 'send_coords',
                'chat_id': message.chat.id,
                'coords': coords
            }
            main_vars.task_queue.append(send_coords_task)

    # Remove webhook, it fails sometimes the set if there is a previous webhook
    bot.remove_webhook()

    # Set webhook
    bot.set_webhook(url='https://8ae0b3f7.ngrok.io/webhook')

    @app.route("/", methods=['GET', 'POST'])
    def hello():
        return "Hello World!"

    return app
