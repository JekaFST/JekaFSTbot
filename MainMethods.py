# -*- coding: utf-8 -*-
import threading
import time
import re
from BotSession import BotSession
from SessionMethods import compile_urls, login_to_en, send_task_to_chat, send_code_to_level, send_all_sectors_to_chat, \
    send_all_helps_to_chat, send_last_help_to_chat, send_all_bonuses_to_chat, send_task_images_to_chat, launch_session, \
    send_auth_messages_to_chat, send_unclosed_bonuses_to_chat, send_code_to_storm_level, send_task_to_chat_storm


def start(chat_id, bot, sessions_dict):
    if chat_id not in sessions_dict.keys():
        sessions_dict[chat_id] = BotSession()

    bot.send_message(chat_id, 'Чтобы начать использовать бота, необходимо задать конфигурацию игры:\n'
                              '- ввести домен игры (/domain http://demo.en.cx)\n'
                              '- ввести game id игры (/gameid 26991 | 27495)\n'
                              '- ввести логин игрока (/login abc)\n'
                              '- ввести пароль игрока (/password abc)\n'
                              '- залогиниться в движок (/login_to_en)\n'
                              'и активировать сессию (/start_session)\n'
                              'Краткое описание доступно по команде /help', disable_web_page_preview=True)


def stop_session(chat_id, bot, session, additional_chat_ids):
    session.stop_updater = True
    session.put_updater_task = False
    session.use_channel = False
    session.active = False
    bot.send_message(chat_id, 'Сессия остановлена')
    for k, v in additional_chat_ids.items():
        if v == chat_id:
            del additional_chat_ids.updater_schedulers_dict[k]


def config(chat_id, bot, session):
    session_condition = 'Сессия активна' if session.active else 'Сессия не активна'
    channel_condition = '\r\nИмя канала задано' if session.channel_name else '\r\nИмя канала не задано'
    reply = session_condition + '\r\nДомен: ' + session.config['en_domain'] + '\r\nID игры: ' + session.config['game_id'] + \
            '\r\nЛогин: ' + session.config['Login'] + channel_condition + '\r\nИнтервал слежения: ' + str(session.delay)
    bot.send_message(chat_id, reply, disable_web_page_preview=True)


def set_login(chat_id, bot, session, new_login):
    if not session.active:
        session.config['Login'] = new_login
        reply = 'Логин успешно задан' if session.config['Login'] == new_login else 'Логин не задан, повторите'
        bot.send_message(chat_id, reply)
    else:
        bot.send_message(chat_id, 'Нельзя менять логин при активной сессии')


def set_password(chat_id, bot, session, new_password):
    if not session.active:
        session.config['Password'] = new_password
        reply = 'Пароль успешно задан' if session.config['Password'] == new_password else 'Пароль не задана, повторите'
        bot.send_message(chat_id, reply)
    else:
        bot.send_message(chat_id, 'Нельзя менять пароль при активной сессии')


def set_domain(chat_id, bot, session, new_domain):
    if not session.active:
        session.config['en_domain'] = new_domain
        reply = 'Домен успешно задан' if session.config['en_domain'] == new_domain \
            else 'Домен не задан, повторите (/domain http://demo.en.cx)'
        bot.send_message(chat_id, reply)
    else:
        bot.send_message(chat_id, 'Нельзя менять домен при активной сессии')


def set_game_id(chat_id, bot, session, new_game_id):
    if not session.active:
        session.config['game_id'] = new_game_id
        reply = 'Игра успешно задана' if session.config['game_id'] == new_game_id \
            else 'Игра не задана, повторите (/gameid 26991)'
        bot.send_message(chat_id, reply)
    else:
        bot.send_message(chat_id, 'Нельзя менять игру при активной сессии')


def login(chat_id, bot, session):
    if session.config['en_domain'] and session.config['game_id'] and session.config['Login'] and session.config['Password']:
        session.urls = compile_urls(session.urls, session.config)
        login_to_en(session, bot, chat_id)
    else:
        bot.send_message(chat_id, 'Не вся необходимая конфигурация задана. Проверьте домен, id игры, логин и пароль')


def start_session(chat_id, bot, session):
    if session.config['en_domain'] and session.config['game_id'] and session.config['Login'] and session.config['Password']:
        session.urls = compile_urls(session.urls, session.config)
        launch_session(session, bot, chat_id)
    else:
        bot.send_message(chat_id, 'Не вся необходимая конфигурация задана. Проверьте домен, id игры, логин и пароль')


def send_task(chat_id, bot, session, storm_level_number):
    if session.active:
        if not session.storm_game:
            send_task_to_chat(bot, chat_id, session)
        else:
            if not storm_level_number:
                bot.send_message(chat_id, '\xE2\x9D\x97 Укажите уровень: <b>/task номер уровня</b>', parse_mode='HTML')
                return
            send_task_to_chat_storm(bot, chat_id, session, storm_level_number)
    else:
        bot.send_message(chat_id, 'Нельзя запросить задание при неактивной сессии')


def send_task_images(chat_id, bot, session):
    if session.active:
        send_task_images_to_chat(bot, chat_id, session)
    else:
        bot.send_message(chat_id, 'Нельзя запросить задание при неактивной сессии')


def send_all_sectors(chat_id, bot, session):
    if session.active:
        send_all_sectors_to_chat(bot, chat_id, session)
    else:
        bot.send_message(chat_id, 'Нельзя запросить сектора при неактивной сессии')


def send_all_helps(chat_id, bot, session):
    if session.active:
        send_all_helps_to_chat(bot, chat_id, session)
    else:
        bot.send_message(chat_id, 'Нельзя запросить подсказки при неактивной сессии')


def send_last_help(chat_id, bot, session):
    if session.active:
        send_last_help_to_chat(bot, chat_id, session)
    else:
        bot.send_message(chat_id, 'Нельзя запросить подсказку при неактивной сессии')


def send_all_bonuses(chat_id, bot, session):
    if session.active:
        send_all_bonuses_to_chat(bot, chat_id, session)
    else:
        bot.send_message(chat_id, 'Нельзя запросить бонусы при неактивной сессии')


def send_unclosed_bonuses(chat_id, bot, session):
    if session.active:
        send_unclosed_bonuses_to_chat(bot, chat_id, session)
    else:
        bot.send_message(chat_id, 'Нельзя запросить не закрытые бонусы при неактивной сессии')


def send_auth_messages(chat_id, bot, session):
    if session.active:
        send_auth_messages_to_chat(bot, chat_id, session)
    else:
        bot.send_message(chat_id, 'Нельзя запросить сообщения от авторов при неактивной сессии')


def start_updater(chat_id, bot, main_vars):
    session = main_vars.sessions_dict[chat_id]
    if session.active and chat_id not in main_vars.updater_schedulers_dict.keys():
        session.stop_updater = False
        session.put_updater_task = True
        bot.send_message(chat_id, 'Слежение запущено')
        name = 'updater_%s' % chat_id
        main_vars.updater_schedulers_dict[chat_id] = threading.Thread(name=name, target=updater_scheduler,
                                                                      args=(chat_id, bot, main_vars))
        main_vars.updater_schedulers_dict[chat_id].start()
    else:
        bot.send_message(chat_id, 'Нельзя запустить слежение повторно или при неактивной сессии')


def updater_scheduler(chat_id, bot, main_vars):
    session = main_vars.sessions_dict[chat_id]
    while not session.stop_updater:
        if session.put_updater_task:
            time.sleep(session.delay)
            updater_task = {
                'task_type': 'updater',
                'chat_id': chat_id
            }
            main_vars.task_queue.append(updater_task)
            session.put_updater_task = False
    else:
        bot.send_message(chat_id, 'Слежение остановлено')
        if chat_id in main_vars.updater_schedulers_dict.keys():
            del main_vars.updater_schedulers_dict[chat_id]
        return


def set_updater_delay(chat_id, bot, session, new_delay):
    session.delay = new_delay
    reply = 'Задержка успешно выставлена' if session.delay == new_delay else 'Задержка не обновлена, повторите'
    bot.send_message(chat_id, reply)


def stop_updater(session):
    if session.active:
        session.stop_updater = True
        session.put_updater_task = False


def set_channel_name(chat_id, bot, session, new_channel_name):
    if "@" not in new_channel_name:
        new_channel_name = "@" + new_channel_name
    session.channel_name = new_channel_name
    reply = 'Канал успешно задан' if session.channel_name == new_channel_name else 'Канал не задан, повторите'
    bot.send_message(chat_id, reply)


def start_channel(chat_id, bot, session):
    session.use_channel = True
    bot.send_message(chat_id, 'Постинг в канал разрешен')


def stop_channel(chat_id, bot, session):
    session.use_channel = False
    bot.send_message(chat_id, 'Постинг в канал запрещен')


def send_code_main(chat_id, bot, session, message_id, code):
    if session.active:
        if not session.send_codes:
            bot.send_message(chat_id, 'Сдача кодов выключена. Для включения введите команду /codes_on')
            return
        if not session.storm_game:
            send_code_to_level(code, bot, chat_id, message_id, session)
        else:
            try:
                level_number = re.findall(r'([\d]+)\s*!', code)[0]
                code = re.findall(r'!\s*(.+)', code)[0]
            except Exception:
                bot.send_message(chat_id, '\xE2\x9D\x97 Укажите уровень: <b>!номер уровня!код</b>',
                                 reply_to_message_id=message_id, parse_mode='HTML')
                return
            send_code_to_storm_level(code, level_number, bot, chat_id, message_id, session)
    else:
        bot.send_message(chat_id, 'Нельзя сдавать коды при неактивной сессии')


def send_code_bonus(chat_id, bot, session, message_id, code):
    if session.active:
        if not session.send_codes:
            bot.send_message(chat_id, 'Сдача кодов выключена. Для включения введите команду /codes_on')
            return
        if not session.storm_game:
            send_code_to_level(code, bot, chat_id, message_id, session, bonus_only=True)
        else:
            try:
                level_number = re.findall(r'([\d]+)\s*\?', code)[0]
                code = re.findall(r'\?\s*(.+)', code)[0]
            except Exception:
                bot.send_message(chat_id, '\xE2\x9D\x97 Укажите уровень: <b>?номер уровня?код</b>',
                                 reply_to_message_id=message_id, parse_mode='HTML')
                return
            send_code_to_storm_level(code, level_number, bot, chat_id, message_id, session, bonus_only=True)
    else:
        bot.send_message(chat_id, 'Нельзя сдавать коды при неактивной сессии')


def send_coords(chat_id, bot, session, coords):
    if session.active and session.send_coords_active:
        for coord in coords:
            latitude = re.findall(r'\d\d\.\d{4,7}', coord)[0]
            longitude = re.findall(r'\d\d\.\d{4,7}', coord)[1]
            bot.send_location(chat_id, latitude, longitude)


def join(chat_id, bot, message_id, additional_chat_id, additional_chat_ids):
    additional_chat_ids[additional_chat_id] = chat_id
    bot.send_message(chat_id, 'Теперь вы можете работать с ботом через личный чат', reply_to_message_id=message_id)


def reset_join(chat_id, bot, message_id, additional_chat_id, additional_chat_ids):
    del additional_chat_ids[additional_chat_id]
    bot.send_message(chat_id, 'Взаимодействие с ботом через личный чат сброшено', reply_to_message_id=message_id)


def enable_codes(chat_id, bot, session):
    session.send_codes = True
    bot.send_message(chat_id, 'Сдача кодов включена')


def disable_codes(chat_id, bot, session):
    session.send_codes = False
    bot.send_message(chat_id, 'Сдача кодов выключена')
