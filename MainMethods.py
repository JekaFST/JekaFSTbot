# -*- coding: utf-8 -*-
import threading
import time
import re
from BotSession import BotSession
from SessionMethods import compile_urls, login_to_en, send_task_to_chat, send_code_to_level


def start(chat_id, bot, sessions_dict):
    if chat_id not in sessions_dict.keys():
        sessions_dict[chat_id] = BotSession()

    bot.send_message(chat_id, 'Чтобы начать использовать бота, необходимо задать конфигурацию игры:\n'
                              'ввести домен игры (/domain http://demo.en.cx)\n'
                              'ввести game id игры (/gameid 26991)\n'
                              'и залогиниться в движок (/login)\n'
                              'Краткое описание доступно по команде /help', disable_web_page_preview=True)
    sessions_dict[chat_id].active = True


def stop(chat_id, bot, session):
    bot.send_message(chat_id, 'Бот выключен. Настройки сброшены')
    session.stop_updater = True
    session.use_channel = False
    session.active = False


def config(chat_id, bot, session):
    session_condition = 'Сессия активна' if session.active else 'Сессия не активна'
    channel_condition = '\r\nИмя канала задано' if session.channel_name else '\r\nИмя канала не задано'
    reply = session_condition + '\r\nДомен: ' + session.config['en_domain'] +\
            '\r\nID игры: ' + session.config['game_id'] + '\r\nЛогин: ' + session.config['Login'] + channel_condition
    bot.send_message(chat_id, session_condition + reply, disable_web_page_preview=True)


def set_login(chat_id, bot, session, new_login):
    if session.active:
        session.config['Login'] = new_login
        reply = 'Логин успешно задан' if session.config['Login'] else 'Логин не задан, повторите'
        bot.send_message(chat_id, reply)


def set_password(chat_id, bot, session, new_password):
    if session.active:
        session.config['Password'] = new_password
        reply = 'Пароль успешно задан' if session.config['Password'] else 'Пароль не задана, повторите'
        bot.send_message(chat_id, reply)


def set_domain(chat_id, bot, session, new_domain):
    if session.active:
        session.config['en_domain'] = new_domain
        reply = 'Домен успешно задан' if session.config['en_domain'] \
            else 'Домен не задан, повторите (/domain http://demo.en.cx)'
        bot.send_message(chat_id, reply)


def set_game_id(chat_id, bot, session, new_game_id):
    if session.active:
        session.config['game_id'] = new_game_id
        reply = 'Игра успешно задана' if session.config['game_id'] else 'Игра не задана, повторите (/gameid 26991)'
        bot.send_message(chat_id, reply)


def login(chat_id, bot, session):
    if session.active:
        session.urls = compile_urls(session.urls, session.config)
        reply = login_to_en(session, bot, chat_id)
        bot.send_message(chat_id, reply)


def send_task(chat_id, bot, session):
    if session.active:
        send_task_to_chat(bot, chat_id, session)


def start_updater(chat_id, bot, main_vars):
    session = main_vars.sessions_dict[chat_id]
    if session.active:
        session.stop_updater = False
        bot.send_message(chat_id, 'Слежение запущено')
        name = 'updater_%s' % chat_id
        main_vars.updater_schedulers_dict[chat_id] = threading.Thread(name=name, target=updater_scheduler,
                                                                      args=(chat_id, bot, main_vars))
        main_vars.updater_schedulers_dict[chat_id].start()


def updater_scheduler(chat_id, bot, main_vars):
    session = main_vars.sessions_dict[chat_id]
    while not session.stop_updater:
        chat_ids = list()
        for task in main_vars.task_queue:
            if task['task_type'] == 'updater':
                chat_ids.append(task['chat_id'])
        if chat_id not in chat_ids:
            time.sleep(session.delay)
            updater_task = {
                'task_id': main_vars.id,
                'task_type': 'updater',
                'chat_id': chat_id
            }
            main_vars.task_queue.append(updater_task)
            main_vars.id += 1
    else:
        bot.send_message(chat_id, 'Слежение остановлено')
        return


def stop_updater(session):
    if session.active:
        session.stop_updater = True


def send_code_main(chat_id, bot, session, message_id, code):
    if session.active:
        send_code_to_level(code, bot, chat_id, message_id, session)


def send_code_bonus(chat_id, bot, session, message_id, code):
    if session.active:
        send_code_to_level(code, bot, chat_id, message_id, session, bonus_only=True)


def send_coords(chat_id, bot, session, coords):
    if session.active and session.send_coords_active:
        for coord in coords:
            latitude = re.findall(r'\d\d\.\d{4,7}', coord)[0]
            longitude = re.findall(r'\d\d\.\d{4,7}', coord)[1]
            bot.send_location(chat_id, latitude, longitude)
