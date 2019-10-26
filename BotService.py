# -*- coding: utf-8 -*-
import re
import os
import uuid
import string
import random
import logging
import telebot
import threading
import flask as f
from Const import helptext
from collections import namedtuple
from DBMethods import DB, DBSession
from MainClasses import Task, Validations
from TextConvertingMethods import find_coords
from builder import FillEngine, CleanEngine, TransferEngine
from BotServiceMethods import add_level_bonuses, add_level_sectors, run_db_cleanup, capture_stdout

StatusHolderCls = namedtuple("StatusHolder", ["message", "debug_info", "status", "get", "clear", "set_request", "get_request"])


class Status:
    EMPTY = "_"
    IN_PROGRESS = "Выполняется"
    FAILED = "Ошибка"
    DONE = "Выполнено"


class StatusHolder(object):
    def __init__(self):
        self.statuses = {}

    def get_status(self, key):
        if key not in self.statuses:
            self.statuses[key] = {
                "messages": [],
                "debug_info": [],
                "status": Status.EMPTY,
                "actual_request": 0
            }
        return self.statuses[key]

    def get_holder_for_app(self, app_name, ip_address):
        key = '%s_%s' % (app_name, ip_address)
        return StatusHolderCls(
            lambda message: self.add_message(key, message),
            lambda debug_info: self.add_debug_info(key, debug_info),
            lambda status: self.set_status(key, status),
            lambda: self.get_status(key),
            lambda: self.clear_status(key),
            lambda: self.set_number_request(key),
            lambda: self.get_number_request(key)
        )

    def clear_status(self, app_name):
        if app_name in self.statuses:
            del self.statuses[app_name]

    def add_message(self, app_name, message):
        status = self.get_status(app_name)
        status["messages"].append(message)

    def add_debug_info(self, app_name, message):
        status = self.get_status(app_name)
        status["debug_info"].extend(message)

    def set_status(self, app_name, status_string):
        status = self.get_status(app_name)
        status["status"] = status_string

    def get_number_request(self, app_name):
        status = self.get_status(app_name)
        return status["actual_request"]

    def set_number_request(self, app_name):
        status = self.get_status(app_name)
        request_number = str(uuid.uuid4())
        status["actual_request"] = request_number
        return request_number


def _get_all_apps(modules):
    apps = []
    for module in modules:
        apps.extend(module.get_applications())
    return apps


def find_app(app_name, all_apps):
    for app in all_apps:
        if app['name'] == app_name:
            return app
    raise AssertionError("Unknown application '{}'".format(app_name))


def get_index(root_path):
    with open(os.path.join(root_path, 'templates', 'index.html')) as fp:
        response = f.make_response(fp.read())
        # response = f.make_response(f.render_template("index.html", apps=apps, base_url='https://jekafstbot.herokuapp.com' if prod else 'http://localhost:443'))
        if not f.request.cookies.get('builder_client_id'):
            chars = string.ascii_uppercase + string.digits
            client_id = ''.join(random.choice(chars) for _ in range(10))
            response.set_cookie('builder_client_id', client_id)
        return response


# def run_app():
def run_app(bot, queue):
    app = f.Flask(__name__)

    fill_engine = FillEngine.FillEngine()
    clean_engine = CleanEngine.CleanEngine()
    transfer_engine = TransferEngine.TransferEngine()
    modules = [fill_engine, clean_engine, transfer_engine]
    all_apps = _get_all_apps(modules)
    stats = StatusHolder()
    current_app = {}

    # Process webhook calls
    @app.route('/webhook', methods=['GET', 'POST'])
    def webhook():
        if f.request.headers.get('content-type') == 'application/json':
            json_string = f.request.get_data().decode('utf-8')
            update = telebot.types.Update.de_json(json_string)
            bot.process_new_updates([update])
            return ''
        else:
            f.abort(403)

    @bot.message_handler(commands=['ask_for_permission'])
    def ask_for_permission(message):
        main_chat_ids, _ = DB.get_allowed_chat_ids()
        if message.chat.id in main_chat_ids:
            bot.send_message(message.chat.id, 'Данный чат уже разрешен для работы с ботом')
            return
        try:
            title = str(message.chat.title.encode('utf-8')) if message.chat.title else ''
            text = '<b>%s</b> запрашивает разрешение на работу с ботом из чата "%s"\r\nchat_id: %s' % \
                   (str(message.from_user.username.encode('utf-8')), title, str(message.chat.id))
            # admin_id = message.from_user.id if message.from_user.id in [66204553] else 45839899
            admin_id = 45839899
            bot.send_message(admin_id, text, parse_mode='HTML')
            bot.send_message(message.chat.id, 'Запрос на разрешение использования бота отправлен администратору\n'
                                              'Если вам не придет ответ в течение нескольких часов - напишите в личку @JekaFST',
                             reply_to_message_id=message.message_id)
        except Exception:
            logging.exception('Запрос на разрешение не отправлен')
            bot.send_message(message.chat.id, 'Запрос на разрешение использования бота не отправлен администратору\n'
                                              'Напишите в личку @JekaFST',
                             reply_to_message_id=message.message_id)

    @bot.message_handler(commands=['ask_to_add_gameid'])
    def ask_to_add_gameid(message):
        allowed, main_chat_ids, _ = Validations.check_permission(message.chat.id, bot)
        if allowed and Validations.check_from_main_chat(message.chat.id, bot, main_chat_ids, message.message_id):
            allowed_game_ids = DB.get_allowed_game_ids(message.chat.id)
            game_id = re.search(r'[\d]+', str(message.text.encode('utf-8'))).group(0)
            if game_id in allowed_game_ids:
                bot.send_message(message.chat.id, 'Данная игра уже разрешена для этого чата')
                return
            try:
                title = str(message.chat.title.encode('utf-8')) if message.chat.title else ''
                text = '<b>%s</b> запрашивает разрешение на игру %s для чата "%s"\r\nchat_id: %s' % \
                       (str(message.from_user.username.encode('utf-8')), game_id, title, str(message.chat.id))
                # admin_id = message.from_user.id if message.from_user.id in [66204553] else 45839899
                admin_id = 45839899
                bot.send_message(admin_id, text, parse_mode='HTML')
                bot.send_message(message.chat.id, 'Запрос на разрешение игры для этого чата отправлен администратору\n'
                                                  'Если вам не придет ответ в течение нескольких часов - напишите в личку @JekaFST',
                                 reply_to_message_id=message.message_id)
            except Exception:
                logging.exception('Запрос на разрешение игры не отправлен')
                bot.send_message(message.chat.id, 'Запрос на разрешение игры из этого чата не отправлен администратору\n'
                                                  'Напишите в личку @JekaFST',
                                 reply_to_message_id=message.message_id)

    @bot.message_handler(commands=['join'])
    def join_session(message):
        allowed, main_chat_ids, add_chat_ids = Validations.check_permission(message.chat.id, bot)
        if allowed \
                and Validations.check_session_available(message.chat.id, bot) \
                and Validations.check_join_possible(message.chat.id, bot, message.from_user.id, message.message_id, add_chat_ids):
            join_task = Task(message.chat.id, 'join', message_id=message.message_id, user_id=message.from_user.id)
            queue.put((99, join_task))

    @bot.message_handler(commands=['reset_join'])
    def reset_join(message):
        allowed, main_chat_ids, add_chat_ids = Validations.check_permission(message.chat.id, bot)
        if allowed \
                and Validations.check_session_available(message.chat.id, bot) \
                and Validations.check_reset_join_possible(message.chat.id, bot, message.from_user.id, message.message_id, add_chat_ids):
            reset_join_task = Task(message.chat.id, 'reset_join', message_id=message.message_id, user_id=message.from_user.id)
            queue.put((99, reset_join_task))

    @bot.message_handler(commands=['add'])
    def add_chat_to_allowed(message):
        if message.chat.id not in [45839899]:  # 66204553
            bot.send_message(message.chat.id, 'Данная команда не доступна из этого чата')
            return
        chat_id = int(re.search(r'[-\d]+', str(message.text.encode('utf-8'))).group(0))
        main_chat_ids, _ = DB.get_allowed_chat_ids()
        if chat_id in main_chat_ids:
            bot.send_message(message.chat.id, 'Данный чат уже разрешен для работы с ботом')
            return
        if DB.insert_main_chat_id(chat_id):
            bot.send_message(chat_id, 'Этот чат добавлен в список разрешенных для работы с ботом')
        else:
            bot.send_message(message.chat.id, 'Этот чат не добавлен в список разрешенных для работы с ботом\r\n'
                                              'Insert не выполнен')

    @bot.message_handler(commands=['add_game_id'])
    def add_game_id(message):
        if message.chat.id not in [45839899]:  # 66204553
            bot.send_message(message.chat.id, 'Данная команда не доступна из этого чата')
            return
        chat_id = int(re.findall(r':\s+([-\d]+)$', str(message.text.encode('utf-8')))[0])
        game_id = re.findall(r'/add_game_id\s+(\d+)\s*:', str(message.text.encode('utf-8')))[0]
        allowed_game_ids = DB.get_allowed_game_ids(chat_id)
        if game_id not in allowed_game_ids:
            allowed_game_ids += game_id if not allowed_game_ids else ', ' + game_id
            if DB.update_allowed_game_ids(chat_id, allowed_game_ids):
                bot.send_message(chat_id, 'Игра %s разрешена' % game_id)
            else:
                bot.send_message(message.chat.id, 'Игра не разрешена. Insert не выполнен')

    @bot.message_handler(commands=['add_builder_game_id'])
    def add_builder_game_id(message):
        if message.chat.id != 45839899:
            bot.send_message(message.chat.id, 'Данная команда не доступна из этого чата')
            return
        game_id = re.search(r'[\d]+', str(message.text.encode('utf-8'))).group(0)
        if game_id not in DB.get_gameids_for_builder_list():
            if DB.insert_gameids_for_builder(game_id):
                bot.send_message(message.chat.id, 'Игра %s добавлена в разрешенные для game builder' % game_id)
            else:
                bot.send_message(message.chat.id, 'Игра для game builder не разрешена. Insert не выполнен')

    @bot.message_handler(commands=['start'])
    def start(message):
        allowed, main_chat_ids, add_chat_ids = Validations.check_permission(message.chat.id, bot)
        if allowed and not Validations.check_from_add_chat(message.chat.id, add_chat_ids):
            start_task = Task(message.chat.id, 'start')
            queue.put((99, start_task))

    @bot.message_handler(commands=['help'])
    def help(message):
        allowed, _, _ = Validations.check_permission(message.chat.id, bot)
        if allowed:
            bot.send_message(message.chat.id, helptext)

    @bot.message_handler(commands=['start_session'])
    def start_session(message):
        allowed, main_chat_ids, add_chat_ids = Validations.check_permission(message.chat.id, bot)
        if allowed and Validations.check_session_available(message.chat.id, bot) \
                and Validations.check_from_main_chat(message.chat.id, bot, main_chat_ids, message.message_id):

            start_session_task = Task(message.chat.id, 'start_session', session_id=message.chat.id)
            queue.put((99, start_session_task))

    @bot.message_handler(commands=['stop_session'])
    def stop_session(message):
        allowed, main_chat_ids, add_chat_ids = Validations.check_permission(message.chat.id, bot)
        if allowed and Validations.check_session_available(message.chat.id, bot) \
                and Validations.check_from_main_chat(message.chat.id, bot, main_chat_ids, message.message_id):

            stop_session_task = Task(message.chat.id, 'stop_session', session_id=message.chat.id)
            queue.put((99, stop_session_task))

    @bot.message_handler(commands=['config'])
    def config(message):
        allowed, main_chat_ids, add_chat_ids = Validations.check_permission(message.chat.id, bot)
        if allowed and Validations.check_session_available(message.chat.id, bot) \
                and Validations.check_from_main_chat(message.chat.id, bot, main_chat_ids, message.message_id):

            config_task = Task(message.chat.id, 'config', session_id=message.chat.id)
            queue.put((99, config_task))

    @bot.message_handler(commands=['login'])
    def save_login(message):
        allowed, main_chat_ids, add_chat_ids = Validations.check_permission(message.chat.id, bot)
        if allowed and Validations.check_session_available(message.chat.id, bot):

            main_chat_id = message.chat.id if message.chat.id in main_chat_ids else DB.get_main_chat_id_via_add(message.chat.id)
            new_login = re.findall(r'/login\s*(.+)', str(message.text.encode('utf-8')))[0] if re.findall(r'/login\s*(.+)', str(message.text.encode('utf-8'))) else None
            if not new_login:
                bot.send_message(message.chat.id, 'Введите логин после команды /login, через пробел', reply_to_message_id=message.message_id)
                return
            set_login_task = Task(message.chat.id, 'login', session_id=main_chat_id, new_login=new_login)
            queue.put((99, set_login_task))

    @bot.message_handler(commands=['password'])
    def save_password(message):
        allowed, main_chat_ids, add_chat_ids = Validations.check_permission(message.chat.id, bot)
        if allowed and Validations.check_session_available(message.chat.id, bot):

            main_chat_id = message.chat.id if message.chat.id in main_chat_ids else DB.get_main_chat_id_via_add(message.chat.id)
            new_password = re.findall(r'/password\s*(.+)', str(message.text.encode('utf-8')))[0] if re.findall(r'/password\s*(.+)', str(message.text.encode('utf-8'))) else None
            if not new_password:
                bot.send_message(message.chat.id, 'Введите пароль после команды /password, через пробел', reply_to_message_id=message.message_id)
                return
            set_password_task = Task(message.chat.id, 'password', session_id=main_chat_id, new_password=new_password)
            queue.put((99, set_password_task))

    @bot.message_handler(commands=['domain'])
    def save_en_domain(message):
        allowed, main_chat_ids, add_chat_ids = Validations.check_permission(message.chat.id, bot)
        if allowed and Validations.check_session_available(message.chat.id, bot):

            main_chat_id = message.chat.id if message.chat.id in main_chat_ids else DB.get_main_chat_id_via_add(message.chat.id)
            new_domain = re.findall(r'/domain\s*(.+)', str(message.text.encode('utf-8')))[0] if re.findall(r'/domain\s*(.+)', str(message.text.encode('utf-8'))) else None
            if not new_domain:
                bot.send_message(message.chat.id, 'Введите домен после команды /domain, через пробел', reply_to_message_id=message.message_id)
                return
            set_domain_task = Task(message.chat.id, 'domain', session_id=main_chat_id, new_domain=new_domain)
            queue.put((99, set_domain_task))

    @bot.message_handler(commands=['gameid'])
    def save_game_id(message):
        allowed, main_chat_ids, add_chat_ids = Validations.check_permission(message.chat.id, bot)
        if allowed and Validations.check_session_available(message.chat.id, bot):

            main_chat_id = message.chat.id if message.chat.id in main_chat_ids else DB.get_main_chat_id_via_add(message.chat.id)
            new_game_id = re.findall(r'[\d]+', str(message.text.encode('utf-8')))[0] if re.findall(r'[\d]+', str(message.text.encode('utf-8'))) else None
            if not new_game_id:
                bot.send_message(message.chat.id, 'Введите айди игры после команды /gameid, через пробел', reply_to_message_id=message.message_id)
                return
            set_game_id_task = Task(message.chat.id, 'game_id', session_id=main_chat_id, new_game_id=new_game_id)
            queue.put((99, set_game_id_task))

    @bot.message_handler(commands=['login_to_en'])
    def login_to_en(message):
        allowed, main_chat_ids, add_chat_ids = Validations.check_permission(message.chat.id, bot)
        if allowed and Validations.check_session_available(message.chat.id, bot) \
                and Validations.check_from_main_chat(message.chat.id, bot, main_chat_ids, message.message_id):

            login_to_en_task = Task(message.chat.id, 'login_to_en', session_id=message.chat.id)
            queue.put((99, login_to_en_task))

    @bot.message_handler(commands=['task'])
    def send_task(message):
        allowed, main_chat_ids, add_chat_ids = Validations.check_permission(message.chat.id, bot)
        if allowed and Validations.check_session_available(message.chat.id, bot):

            main_chat_id = message.chat.id if message.chat.id in main_chat_ids else DB.get_main_chat_id_via_add(message.chat.id)
            storm_level = int(re.search(r'[\d]+', str(message.text.encode('utf-8'))).group(0)) if \
                re.findall(r'[\d]+', str(message.text.encode('utf-8'))) else None
            send_task_task = Task(message.chat.id, 'send_task', session_id=main_chat_id, storm_level_number=storm_level)
            queue.put((99, send_task_task))

    @bot.message_handler(commands=['task_images'])
    def send_task_images(message):
        allowed, main_chat_ids, add_chat_ids = Validations.check_permission(message.chat.id, bot)
        if allowed and Validations.check_session_available(message.chat.id, bot) \
                and Validations.check_from_main_chat(message.chat.id, bot, main_chat_ids, message.message_id):

            main_chat_id = message.chat.id if message.chat.id in main_chat_ids else DB.get_main_chat_id_via_add(message.chat.id)
            send_task_images_task = Task(message.chat.id, 'task_images', session_id=main_chat_id)
            queue.put((99, send_task_images_task))

    @bot.message_handler(commands=['sectors'])
    def send_all_sectors(message):
        allowed, main_chat_ids, add_chat_ids = Validations.check_permission(message.chat.id, bot)
        if allowed and Validations.check_session_available(message.chat.id, bot):

            main_chat_id = message.chat.id if message.chat.id in main_chat_ids else DB.get_main_chat_id_via_add(message.chat.id)
            storm_level = int(re.search(r'[\d]+', str(message.text.encode('utf-8'))).group(0)) if \
                re.findall(r'[\d]+', str(message.text.encode('utf-8'))) else None
            send_all_sectors_task = Task(message.chat.id, 'send_sectors', session_id=main_chat_id, storm_level_number=storm_level)
            queue.put((99, send_all_sectors_task))

    @bot.message_handler(commands=['hints'])
    def send_all_helps(message):
        allowed, main_chat_ids, add_chat_ids = Validations.check_permission(message.chat.id, bot)
        if allowed and Validations.check_session_available(message.chat.id, bot):

            main_chat_id = message.chat.id if message.chat.id in main_chat_ids else DB.get_main_chat_id_via_add(message.chat.id)
            storm_level = int(re.search(r'[\d]+', str(message.text.encode('utf-8'))).group(0)) if \
                re.findall(r'[\d]+', str(message.text.encode('utf-8'))) else None
            send_all_helps_task = Task(message.chat.id, 'send_helps', session_id=main_chat_id, storm_level_number=storm_level)
            queue.put((99, send_all_helps_task))

    @bot.message_handler(commands=['last_hint'])
    def send_last_help(message):
        allowed, main_chat_ids, add_chat_ids = Validations.check_permission(message.chat.id, bot)
        if allowed and Validations.check_session_available(message.chat.id, bot):

            main_chat_id = message.chat.id if message.chat.id in main_chat_ids else DB.get_main_chat_id_via_add(message.chat.id)
            storm_level = int(re.search(r'[\d]+', str(message.text.encode('utf-8'))).group(0)) if \
                re.findall(r'[\d]+', str(message.text.encode('utf-8'))) else None
            send_last_help_task = Task(message.chat.id, 'send_last_help', session_id=main_chat_id, storm_level_number=storm_level)
            queue.put((99, send_last_help_task))

    @bot.message_handler(commands=['bonuses'])
    def send_all_bonuses(message):
        allowed, main_chat_ids, add_chat_ids = Validations.check_permission(message.chat.id, bot)
        if allowed and Validations.check_session_available(message.chat.id, bot):

            main_chat_id = message.chat.id if message.chat.id in main_chat_ids else DB.get_main_chat_id_via_add(message.chat.id)
            storm_level = int(re.search(r'[\d]+', str(message.text.encode('utf-8'))).group(0)) if \
                re.findall(r'[\d]+', str(message.text.encode('utf-8'))) else None
            send_all_bonuses_task = Task(message.chat.id, 'send_bonuses', session_id=main_chat_id, storm_level_number=storm_level)
            queue.put((99, send_all_bonuses_task))

    @bot.message_handler(commands=['unclosed_bonuses'])
    def send_unclosed_bonuses(message):
        allowed, main_chat_ids, add_chat_ids = Validations.check_permission(message.chat.id, bot)
        if allowed and Validations.check_session_available(message.chat.id, bot):

            main_chat_id = message.chat.id if message.chat.id in main_chat_ids else DB.get_main_chat_id_via_add(message.chat.id)
            storm_level = int(re.search(r'[\d]+', str(message.text.encode('utf-8'))).group(0)) if \
                re.findall(r'[\d]+', str(message.text.encode('utf-8'))) else None
            send_unclosed_bonuses_task = Task(message.chat.id, 'unclosed_bonuses', session_id=main_chat_id, storm_level_number=storm_level)
            queue.put((99, send_unclosed_bonuses_task))

    @bot.message_handler(commands=['messages'])
    def send_auth_messages(message):
        allowed, main_chat_ids, add_chat_ids = Validations.check_permission(message.chat.id, bot)
        if allowed and Validations.check_session_available(message.chat.id, bot):

            main_chat_id = message.chat.id if message.chat.id in main_chat_ids else DB.get_main_chat_id_via_add(message.chat.id)
            storm_level = int(re.search(r'[\d]+', str(message.text.encode('utf-8'))).group(0)) if \
                re.findall(r'[\d]+', str(message.text.encode('utf-8'))) else None
            send_auth_messages_task = Task(message.chat.id, 'send_messages', session_id=main_chat_id, storm_level_number=storm_level)
            queue.put((99, send_auth_messages_task))

    @bot.message_handler(commands=['start_updater'])
    def start_updater(message):
        allowed, main_chat_ids, add_chat_ids = Validations.check_permission(message.chat.id, bot)
        if allowed and Validations.check_session_available(message.chat.id, bot) \
                and Validations.check_from_main_chat(message.chat.id, bot, main_chat_ids, message.message_id):

            start_updater_task = Task(message.chat.id, 'start_updater', queue=queue, session_id=message.chat.id)
            queue.put((2, start_updater_task))

    @bot.message_handler(commands=['delay'])
    def set_updater_delay(message):
        allowed, main_chat_ids, add_chat_ids = Validations.check_permission(message.chat.id, bot)
        if allowed and Validations.check_session_available(message.chat.id, bot) \
                and Validations.check_from_main_chat(message.chat.id, bot, main_chat_ids, message.message_id):

            new_delay = int(re.search(r'[\d]+', str(message.text.encode('utf-8'))).group(0))
            set_delay_task = Task(message.chat.id, 'delay', session_id=message.chat.id, new_delay=new_delay)
            queue.put((99, set_delay_task))

    @bot.message_handler(commands=['stop_updater'])
    def stop_updater(message):
        allowed, main_chat_ids, add_chat_ids = Validations.check_permission(message.chat.id, bot)
        if allowed and Validations.check_session_available(message.chat.id, bot) \
                and Validations.check_from_main_chat(message.chat.id, bot, main_chat_ids, message.message_id):

            stop_updater_task = Task(message.chat.id, 'stop_updater', session_id=message.chat.id)
            queue.put((2, stop_updater_task))

    @bot.message_handler(commands=['set_channel_name'])
    def set_channel_name(message):
        allowed, main_chat_ids, add_chat_ids = Validations.check_permission(message.chat.id, bot)
        if allowed and Validations.check_session_available(message.chat.id, bot):

            main_chat_id = message.chat.id if message.chat.id in main_chat_ids else DB.get_main_chat_id_via_add(message.chat.id)
            new_channel_name = re.findall(r'/set_channel_name\s*(.+)', str(message.text.encode('utf-8')))[0] if re.findall(r'/set_channel_name\s*(.+)', str(message.text.encode('utf-8'))) else None
            if not new_channel_name:
                bot.send_message(message.chat.id, 'Введите имя канала после команды /set_channel_name, через пробел', reply_to_message_id=message.message_id)
                return
            set_channel_name_task = Task(message.chat.id, 'channel_name', session_id=main_chat_id, new_channel_name=new_channel_name)
            queue.put((99, set_channel_name_task))

    @bot.message_handler(commands=['start_channel'])
    def start_channel(message):
        allowed, main_chat_ids, add_chat_ids = Validations.check_permission(message.chat.id, bot)
        if allowed and Validations.check_session_available(message.chat.id, bot) \
                and Validations.check_from_main_chat(message.chat.id, bot, main_chat_ids, message.message_id):

            start_channel_task = Task(message.chat.id, 'start_channel', session_id=message.chat.id)
            queue.put((99, start_channel_task))

    @bot.message_handler(commands=['stop_channel'])
    def stop_channel(message):
        allowed, main_chat_ids, add_chat_ids = Validations.check_permission(message.chat.id, bot)
        if allowed and Validations.check_session_available(message.chat.id, bot) \
                and Validations.check_from_main_chat(message.chat.id, bot, main_chat_ids, message.message_id):

            stop_channel_task = Task(message.chat.id, 'stop_channel', session_id=message.chat.id)
            queue.put((99, stop_channel_task))

    @bot.message_handler(commands=['codes_on'])
    def enable_codes(message):
        allowed, main_chat_ids, add_chat_ids = Validations.check_permission(message.chat.id, bot)
        if allowed and Validations.check_session_available(message.chat.id, bot) \
                and Validations.check_from_main_chat(message.chat.id, bot, main_chat_ids, message.message_id):

            enable_codes_task = Task(message.chat.id, 'codes_on', session_id=message.chat.id)
            queue.put((1, enable_codes_task))

    @bot.message_handler(commands=['codes_off'])
    def disable_codes(message):
        allowed, main_chat_ids, add_chat_ids = Validations.check_permission(message.chat.id, bot)
        if allowed and Validations.check_session_available(message.chat.id, bot) \
                and Validations.check_from_main_chat(message.chat.id, bot, main_chat_ids, message.message_id):

            disable_codes_task = Task(message.chat.id, 'codes_off', session_id=message.chat.id)
            queue.put((0, disable_codes_task))

    @bot.message_handler(commands=['add_tag'])
    def add_tag(message):
        if message.chat.id != 45839899:
            bot.send_message(message.chat.id, 'Данная команда не доступна из этого чата')
            return
        tag_to_add = re.findall(r'/add_tag\s*(.+)', str(message.text.encode('utf-8')))[0]
        if DB.insert_tag_in_tags_list(tag_to_add):
            bot.send_message(message.chat.id, 'Тег успешно добавлен в обработчик')
        else:
            bot.send_message(message.chat.id, 'Тег не добавлен в обработчикб повторите попытку')

    @bot.message_handler(commands=['send_ll'])
    def send_live_location(message):
        if message.chat.id == -1001204488259:
            return
        allowed, main_chat_ids, add_chat_ids = Validations.check_permission(message.chat.id, bot)
        if allowed and Validations.check_session_available(message.chat.id, bot):

            main_chat_id = message.chat.id if message.chat.id in main_chat_ids else DB.get_main_chat_id_via_add(message.chat.id)
            coords = re.findall(r'\d\d\.\d{4,7},\s{0,3}\d\d\.\d{4,7}|'
                                r'\d\d\.\d{4,7}\s{0,3}\d\d\.\d{4,7}|'
                                r'\d\d\.\d{4,7}\r\n\d\d\.\d{4,7}|'
                                r'\d\d\.\d{4,7},\r\n\d\d\.\d{4,7}', message.text)
            seconds = re.findall(r'\ss(\d+)', str(message.text.encode('utf-8')))
            duration = int(seconds[0]) if seconds else None
            if duration:
                if duration > 86400:
                    duration = 86400
                elif duration < 60:
                    duration = 60
                else:
                    pass
            send_live_location_task = Task(message.chat.id, 'live_location', session_id=main_chat_id, coords=coords, duration=duration)
            queue.put((99, send_live_location_task))

    @bot.message_handler(commands=['stop_ll'])
    def stop_live_location(message):
        allowed, main_chat_ids, add_chat_ids = Validations.check_permission(message.chat.id, bot)
        if allowed and Validations.check_session_available(message.chat.id, bot):

            main_chat_id = message.chat.id if message.chat.id in main_chat_ids else DB.get_main_chat_id_via_add(message.chat.id)
            point_number = re.findall(r'\s+(\d{1,2})', str(message.text.encode('utf-8')))
            point = point_number[0] if point_number else None
            stop_live_location_task = Task(message.chat.id, 'stop_live_location', session_id=main_chat_id, point=point)
            queue.put((99, stop_live_location_task))

    @bot.message_handler(commands=['edit_ll'])
    def edit_live_location(message):
        allowed, main_chat_ids, add_chat_ids = Validations.check_permission(message.chat.id, bot)
        if allowed and Validations.check_session_available(message.chat.id, bot):

            main_chat_id = message.chat.id if message.chat.id in main_chat_ids else DB.get_main_chat_id_via_add(message.chat.id)
            coords = re.findall(r'\d\d\.\d{4,7},\s{0,3}\d\d\.\d{4,7}|'
                                r'\d\d\.\d{4,7}\s{0,3}\d\d\.\d{4,7}|'
                                r'\d\d\.\d{4,7}\r\n\d\d\.\d{4,7}|'
                                r'\d\d\.\d{4,7},\r\n\d\d\.\d{4,7}', message.text)
            point_number = re.findall(r'\s(\d{1,2})\s', str(message.text.encode('utf-8')))
            point = point_number[0] if point_number else None
            edit_live_location_task = Task(message.chat.id, 'edit_live_location', session_id=main_chat_id, point=point, coords=coords)
            queue.put((99, edit_live_location_task))

    @bot.message_handler(commands=['clean_ll'])
    def clean_ll(message):
        allowed, main_chat_ids, add_chat_ids = Validations.check_permission(message.chat.id, bot)
        if allowed and Validations.check_session_available(message.chat.id, bot):

            main_chat_id = message.chat.id if message.chat.id in main_chat_ids else DB.get_main_chat_id_via_add(message.chat.id)
            clean_live_location_task = Task(message.chat.id, 'clean_ll', session_id=main_chat_id)
            queue.put((99, clean_live_location_task))

    @bot.message_handler(commands=['add_points_ll'])
    def add_points_live_location(message):
        allowed, main_chat_ids, add_chat_ids = Validations.check_permission(message.chat.id, bot)
        if allowed and Validations.check_session_available(message.chat.id, bot):

            main_chat_id = message.chat.id if message.chat.id in main_chat_ids else DB.get_main_chat_id_via_add(message.chat.id)
            points_dict = dict()
            points = re.findall(r'\d{1,2}\s*-\s*\d\d\.\d{4,7},\s{,3}\d\d\.\d{4,7}|'
                                r'\d{1,2}\s*-\s*\d\d\.\d{4,7}\s{1,3}\d\d\.\d{4,7}', str(message.text.encode('utf-8')))
            for point in points:
                i = re.findall(r'(\d{1,2})\s*-', point)[0]
                points_dict[i] = re.findall(r'\d\d\.\d{4,7},\s{,3}\d\d\.\d{4,7}|'
                                            r'\d\d\.\d{4,7}\s{1,3}\d\d\.\d{4,7}', point)[0]
            if not points_dict:
                bot.send_message(message.chat.id, 'Нет точек, для отправки live_locations. Верный формат:\n'
                                                  '1 - корды\n2 - корды\n...\nn - корды')
            seconds = re.findall(r'\ss(\d+)', str(message.text.encode('utf-8')))
            duration = int(seconds[0]) if seconds else None
            if duration:
                if duration > 86400:
                    duration = 86400
                elif duration < 60:
                    duration = 60
                else:
                    pass
            add_points_ll_task = Task(message.chat.id, 'add_points_ll', session_id=main_chat_id, points_dict=points_dict, duration=duration)
            queue.put((99, add_points_ll_task))

    @bot.message_handler(commands=['get_codes_links'])
    def get_codes_links(message):
        allowed, main_chat_ids, add_chat_ids = Validations.check_permission(message.chat.id, bot)
        if allowed and Validations.check_session_available(message.chat.id, bot) \
                and Validations.check_from_main_chat(message.chat.id, bot, main_chat_ids, message.message_id):

            get_codes_links_task = Task(message.chat.id, 'get_codes_links', session_id=message.chat.id, message_id=message.message_id)
            queue.put((99, get_codes_links_task))

    @bot.message_handler(commands=['kml'])
    def get_map_file(message):
        allowed, main_chat_ids, add_chat_ids = Validations.check_permission(message.chat.id, bot)
        if allowed and Validations.check_session_available(message.chat.id, bot):

            main_chat_id = message.chat.id if message.chat.id in main_chat_ids else DB.get_main_chat_id_via_add(message.chat.id)
            get_map_file_task = Task(message.chat.id, 'get_map_file', session_id=main_chat_id, message_id=message.message_id)
            queue.put((99, get_map_file_task))

    @bot.message_handler(commands=['instruction'])
    def send_instruction(message):
        bot.send_message(message.chat.id, 'https://jekafstbot.herokuapp.com/instruction')

    @bot.message_handler(commands=[''])
    def send_code_command(message):
        bot.send_message(message.chat.id, 'https://jekafstbot.herokuapp.com/instruction'

    @bot.message_handler(regexp='^[!\.]\s*(.+)')
    def main_code_processor(message):
        allowed, main_chat_ids, add_chat_ids = Validations.check_permission(message.chat.id, bot)
        if allowed and Validations.check_session_available(message.chat.id, bot):

            main_chat_id = message.chat.id if message.chat.id in main_chat_ids else DB.get_main_chat_id_via_add(message.chat.id)
            code = re.findall(r'[!\.]\s*(.+)', str(message.text.lower().encode('utf-8')))[0]
            send_code_main_task = Task(message.chat.id, 'send_code_main', session_id=main_chat_id, code=code,
                                       message_id=message.message_id)
            queue.put((1, send_code_main_task))

    @bot.message_handler(regexp='^\?\s*(.+)')
    def bonus_code_processor(message):
        allowed, main_chat_ids, add_chat_ids = Validations.check_permission(message.chat.id, bot)
        if allowed and Validations.check_session_available(message.chat.id, bot):

            main_chat_id = message.chat.id if message.chat.id in main_chat_ids else DB.get_main_chat_id_via_add(message.chat.id)
            code = re.findall(r'\?\s*(.+)', str(message.text.lower().encode('utf-8')))[0]
            send_code_bonus_task = Task(message.chat.id, 'send_code_bonus', session_id=main_chat_id, code=code,
                                        message_id=message.message_id)
            queue.put((1, send_code_bonus_task))

    @bot.message_handler(regexp='\d\d\.\d{4,7},\s{0,3}\d\d\.\d{4,7}|'
                                '\d\d\.\d{4,7}\s{0,3}\d\d\.\d{4,7}|'
                                '\d\d\.\d{4,7}\r\n\d\d\.\d{4,7}|'
                                '\d\d\.\d{4,7},\r\n\d\d\.\d{4,7}')
    def coords_processor(message):
        allowed, main_chat_ids, add_chat_ids = Validations.check_permission(message.chat.id, bot)
        if allowed:
            coords = find_coords(message.text)
            if coords:
                send_coords_task = Task(message.chat.id, 'send_coords', coords=coords, message_id=message.message_id)
                queue.put((99, send_coords_task))

    @app.route("/")
    def index():
        return get_index(app.root_path)

    @app.route("/apps", methods=['GET'])
    def apps():
        app_names = [{"name": app["name"]} for app in all_apps]
        return f.jsonify(app_names)

    @app.route('/builder/<app_name>', methods=['GET'])
    def app_get(app_name):
        app = find_app(app_name, all_apps)
        client_id = f.request.cookies.get('builder_client_id')
        current_app[client_id] = app_name
        if 'get_fn' in app:
            get_fn = app['get_fn']
            return f.jsonify(get_fn())
        return f.jsonify(stats.get_status('%s_%s' % (app_name, client_id)))

    @app.route("/builder/<app_name>", methods=['POST'])
    def app_post(app_name):
        app = find_app(app_name, all_apps)
        client_id = f.request.cookies.get('builder_client_id')
        current_app[client_id] = app_name
        stat = stats.get_holder_for_app(app_name, client_id)
        stat.clear()
        request_number = stat.set_request()
        app_fn = app['fn']

        try:
            with capture_stdout() as debug_info:
                stat.status(Status.IN_PROGRESS)
                for message in app_fn(f.request):
                    if stat.get_request() == request_number:
                        if message == 'CLEAR_MESSAGES':
                            del stat.get()['messages'][:]
                            continue
                        stat.message(message)
            if stat.get_request() == request_number:
                stat.status(Status.DONE)
        except Exception as e:
            logging.exception("Exception в game_details_builder - проверьте логи")
            stat.status(Status.FAILED)
            stat.message("Fail message: %s" % str(e))
        if stat.get_request() == request_number:
            stat.debug_info(debug_info)
        if current_app[client_id] == app_name:
            return f.jsonify(stat.get())
        else:
            return f.jsonify(stats.get_holder_for_app(current_app[client_id], client_id).get())

    @app.route("/session/<session_id>", methods=['GET', 'POST'])
    def admin(session_id):
        session = DBSession.get_session(session_id)
        data = dict()
        # chat = bot.get_chat(int(session_id))
        # data['chat_title'] = chat.title.encode('utf-8')
        data['updater'] = 'Stopped' if session['stopupdater'] else 'Launched'
        data['updater_task'] = 'TRUE' if session['putupdatertask'] else 'FALSE'
        return f.render_template("TemplateForSession.html", title='Session for chat: %s' % session_id, data=data)

    @app.route("/instruction", methods=['GET', 'POST'])
    def send_instruction():
        return f.render_template("TemplateForInstruction.html")

    @app.route("/DBcleanup", methods=['GET', 'POST'])
    def db_cleanup():
        threads = threading.enumerate()
        for thread in threads:
            if thread.getName() == 'th_db_cleanup':
                return 'Чистка базы от элементов закончившихся игр уже запущена. Нельзя запустить повторно.'
        threading.Thread(name='th_db_cleanup', target=run_db_cleanup, args=[bot]).start()
        return 'Чистка базы от элементов закончившихся игр запущена'

    @app.route("/<session_id>/<game_id>", methods=['GET', 'POST'])
    def all_codes_per_game(session_id, game_id):
        levels_dict = dict()
        sectors_lines = DB.get_sectors_per_game(session_id, game_id)
        bonus_lines = DB.get_bonuses_per_game(session_id, game_id)
        levels_dict = add_level_sectors(levels_dict, sectors_lines)
        levels_dict = add_level_bonuses(levels_dict, bonus_lines)

        levels_list = [level for level in levels_dict.values()]
        return f.render_template("TemplateForCodes.html", title='All codes per game', levels_list=levels_list)

    @app.route("/<session_id>/<game_id>/<level_number>", methods=['GET', 'POST'])
    def all_codes_per_level(session_id, game_id, level_number):
        levels_dict = dict()
        sectors_lines = DB.get_sectors_per_level(session_id, game_id, level_number)
        bonus_lines = DB.get_bonuses_per_level(session_id, game_id, level_number)
        levels_dict = add_level_sectors(levels_dict, sectors_lines)
        levels_dict = add_level_bonuses(levels_dict, bonus_lines)

        levels_list = [level for level in levels_dict.values()]
        return f.render_template("TemplateForCodes.html", title='All codes per %s level' % level_number, levels_list=levels_list)

    @app.route('/favicon.ico')
    def favicon():
        return f.send_from_directory(os.path.join(app.root_path, 'static', 'images'), 'favicon.ico', mimetype='image/png')

    @app.route('/googledocid')
    def googledocid():
        return f.send_from_directory(os.path.join(app.root_path, 'static', 'images'), 'googledocid.png', mimetype='image/png')

    @app.route('/gameid')
    def gameid():
        return f.send_from_directory(os.path.join(app.root_path, 'static', 'images'), 'gameid.png', mimetype='image/png')

    return app
