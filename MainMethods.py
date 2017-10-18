# -*- coding: utf-8 -*-
import threading

import time

from BotSession import BotSession
from SessionMethods import compile_urls, login_to_en, send_task_to_chat


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
