# -*- coding: utf-8 -*-
import re
import os
import logging
import telebot
import threading
import flask as f
from DBMethods import DB
from Worker import queue
from MainClasses import Task, Validations
from BotServiceMethods import run_db_cleanup
from TextConvertingMethods import find_coords
from Const import helptext, num_worker_threads

logging.basicConfig(level=logging.INFO)
bot = telebot.TeleBot("583637976:AAEFrQFiAaGuKwmoRV0N1MwU-ujRzmCxCAo")


def run_app():
    for i in range(num_worker_threads):
        threading.Thread(target=queue.worker, args=[bot]).start()

    app = f.Flask(__name__)

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

    @bot.message_handler(commands=['join'])
    def join_session(message):
        allowed, main_chat_ids, add_chat_ids = Validations.check_permission(message.chat.id, bot)
        if allowed \
                and Validations.check_session_available(message.chat.id, bot) \
                and Validations.check_join_possible(message.chat.id, bot, message.from_user.id, message.message_id, add_chat_ids):
            join_task = Task(message.chat.id, 'join', message_id=message.message_id, user_id=message.from_user.id)
            queue.queue.put((99, join_task))

    @bot.message_handler(commands=['reset_join'])
    def reset_join(message):
        allowed, main_chat_ids, add_chat_ids = Validations.check_permission(message.chat.id, bot)
        if allowed \
                and Validations.check_session_available(message.chat.id, bot) \
                and Validations.check_reset_join_possible(message.chat.id, bot, message.from_user.id, message.message_id, add_chat_ids):
            reset_join_task = Task(message.chat.id, 'reset_join', message_id=message.message_id, user_id=message.from_user.id)
            queue.queue.put((99, reset_join_task))

    @bot.message_handler(commands=['start'])
    def start(message):
        if Validations.check_from_add_chat(message.chat.id):
            bot.send_message(message.chat.id,
                             'Нельзя создать сессию для этого чата.\n'
                             'Этот чат является дополнительным для существующей сессии.'
                             'Краткая инструкция к боту доступна по ссылке:\n'
                             'https://jekafst.net/instruction', disable_web_page_preview=True)
        else:
            start_task = Task(message.chat.id, 'start')
            queue.queue.put((99, start_task))

    @bot.message_handler(commands=['help'])
    def help(message):
        bot.send_message(message.chat.id, helptext, parse_mode='HTML')

    @bot.message_handler(commands=['start_session'])
    def start_session(message):
        if Validations.check_session_available(message.chat.id, bot)\
                and Validations.check_from_main_chat(message.chat.id, bot, message.message_id):

            start_session_task = Task(message.chat.id, 'start_session', session_id=message.chat.id)
            queue.queue.put((99, start_session_task))

    @bot.message_handler(commands=['stop_session'])
    def stop_session(message):
        if Validations.check_session_available(message.chat.id, bot)\
                and Validations.check_from_main_chat(message.chat.id, bot, message.message_id):

            stop_session_task = Task(message.chat.id, 'stop_session', session_id=message.chat.id)
            queue.queue.put((99, stop_session_task))

    @bot.message_handler(commands=['config'])
    def config(message):
        if Validations.check_session_available(message.chat.id, bot) \
                and Validations.check_from_main_chat(message.chat.id, bot, message.message_id):

            config_task = Task(message.chat.id, 'config', session_id=message.chat.id)
            queue.queue.put((99, config_task))

    @bot.message_handler(commands=['login'])
    def save_login(message):
        is_session_available, sessions_ids = Validations.check_session_available(message.chat.id, bot)
        if is_session_available:
            main_chat_id = message.chat.id if message.chat.id in sessions_ids else DB.get_main_chat_id_via_add(message.chat.id)
            new_login = re.findall(r'/login\s*(.+)', str(message.text.encode('utf-8')))[0] if re.findall(r'/login\s*(.+)', str(message.text.encode('utf-8'))) else None
            if not new_login:
                bot.send_message(message.chat.id, 'Введите логин после команды /login, через пробел', reply_to_message_id=message.message_id)
                return
            set_login_task = Task(message.chat.id, 'login', session_id=main_chat_id, new_login=new_login)
            queue.queue.put((99, set_login_task))

    @bot.message_handler(commands=['password'])
    def save_password(message):
        is_session_available, sessions_ids = Validations.check_session_available(message.chat.id, bot)
        if is_session_available:

            main_chat_id = message.chat.id if message.chat.id in sessions_ids else DB.get_main_chat_id_via_add(message.chat.id)
            new_password = re.findall(r'/password\s*(.+)', str(message.text.encode('utf-8')))[0] if re.findall(r'/password\s*(.+)', str(message.text.encode('utf-8'))) else None
            if not new_password:
                bot.send_message(message.chat.id, 'Введите пароль после команды /password, через пробел', reply_to_message_id=message.message_id)
                return
            set_password_task = Task(message.chat.id, 'password', session_id=main_chat_id, new_password=new_password)
            queue.queue.put((99, set_password_task))

    @bot.message_handler(commands=['domain'])
    def save_en_domain(message):
        is_session_available, sessions_ids = Validations.check_session_available(message.chat.id, bot)
        if is_session_available:

            main_chat_id = message.chat.id if message.chat.id in sessions_ids else DB.get_main_chat_id_via_add(message.chat.id)
            new_domain = re.findall(r'/domain\s*(.+)', str(message.text.encode('utf-8')))[0] if re.findall(r'/domain\s*(.+)', str(message.text.encode('utf-8'))) else None
            if not new_domain:
                bot.send_message(message.chat.id, 'Введите домен после команды /domain, через пробел', reply_to_message_id=message.message_id)
                return
            set_domain_task = Task(message.chat.id, 'domain', session_id=main_chat_id, new_domain=new_domain)
            queue.queue.put((99, set_domain_task))

    @bot.message_handler(commands=['gameid'])
    def save_game_id(message):
        is_session_available, sessions_ids = Validations.check_session_available(message.chat.id, bot)
        if is_session_available:

            main_chat_id = message.chat.id if message.chat.id in sessions_ids else DB.get_main_chat_id_via_add(message.chat.id)
            new_game_id = re.findall(r'[\d]+', str(message.text.encode('utf-8')))[0] if re.findall(r'[\d]+', str(message.text.encode('utf-8'))) else None
            if not new_game_id:
                bot.send_message(message.chat.id, 'Введите айди игры после команды /gameid, через пробел', reply_to_message_id=message.message_id)
                return
            set_game_id_task = Task(message.chat.id, 'game_id', session_id=main_chat_id, new_game_id=new_game_id)
            queue.queue.put((99, set_game_id_task))

    @bot.message_handler(commands=['login_to_en'])
    def login_to_en(message):
        if Validations.check_session_available(message.chat.id, bot)\
                and Validations.check_from_main_chat(message.chat.id, bot, message.message_id):

            login_to_en_task = Task(message.chat.id, 'login_to_en', session_id=message.chat.id)
            queue.queue.put((99, login_to_en_task))

    @bot.message_handler(commands=['task'])
    def send_task(message):
        is_session_available, sessions_ids = Validations.check_session_available(message.chat.id, bot)
        if is_session_available:

            main_chat_id = message.chat.id if message.chat.id in sessions_ids else DB.get_main_chat_id_via_add(message.chat.id)
            storm_level = int(re.search(r'[\d]+', str(message.text.encode('utf-8'))).group(0)) if \
                re.findall(r'[\d]+', str(message.text.encode('utf-8'))) else None
            send_task_task = Task(message.chat.id, 'send_task', session_id=main_chat_id, storm_level_number=storm_level)
            queue.queue.put((99, send_task_task))

    @bot.message_handler(commands=['task_images'])
    def send_task_images(message):
        is_session_available, sessions_ids = Validations.check_session_available(message.chat.id, bot)
        if is_session_available:

            main_chat_id = message.chat.id if message.chat.id in sessions_ids else DB.get_main_chat_id_via_add(message.chat.id)
            send_task_images_task = Task(message.chat.id, 'task_images', session_id=main_chat_id)
            queue.queue.put((99, send_task_images_task))

    @bot.message_handler(commands=['sectors'])
    def send_all_sectors(message):
        allowed, main_chat_ids, add_chat_ids = Validations.check_permission(message.chat.id, bot)
        if allowed and Validations.check_session_available(message.chat.id, bot):

            main_chat_id = message.chat.id if message.chat.id in main_chat_ids else DB.get_main_chat_id_via_add(message.chat.id)
            storm_level = int(re.search(r'[\d]+', str(message.text.encode('utf-8'))).group(0)) if \
                re.findall(r'[\d]+', str(message.text.encode('utf-8'))) else None
            send_all_sectors_task = Task(message.chat.id, 'send_sectors', session_id=main_chat_id, storm_level_number=storm_level)
            queue.queue.put((99, send_all_sectors_task))

    @bot.message_handler(commands=['hints'])
    def send_all_helps(message):
        allowed, main_chat_ids, add_chat_ids = Validations.check_permission(message.chat.id, bot)
        if allowed and Validations.check_session_available(message.chat.id, bot):

            main_chat_id = message.chat.id if message.chat.id in main_chat_ids else DB.get_main_chat_id_via_add(message.chat.id)
            storm_level = int(re.search(r'[\d]+', str(message.text.encode('utf-8'))).group(0)) if \
                re.findall(r'[\d]+', str(message.text.encode('utf-8'))) else None
            send_all_helps_task = Task(message.chat.id, 'send_helps', session_id=main_chat_id, storm_level_number=storm_level)
            queue.queue.put((99, send_all_helps_task))

    @bot.message_handler(commands=['last_hint'])
    def send_last_help(message):
        allowed, main_chat_ids, add_chat_ids = Validations.check_permission(message.chat.id, bot)
        if allowed and Validations.check_session_available(message.chat.id, bot):

            main_chat_id = message.chat.id if message.chat.id in main_chat_ids else DB.get_main_chat_id_via_add(message.chat.id)
            storm_level = int(re.search(r'[\d]+', str(message.text.encode('utf-8'))).group(0)) if \
                re.findall(r'[\d]+', str(message.text.encode('utf-8'))) else None
            send_last_help_task = Task(message.chat.id, 'send_last_help', session_id=main_chat_id, storm_level_number=storm_level)
            queue.queue.put((99, send_last_help_task))

    @bot.message_handler(commands=['bonuses'])
    def send_all_bonuses(message):
        allowed, main_chat_ids, add_chat_ids = Validations.check_permission(message.chat.id, bot)
        if allowed and Validations.check_session_available(message.chat.id, bot):

            main_chat_id = message.chat.id if message.chat.id in main_chat_ids else DB.get_main_chat_id_via_add(message.chat.id)
            storm_level = int(re.search(r'[\d]+', str(message.text.encode('utf-8'))).group(0)) if \
                re.findall(r'[\d]+', str(message.text.encode('utf-8'))) else None
            send_all_bonuses_task = Task(message.chat.id, 'send_bonuses', session_id=main_chat_id, storm_level_number=storm_level)
            queue.queue.put((99, send_all_bonuses_task))

    @bot.message_handler(commands=['unclosed_bonuses'])
    def send_unclosed_bonuses(message):
        allowed, main_chat_ids, add_chat_ids = Validations.check_permission(message.chat.id, bot)
        if allowed and Validations.check_session_available(message.chat.id, bot):

            main_chat_id = message.chat.id if message.chat.id in main_chat_ids else DB.get_main_chat_id_via_add(message.chat.id)
            storm_level = int(re.search(r'[\d]+', str(message.text.encode('utf-8'))).group(0)) if \
                re.findall(r'[\d]+', str(message.text.encode('utf-8'))) else None
            send_unclosed_bonuses_task = Task(message.chat.id, 'unclosed_bonuses', session_id=main_chat_id, storm_level_number=storm_level)
            queue.queue.put((99, send_unclosed_bonuses_task))

    @bot.message_handler(commands=['messages'])
    def send_auth_messages(message):
        allowed, main_chat_ids, add_chat_ids = Validations.check_permission(message.chat.id, bot)
        if allowed and Validations.check_session_available(message.chat.id, bot):

            main_chat_id = message.chat.id if message.chat.id in main_chat_ids else DB.get_main_chat_id_via_add(message.chat.id)
            storm_level = int(re.search(r'[\d]+', str(message.text.encode('utf-8'))).group(0)) if \
                re.findall(r'[\d]+', str(message.text.encode('utf-8'))) else None
            send_auth_messages_task = Task(message.chat.id, 'send_messages', session_id=main_chat_id, storm_level_number=storm_level)
            queue.queue.put((99, send_auth_messages_task))

    @bot.message_handler(commands=['start_updater'])
    def start_updater(message):
        allowed, main_chat_ids, add_chat_ids = Validations.check_permission(message.chat.id, bot)
        if allowed and Validations.check_session_available(message.chat.id, bot) \
                and Validations.check_from_main_chat(message.chat.id, bot, main_chat_ids, message.message_id):

            start_updater_task = Task(message.chat.id, 'start_updater', queue=queue, session_id=message.chat.id)
            queue.queue.put((2, start_updater_task))

    @bot.message_handler(commands=['delay'])
    def set_updater_delay(message):
        allowed, main_chat_ids, add_chat_ids = Validations.check_permission(message.chat.id, bot)
        if allowed and Validations.check_session_available(message.chat.id, bot) \
                and Validations.check_from_main_chat(message.chat.id, bot, main_chat_ids, message.message_id):

            new_delay = int(re.search(r'[\d]+', str(message.text.encode('utf-8'))).group(0))
            set_delay_task = Task(message.chat.id, 'delay', session_id=message.chat.id, new_delay=new_delay)
            queue.queue.put((99, set_delay_task))

    @bot.message_handler(commands=['stop_updater'])
    def stop_updater(message):
        allowed, main_chat_ids, add_chat_ids = Validations.check_permission(message.chat.id, bot)
        if allowed and Validations.check_session_available(message.chat.id, bot) \
                and Validations.check_from_main_chat(message.chat.id, bot, main_chat_ids, message.message_id):

            stop_updater_task = Task(message.chat.id, 'stop_updater', session_id=message.chat.id)
            queue.queue.put((2, stop_updater_task))

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
            queue.queue.put((99, set_channel_name_task))

    @bot.message_handler(commands=['start_channel'])
    def start_channel(message):
        allowed, main_chat_ids, add_chat_ids = Validations.check_permission(message.chat.id, bot)
        if allowed and Validations.check_session_available(message.chat.id, bot) \
                and Validations.check_from_main_chat(message.chat.id, bot, main_chat_ids, message.message_id):

            start_channel_task = Task(message.chat.id, 'start_channel', session_id=message.chat.id)
            queue.queue.put((99, start_channel_task))

    @bot.message_handler(commands=['stop_channel'])
    def stop_channel(message):
        allowed, main_chat_ids, add_chat_ids = Validations.check_permission(message.chat.id, bot)
        if allowed and Validations.check_session_available(message.chat.id, bot) \
                and Validations.check_from_main_chat(message.chat.id, bot, main_chat_ids, message.message_id):

            stop_channel_task = Task(message.chat.id, 'stop_channel', session_id=message.chat.id)
            queue.queue.put((99, stop_channel_task))

    @bot.message_handler(commands=['codes_on'])
    def enable_codes(message):
        allowed, main_chat_ids, add_chat_ids = Validations.check_permission(message.chat.id, bot)
        if allowed and Validations.check_session_available(message.chat.id, bot) \
                and Validations.check_from_main_chat(message.chat.id, bot, main_chat_ids, message.message_id):

            enable_codes_task = Task(message.chat.id, 'codes_on', session_id=message.chat.id)
            queue.queue.put((1, enable_codes_task))

    @bot.message_handler(commands=['codes_off'])
    def disable_codes(message):
        allowed, main_chat_ids, add_chat_ids = Validations.check_permission(message.chat.id, bot)
        if allowed and Validations.check_session_available(message.chat.id, bot) \
                and Validations.check_from_main_chat(message.chat.id, bot, main_chat_ids, message.message_id):

            disable_codes_task = Task(message.chat.id, 'codes_off', session_id=message.chat.id)
            queue.queue.put((0, disable_codes_task))

    @bot.message_handler(commands=['add_tag'])
    def add_tag(message):
        if message.chat.id != 45839899:
            bot.send_message(message.chat.id, 'Данная команда не доступна из этого чата')
            return
        tag_to_add = re.findall(r'/add_tag\s*(.+)', str(message.text.encode('utf-8')))[0]
        if DB.insert_tag_in_tags_list(tag_to_add):
            bot.send_message(message.chat.id, 'Тег успешно добавлен в обработчик')
        else:
            bot.send_message(message.chat.id, 'Тег не добавлен в обработчик, повторите попытку')

    @bot.message_handler(commands=['ll'])
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
            queue.queue.put((99, send_live_location_task))

    @bot.message_handler(commands=['stop_ll'])
    def stop_live_location(message):
        allowed, main_chat_ids, add_chat_ids = Validations.check_permission(message.chat.id, bot)
        if allowed and Validations.check_session_available(message.chat.id, bot):

            main_chat_id = message.chat.id if message.chat.id in main_chat_ids else DB.get_main_chat_id_via_add(message.chat.id)
            point_number = re.findall(r'\s+(\d{1,2})', str(message.text.encode('utf-8')))
            point = point_number[0] if point_number else None
            stop_live_location_task = Task(message.chat.id, 'stop_live_location', session_id=main_chat_id, point=point)
            queue.queue.put((99, stop_live_location_task))

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
            queue.queue.put((99, edit_live_location_task))

    @bot.message_handler(commands=['clean_ll'])
    def clean_ll(message):
        allowed, main_chat_ids, add_chat_ids = Validations.check_permission(message.chat.id, bot)
        if allowed and Validations.check_session_available(message.chat.id, bot):

            main_chat_id = message.chat.id if message.chat.id in main_chat_ids else DB.get_main_chat_id_via_add(message.chat.id)
            clean_live_location_task = Task(message.chat.id, 'clean_ll', session_id=main_chat_id)
            queue.queue.put((99, clean_live_location_task))

    @bot.message_handler(commands=['addll'])
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
            queue.queue.put((99, add_points_ll_task))

    @bot.message_handler(commands=['get_codes_links'])
    def get_codes_links(message):
        allowed, main_chat_ids, add_chat_ids = Validations.check_permission(message.chat.id, bot)
        if allowed and Validations.check_session_available(message.chat.id, bot) \
                and Validations.check_from_main_chat(message.chat.id, bot, main_chat_ids, message.message_id):

            get_codes_links_task = Task(message.chat.id, 'get_codes_links', session_id=message.chat.id, message_id=message.message_id)
            queue.queue.put((99, get_codes_links_task))

    @bot.message_handler(commands=['kml'])
    def get_map_file(message):
        allowed, main_chat_ids, add_chat_ids = Validations.check_permission(message.chat.id, bot)
        if allowed and Validations.check_session_available(message.chat.id, bot):

            main_chat_id = message.chat.id if message.chat.id in main_chat_ids else DB.get_main_chat_id_via_add(message.chat.id)
            points = list()
            chat_points = re.findall(
                r'.+\s*-\s*\d\d\.\d{4,7},\s{,3}\d\d\.\d{4,7}\s*-\s*.+|'
                r'.+\s*-\s*\d\d\.\d{4,7}\s{1,3}\d\d\.\d{4,7}\s*-\s*.+|'
                r'\d\d\.\d{4,7},\s{,3}\d\d\.\d{4,7}\s*-\s*.+|'
                r'\d\d\.\d{4,7}\s{1,3}\d\d\.\d{4,7}\s*-\s*.+|'
                r'.+\s*-\s*\d\d\.\d{4,7},\s{,3}\d\d\.\d{4,7}|'
                r'.+\s*-\s*\d\d\.\d{4,7}\s{1,3}\d\d\.\d{4,7}|'
                r'\d\d\.\d{4,7},\s{,3}\d\d\.\d{4,7}|'
                r'\d\d\.\d{4,7}\s{1,3}\d\d\.\d{4,7}', message.text, re.U)
            for point in chat_points:
                points.append({
                    'name': re.findall(r'(.+)\s*-\s*\d\d\.\d{4,7}', point, re.U)[0] if re.findall(r'(.+)\s*-\s*\d\d\.\d{4,7}', point, re.U) else None,
                    'coords': re.findall(r'\d\d\.\d{4,7},\s{,3}\d\d\.\d{4,7}|\d\d\.\d{4,7}\s{1,3}\d\d\.\d{4,7}', point)[0],
                    'description': re.findall(r'\d\d\.\d{4,7}\s*-\s*(.+)', point, re.U)[0] if re.findall(r'\d\d\.\d{4,7}\s*-\s*(.+)', point, re.U) else None
                })
            get_map_file_task = Task(message.chat.id, 'get_map_file', session_id=main_chat_id, points=points, message_id=message.message_id)
            queue.queue.put((99, get_map_file_task))

    @bot.message_handler(commands=['instruction'])
    def send_instruction(message):
        bot.send_message(message.chat.id, 'https://jekafst.net/instruction')

    @bot.message_handler(regexp='^[!\./]\s*(.+)')
    def main_code_processor(message):
        allowed, main_chat_ids, add_chat_ids = Validations.check_permission(message.chat.id, bot)
        if allowed and Validations.check_session_available(message.chat.id, bot):

            main_chat_id = message.chat.id if message.chat.id in main_chat_ids else DB.get_main_chat_id_via_add(message.chat.id)
            code = re.findall(r'[!\./]\s*(.+)', str(message.text.lower().encode('utf-8')))[0]
            send_code_main_task = Task(message.chat.id, 'send_code_main', session_id=main_chat_id, code=code,
                                       message_id=message.message_id)
            queue.queue.put((1, send_code_main_task))

    @bot.message_handler(regexp='^\?\s*(.+)')
    def bonus_code_processor(message):
        allowed, main_chat_ids, add_chat_ids = Validations.check_permission(message.chat.id, bot)
        if allowed and Validations.check_session_available(message.chat.id, bot):

            main_chat_id = message.chat.id if message.chat.id in main_chat_ids else DB.get_main_chat_id_via_add(message.chat.id)
            code = re.findall(r'\?\s*(.+)', str(message.text.lower().encode('utf-8')))[0]
            send_code_bonus_task = Task(message.chat.id, 'send_code_bonus', session_id=main_chat_id, code=code,
                                        message_id=message.message_id)
            queue.queue.put((1, send_code_bonus_task))

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
                queue.queue.put((99, send_coords_task))

    @app.route("/")
    def index():
        return f.render_template("TemplateForInstruction.html")

    @app.route("/instruction", methods=['GET'])
    def send_instruction():
        return f.render_template("TemplateForInstruction.html")

    @app.route("/db-cleanup", methods=['GET', 'POST'])
    def db_cleanup():
        threads = threading.enumerate()
        for thread in threads:
            if thread.getName() == 'th_db_cleanup':
                return 'Чистка базы от элементов закончившихся игр уже запущена. Нельзя запустить повторно.'
        threading.Thread(name='th_db_cleanup', target=run_db_cleanup, args=[bot]).start()
        return 'Чистка базы от элементов закончившихся игр запущена'

    @app.route('/favicon.ico', methods=['GET'])
    def favicon():
        return f.send_from_directory(os.path.join(app.root_path, 'static', 'images'), 'favicon.ico', mimetype='image/png')

    return app


app = run_app()


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, threaded=True)
