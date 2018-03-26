# -*- coding: utf-8 -*-
import json
import threading
import time
import re
import telebot
from BotSession import BotSession
from CommonMethods import close_live_locations
from DBMethods import DB
from SessionMethods import compile_urls, login_to_en, send_task_to_chat, send_code_to_level, send_all_sectors_to_chat, \
    send_all_helps_to_chat, send_last_help_to_chat, send_all_bonuses_to_chat, send_task_images_to_chat, launch_session, \
    send_auth_messages_to_chat, send_unclosed_bonuses_to_chat, send_code_to_storm_level, send_task_to_chat_storm, \
    drop_session_vars, send_all_helps_to_chat_storm, send_last_help_to_chat_storm, send_all_sectors_to_chat_storm, \
    send_all_bonuses_to_chat_storm, send_unclosed_bonuses_to_chat_storm, send_auth_messages_to_chat_storm, \
    send_live_locations_to_chat


def start(chat_id, bot, sessions_dict, **kwargs):
    config = DB.get_config_by_chat_id(chat_id)
    if chat_id not in sessions_dict.keys() and not config:
        sessions_dict[chat_id] = BotSession()
        bot.send_message(chat_id, '<b>Сессия создана</b>\n'
                                  'Чтобы начать использовать бота, необходимо задать конфигурацию игры:\n'
                                  '- ввести домен игры (/domain http://demo.en.cx)\n'
                                  '- ввести game id игры (/gameid 26991)\n'
                                  '- ввести логин игрока (/login abc)\n'
                                  '- ввести пароль игрока (/password abc)\n'
                                  '- залогиниться в движок (/login_to_en)\n'
                                  'и активировать сессию (/start_session)\n'
                                  'Краткое описание доступно по команде /help', disable_web_page_preview=True, parse_mode='HTML')
    elif chat_id not in sessions_dict.keys() and config:
        sessions_dict[chat_id] = BotSession()
        sessions_dict[chat_id].config['Login'] = config['login']
        sessions_dict[chat_id].config['Password'] = config['password']
        sessions_dict[chat_id].config['en_domain'] = config['endomain']
        sessions_dict[chat_id].channel_name = config['channelname']
        bot.send_message(chat_id, '<b>Сессия создана</b>\n'
                                  'Для данного чата найдена конфигурация по умолчанию. Проверить: /config\n'
                                  'Чтобы начать использовать бота, необходимо:\n'
                                  '- ввести game id игры (/gameid 26991)\n'
                                  '- залогиниться в движок (/login_to_en)\n'
                                  'и активировать сессию (/start_session)\n'
                                  '- сменить домен игры (/domain http://demo.en.cx)\n'
                                  '- сменить логин игрока (/login abc)\n'
                                  '- сменить пароль игрока (/password abc)\n'
                                  'Краткое описание доступно по команде /help', disable_web_page_preview=True, parse_mode='HTML')
    else:
        bot.send_message(chat_id, 'Для данного чата уже создана сессия\n'
                                  'Введите /config для проверки ее состояния')


def stop_session(chat_id, bot, session, add_chat_ids_per_session, **kwargs):
    session.stop_updater = True
    session.put_updater_task = False
    session.use_channel = False
    session.active = False
    bot.send_message(chat_id, 'Сессия остановлена')
    for add_chat_id in add_chat_ids_per_session:
        DB.delete_add_chat_id(add_chat_id)


def config(chat_id, bot, session, **kwargs):
    session_condition = 'Сессия активна' if session.active else 'Сессия не активна'
    channel_condition = '\r\nИмя канала задано' if session.channel_name else '\r\nИмя канала не задано'
    reply = session_condition + '\r\nДомен: ' + session.config['en_domain'] + '\r\nID игры: ' + session.config['game_id'] + \
            '\r\nЛогин: ' + session.config['Login'] + channel_condition + '\r\nИнтервал слежения: ' + str(session.delay)
    bot.send_message(chat_id, reply, disable_web_page_preview=True)


def set_login(chat_id, bot, session, new_login, **kwargs):
    if not session.active:
        session.config['Login'] = new_login
        reply = 'Логин успешно задан' if session.config['Login'] == new_login else 'Логин не задан, повторите'
        bot.send_message(chat_id, reply)
    else:
        bot.send_message(chat_id, 'Нельзя менять логин при активной сессии')


def set_password(chat_id, bot, session, new_password, **kwargs):
    if not session.active:
        session.config['Password'] = new_password
        reply = 'Пароль успешно задан' if session.config['Password'] == new_password else 'Пароль не задана, повторите'
        bot.send_message(chat_id, reply)
    else:
        bot.send_message(chat_id, 'Нельзя менять пароль при активной сессии')


def set_domain(chat_id, bot, session, new_domain, **kwargs):
    if not session.active:
        if 'http://' not in new_domain:
            new_domain = 'http://' + new_domain
        session.config['en_domain'] = new_domain
        reply = 'Домен успешно задан' if session.config['en_domain'] == new_domain \
            else 'Домен не задан, повторите (/domain http://demo.en.cx)'
        bot.send_message(chat_id, reply)
    else:
        bot.send_message(chat_id, 'Нельзя менять домен при активной сессии')


def set_game_id(chat_id, bot, session, new_game_id, **kwargs):
    if not session.active:
        session.config['game_id'] = new_game_id
        reply = 'Игра успешно задана' if session.config['game_id'] == new_game_id \
            else 'Игра не задана, повторите (/gameid 26991)'
        drop_session_vars(session)
        bot.send_message(chat_id, reply)
    else:
        bot.send_message(chat_id, 'Нельзя менять игру при активной сессии')


def login(chat_id, bot, session, **kwargs):
    if session.config['en_domain'] and session.config['game_id'] and session.config['Login'] and session.config['Password']:
        session.urls = compile_urls(session.config)
        login_to_en(session, bot, chat_id)
    else:
        bot.send_message(chat_id, 'Не вся необходимая конфигурация задана. Проверьте домен, id игры, логин и пароль')


def start_session(chat_id, bot, session, **kwargs):
    if not session.active:
        if session.config['cookie'] and session.config['game_id'] and session.config['Login'] and session.config['Password']:
            launch_session(session, bot, chat_id)
        else:
            bot.send_message(chat_id, 'Не вся необходимая конфигурация задана. Проверьте домен, id игры, логин и пароль')
    else:
        bot.send_message(chat_id, 'Сессия уже активирована. Если у вас проблемы со слежением - попробуйте '
                                  '/stop_updater, затем /start_updater')


def send_task(chat_id, bot, session, storm_level_number, **kwargs):
    if not session.active:
        bot.send_message(chat_id, 'Нельзя запросить задание при неактивной сессии')
        return
    if not session.storm_game:
        send_task_to_chat(bot, chat_id, session)
    else:
        if not storm_level_number:
            bot.send_message(chat_id, '\xE2\x9D\x97 Укажите уровень: <b>/task номер уровня</b>', parse_mode='HTML')
            return
        send_task_to_chat_storm(bot, chat_id, session, storm_level_number)


def send_task_images(chat_id, bot, session, **kwargs):
    if session.active:
        send_task_images_to_chat(bot, chat_id, session)
    else:
        bot.send_message(chat_id, 'Нельзя запросить задание при неактивной сессии')


def send_all_sectors(chat_id, bot, session, storm_level_number, **kwargs):
    if not session.active:
        bot.send_message(chat_id, 'Нельзя запросить сектора при неактивной сессии')
        return
    if not session.storm_game:
        send_all_sectors_to_chat(bot, chat_id, session)
    else:
        if not storm_level_number:
            bot.send_message(chat_id, '\xE2\x9D\x97 Укажите уровень: <b>/sectors номер уровня</b>', parse_mode='HTML')
            return
        send_all_sectors_to_chat_storm(bot, chat_id, session, storm_level_number)


def send_all_helps(chat_id, bot, session, storm_level_number, **kwargs):
    if not session.active:
        bot.send_message(chat_id, 'Нельзя запросить подсказки при неактивной сессии')
        return
    if not session.storm_game:
        send_all_helps_to_chat(bot, chat_id, session)
    else:
        if not storm_level_number:
            bot.send_message(chat_id, '\xE2\x9D\x97 Укажите уровень: <b>/helps номер уровня</b>', parse_mode='HTML')
            return
        send_all_helps_to_chat_storm(bot, chat_id, session, storm_level_number)


def send_last_help(chat_id, bot, session, storm_level_number, **kwargs):
    if not session.active:
        bot.send_message(chat_id, 'Нельзя запросить подсказку при неактивной сессии')
        return
    if not session.storm_game:
            send_last_help_to_chat(bot, chat_id, session)
    else:
        if not storm_level_number:
            bot.send_message(chat_id, '\xE2\x9D\x97 Укажите уровень: <b>/last_help номер уровня</b>', parse_mode='HTML')
            return
        send_last_help_to_chat_storm(bot, chat_id, session, storm_level_number)


def send_all_bonuses(chat_id, bot, session, storm_level_number, **kwargs):
    if not session.active:
        bot.send_message(chat_id, 'Нельзя запросить бонусы при неактивной сессии')
        return
    if not session.storm_game:
        send_all_bonuses_to_chat(bot, chat_id, session)
    else:
        if not storm_level_number:
            bot.send_message(chat_id, '\xE2\x9D\x97 Укажите уровень: <b>/bonuses номер уровня</b>', parse_mode='HTML')
            return
        send_all_bonuses_to_chat_storm(bot, chat_id, session, storm_level_number)


def send_unclosed_bonuses(chat_id, bot, session, storm_level_number, **kwargs):
    if not session.active:
        bot.send_message(chat_id, 'Нельзя запросить не закрытые бонусы при неактивной сессии')
        return
    if not session.storm_game:
        send_unclosed_bonuses_to_chat(bot, chat_id, session)
    else:
        if not storm_level_number:
            bot.send_message(chat_id, '\xE2\x9D\x97 Укажите уровень: <b>/unclosed_bonuses номер уровня</b>', parse_mode='HTML')
            return
        send_unclosed_bonuses_to_chat_storm(bot, chat_id, session, storm_level_number)


def send_auth_messages(chat_id, bot, session, storm_level_number, **kwargs):
    if not session.active:
        bot.send_message(chat_id, 'Нельзя запросить сообщения от авторов при неактивной сессии')
        return
    if not session.storm_game:
        send_auth_messages_to_chat(bot, chat_id, session)
    else:
        if not storm_level_number:
            bot.send_message(chat_id, '\xE2\x9D\x97 Укажите уровень: <b>/messages номер уровня</b>', parse_mode='HTML')
            return
        send_auth_messages_to_chat_storm(bot, chat_id, session, storm_level_number)


def start_updater(chat_id, bot, main_vars, **kwargs):
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


def set_updater_delay(chat_id, bot, session, new_delay, **kwargs):
    session.delay = new_delay
    reply = 'Задержка успешно выставлена' if session.delay == new_delay else 'Задержка не обновлена, повторите'
    bot.send_message(chat_id, reply)


def stop_updater(session, **kwargs):
    if session.active:
        session.stop_updater = True
        session.put_updater_task = False


def set_channel_name(chat_id, bot, session, new_channel_name, **kwargs):
    if "@" not in new_channel_name:
        new_channel_name = "@" + new_channel_name
    session.channel_name = new_channel_name
    reply = 'Канал успешно задан' if session.channel_name == new_channel_name else 'Канал не задан, повторите'
    bot.send_message(chat_id, reply)


def start_channel(chat_id, bot, session, **kwargs):
    session.use_channel = True
    bot.send_message(chat_id, 'Постинг в канал разрешен')


def stop_channel(chat_id, bot, session, **kwargs):
    session.use_channel = False
    bot.send_message(chat_id, 'Постинг в канал запрещен')


def send_code_main(chat_id, bot, session, message_id, code):
    if not session.active:
        bot.send_message(chat_id, 'Нельзя сдавать коды при неактивной сессии')
        return
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


def send_code_bonus(chat_id, bot, session, message_id, code):
    if not session.active:
        bot.send_message(chat_id, 'Нельзя сдавать коды при неактивной сессии')
        return
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


def send_coords(chat_id, bot, coords):
    for coord in coords:
        latitude = re.findall(r'\d\d\.\d{4,7}', coord)[0]
        longitude = re.findall(r'\d\d\.\d{4,7}', coord)[1]
        bot.send_venue(chat_id, latitude, longitude, coord, '')


def join(bot, message_id, add_chat_id, **kwargs):
    DB.insert_add_chat_id(kwargs['chat_id'], add_chat_id)
    bot.send_message(kwargs['chat_id'], 'Теперь вы можете работать с ботом через личный чат', reply_to_message_id=message_id)


def reset_join(chat_id, bot, message_id, add_chat_id, **kwargs):
    # main_chat_id = DB.get_main_chat_id_via_add(add_chat_id)
    DB.delete_add_chat_id(add_chat_id)
    bot.send_message(chat_id, 'Взаимодействие с ботом через личный чат сброшено', reply_to_message_id=message_id)


def enable_codes(chat_id, bot, session, **kwargs):
    session.send_codes = True
    bot.send_message(chat_id, 'Сдача кодов включена')


def disable_codes(chat_id, bot, session, **kwargs):
    session.send_codes = False
    bot.send_message(chat_id, 'Сдача кодов выключена')


def send_live_locations(chat_id, bot, session, coords, duration):
    if not session.active:
        bot.send_message(chat_id, 'Нельзя отправлять live location при неактивной сессии')
        return
    if not session.locations and not coords:
        bot.send_message(chat_id, 'Нет координат для отправки')
        return
    if coords and 0 in session.live_location_message_ids.keys():
        bot.send_message(chat_id, 'Live_location основного бота уже отправлена')
        return
    if coords:
        send_live_locations_to_chat(bot, chat_id, session, coords=coords, duration=duration)
        return
    if session.live_location_message_ids:
        bot.send_message(chat_id, 'Live_location уровня уже отправлена(-ы)')
        return
    send_live_locations_to_chat(bot, chat_id, session)


def stop_live_locations(chat_id, bot, session, point):
    if not session.active:
        bot.send_message(chat_id, 'Нельзя остановить live location при неактивной сессии')
        return
    if not session.live_location_message_ids:
        bot.send_message(chat_id, 'Live location не отправлена')
        return
    close_live_locations(chat_id, bot, session, point=point)


def edit_live_locations(chat_id, bot, session, point, coords):
    if not session.active:
        bot.send_message(chat_id, 'Нельзя редактировать live location при неактивной сессии')
        return
    if not session.live_location_message_ids:
        bot.send_message(chat_id, 'Live location не отправлена')
        return
    if not point:
        if 0 in session.live_location_message_ids.keys():
            for coord in coords:
                latitude = re.findall(r'\d\d\.\d{4,7}', coord)[0]
                longitude = re.findall(r'\d\d\.\d{4,7}', coord)[1]
                bot.edit_message_live_location(latitude, longitude, chat_id, session.live_location_message_ids[0])
        else:
            bot.send_message(chat_id, 'Live location основного бота не отправлена. Чтобы изменить координаты точки, '
                                      'надо указать ее номер перед координатами '
                                      '(/edit_ll-пробел-номер-пробел-новые координаты)')
    else:
        if point in session.live_location_message_ids.keys():
            for coord in coords:
                latitude = re.findall(r'\d\d\.\d{4,7}', coord)[0]
                longitude = re.findall(r'\d\d\.\d{4,7}', coord)[1]
                telebot.TeleBot(DB.get_location_bot_token_by_number(point)).edit_message_live_location(
                    latitude, longitude, chat_id, session.live_location_message_ids[point])
        else:
            bot.send_message(chat_id, 'Проверьте номер точки - соответствующая live location не найдена)')


def add_custom_live_locations(chat_id, bot, session, points_dict, duration):
    if not session.active:
        bot.send_message(chat_id, 'Нельзя отправлять live location при неактивной сессии')
        return
    if session.live_location_message_ids:
        close_live_locations(chat_id, bot, session)
    send_live_locations_to_chat(bot, chat_id, session, custom_points=points_dict, duration=duration)
