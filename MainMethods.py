# -*- coding: utf-8 -*-
import json
import threading
import time
import re
import telebot
from CommonMethods import close_live_locations
from DBMethods import DB
from MainClasses import Task
from SessionMethods import compile_urls, login_to_en, send_task_to_chat, send_code_to_level, send_all_sectors_to_chat, \
    send_all_helps_to_chat, send_last_help_to_chat, send_all_bonuses_to_chat, send_task_images_to_chat, launch_session, \
    send_auth_messages_to_chat, send_unclosed_bonuses_to_chat, send_code_to_storm_level, send_task_to_chat_storm, \
    send_all_helps_to_chat_storm, send_last_help_to_chat_storm, send_all_sectors_to_chat_storm, \
    send_all_bonuses_to_chat_storm, send_unclosed_bonuses_to_chat_storm, send_auth_messages_to_chat_storm, \
    send_live_locations_to_chat


def start(task, bot):
    config = DB.get_config_by_chat_id(task.chat_id)
    sessions_ids = DB.get_sessions_ids()
    if task.chat_id not in sessions_ids and not config:
        result = DB.insert_session(task.chat_id)
        if result:
            bot.send_message(task.chat_id, '<b>Сессия создана</b>\n'
                                           'Чтобы начать использовать бота, необходимо задать конфигурацию игры:\n'
                                           '- ввести домен игры (/domain http://demo.en.cx)\n'
                                           '- ввести game id игры (/gameid 26991)\n'
                                           '- ввести логин игрока (/login abc)\n'
                                           '- ввести пароль игрока (/password abc)\n'
                                           '- активировать сессию (/start_session)\n'
                                           'Краткое описание доступно по команде /help',
                             disable_web_page_preview=True, parse_mode='HTML')
        else:
            bot.send_message(task.chat_id, 'Сессия не создана. Ошибка SQL')
    elif task.chat_id not in sessions_ids and config:
        result = DB.insert_session(task.chat_id, login=config['login'], password=config['password'],
                                   en_domain=config['endomain'], channel_name=config['channelname'])
        if result:
            bot.send_message(task.chat_id, '<b>Сессия создана</b>\n'
                                           'Для данного чата найдена конфигурация по умолчанию. Проверить: /config\n'
                                           'Чтобы начать использовать бота, необходимо:\n'
                                           '- ввести game id игры (/gameid 26991)\n'
                                           '- активировать сессию (/start_session)\n'
                                           '- сменить домен игры (/domain http://demo.en.cx)\n'
                                           '- сменить логин игрока (/login abc)\n'
                                           '- сменить пароль игрока (/password abc)\n'
                                           'Краткое описание доступно по команде /help',
                             disable_web_page_preview=True, parse_mode='HTML')
        else:
            bot.send_message(task.chat_id, 'Сессия не создана. Ошибка SQL')
    else:
        bot.send_message(task.chat_id, 'Для данного чата уже создана сессия\n'
                                       'Введите /config для проверки ее состояния')


def stop_session(task, bot):
    DB.update_stop_updater(task.session_id, 'True')
    DB.update_put_updater_task(task.session_id, 'False')
    DB.update_use_channel(task.session_id, 'False')
    DB.update_session_activity(task.session_id, 'False')
    bot.send_message(task.chat_id, 'Сессия остановлена')
    add_chat_ids_per_session = DB.get_add_chat_ids_for_main(task.session_id)
    for add_chat_id in add_chat_ids_per_session:
        DB.delete_add_chat_id(add_chat_id)


def config(task, bot):
    session_condition = 'Сессия активна' if task.session['active'] else 'Сессия не активна'
    channel_condition = '\r\nИмя канала задано' if task.session['channelname'] else '\r\nИмя канала не задано'
    reply = session_condition + '\r\nДомен: ' + task.session['endomain'] + '\r\nID игры: ' + task.session['gameid'] + \
            '\r\nЛогин: ' + task.session['login'] + channel_condition + '\r\nИнтервал слежения: ' + str(task.session['delay'])
    bot.send_message(task.chat_id, reply, disable_web_page_preview=True)


def set_login(task, bot):
    if not task.session.active:
        task.session.config['Login'] = task.new_login
        reply = 'Логин успешно задан' if task.session.config['Login'] == task.new_login else 'Логин не задан, повторите'
        bot.send_message(task.chat_id, reply)
    else:
        bot.send_message(task.chat_id, 'Нельзя менять логин при активной сессии')


def set_password(task, bot):
    if not task.session.active:
        task.session.config['Password'] = task.new_password
        reply = 'Пароль успешно задан' if task.session.config['Password'] == task.new_password else 'Пароль не задана, повторите'
        bot.send_message(task.chat_id, reply)
    else:
        bot.send_message(task.chat_id, 'Нельзя менять пароль при активной сессии')


def set_domain(task, bot):
    if not task.session.active:
        if 'http://' not in task.new_domain:
            new_domain = 'http://' + task.new_domain
            task.session.config['en_domain'] = new_domain
        reply = 'Домен успешно задан' if task.session.config['en_domain'] == new_domain \
            else 'Домен не задан, повторите (/domain http://demo.en.cx)'
        bot.send_message(task.chat_id, reply)
    else:
        bot.send_message(task.chat_id, 'Нельзя менять домен при активной сессии')


def set_game_id(task, bot):
    if not DB.get_session_activity(task.session_id):
        if DB.update_gameid(task.session_id, task.new_game_id):
            if DB.get_game_id(task.session_id) == task.new_game_id:
                DB.drop_session_vars(task.session_id)
                reply = 'Игра успешно задана. Переменные сброшены'
            else:
                reply = 'Игра не задана, повторите (/gameid 26991)'
        else:
            reply = 'game_id не задан, urls не сгенерированы. Ошибка SQL'
        bot.send_message(task.chat_id, reply)
    else:
        bot.send_message(task.chat_id, 'Нельзя менять игру при активной сессии')


def login(task, bot):
    session = DB.get_session(task.session_id)
    if session['endomain'] and session['gameid'] and session['login'] and session['password']:
        login_to_en(task.session_id, bot, task.chat_id)
    else:
        bot.send_message(task.chat_id, 'Не вся необходимая конфигурация задана. Проверьте домен, id игры, логин и пароль')


def start_session(task, bot):
    if not DB.get_session_activity(task.session_id):
        session = DB.get_session(task.session_id)
        if not session['cookie'] and session['endomain'] and session['gameid'] and session['login'] \
                and session['password']:
            compile_urls(session['sessionid'], task.chat_id, bot, session['gameid'], session['endomain'])
            login_to_en(task.session_id, bot, task.chat_id)
            launch_session(task.session_id, bot, task.chat_id)

        elif session['cookie'] and session['gameid'] and session['login'] and session['password']:
            compile_urls(session['sessionid'], task.chat_id, bot, session['gameid'], session['endomain'])
            launch_session(task.session_id, bot, task.chat_id)
        else:
            bot.send_message(task.chat_id, 'Не вся необходимая конфигурация задана или бот не залогинен. '
                                           'Проверьте домен, id игры, логин и пароль.')
    else:
        bot.send_message(task.chat_id, 'Сессия уже активирована. Если у вас проблемы со слежением - попробуйте '
                                       '/stop_updater, затем /start_updater')


def send_task(task, bot):
    if not task.session.active:
        bot.send_message(task.chat_id, 'Нельзя запросить задание при неактивной сессии')
        return
    if not task.session.storm_game:
        send_task_to_chat(bot, task.chat_id, task.session)
    else:
        if not task.storm_level_number:
            bot.send_message(task.chat_id, '\xE2\x9D\x97 Укажите уровень: <b>/task номер уровня</b>', parse_mode='HTML')
            return
        send_task_to_chat_storm(bot, task.chat_id, task.session, task.storm_level_number)


def send_task_images(task, bot):
    if task.session.active:
        send_task_images_to_chat(bot, task.chat_id, task.session)
    else:
        bot.send_message(task.chat_id, 'Нельзя запросить задание при неактивной сессии')


def send_all_sectors(task, bot):
    if not task.session.active:
        bot.send_message(task.chat_id, 'Нельзя запросить сектора при неактивной сессии')
        return
    if not task.session.storm_game:
        send_all_sectors_to_chat(bot, task.chat_id, task.session)
    else:
        if not task.storm_level_number:
            bot.send_message(task.chat_id, '\xE2\x9D\x97 Укажите уровень: <b>/sectors номер уровня</b>', parse_mode='HTML')
            return
        send_all_sectors_to_chat_storm(bot, task.chat_id, task.session, task.storm_level_number)


def send_all_helps(task, bot):
    if not task.session.active:
        bot.send_message(task.chat_id, 'Нельзя запросить подсказки при неактивной сессии')
        return
    if not task.session.storm_game:
        send_all_helps_to_chat(bot, task.chat_id, task.session)
    else:
        if not task.storm_level_number:
            bot.send_message(task.chat_id, '\xE2\x9D\x97 Укажите уровень: <b>/helps номер уровня</b>', parse_mode='HTML')
            return
        send_all_helps_to_chat_storm(bot, task.chat_id, task.session, task.storm_level_number)


def send_last_help(task, bot):
    if not task.session.active:
        bot.send_message(task.chat_id, 'Нельзя запросить подсказку при неактивной сессии')
        return
    if not task.session.storm_game:
            send_last_help_to_chat(bot, task.chat_id, task.session)
    else:
        if not task.storm_level_number:
            bot.send_message(task.chat_id, '\xE2\x9D\x97 Укажите уровень: <b>/last_help номер уровня</b>', parse_mode='HTML')
            return
        send_last_help_to_chat_storm(bot, task.chat_id, task.session, task.storm_level_number)


def send_all_bonuses(task, bot):
    if not task.session.active:
        bot.send_message(task.chat_id, 'Нельзя запросить бонусы при неактивной сессии')
        return
    if not task.session.storm_game:
        send_all_bonuses_to_chat(bot, task.chat_id, task.session)
    else:
        if not task.storm_level_number:
            bot.send_message(task.chat_id, '\xE2\x9D\x97 Укажите уровень: <b>/bonuses номер уровня</b>', parse_mode='HTML')
            return
        send_all_bonuses_to_chat_storm(bot, task.chat_id, task.session, task.storm_level_number)


def send_unclosed_bonuses(task, bot):
    if not task.session.active:
        bot.send_message(task.chat_id, 'Нельзя запросить не закрытые бонусы при неактивной сессии')
        return
    if not task.session.storm_game:
        send_unclosed_bonuses_to_chat(bot, task.chat_id, task.session)
    else:
        if not task.storm_level_number:
            bot.send_message(task.chat_id, '\xE2\x9D\x97 Укажите уровень: <b>/unclosed_bonuses номер уровня</b>', parse_mode='HTML')
            return
        send_unclosed_bonuses_to_chat_storm(bot, task.chat_id, task.session, task.storm_level_number)


def send_auth_messages(task, bot):
    if not task.session.active:
        bot.send_message(task.chat_id, 'Нельзя запросить сообщения от авторов при неактивной сессии')
        return
    if not task.session.storm_game:
        send_auth_messages_to_chat(bot, task.chat_id, task.session)
    else:
        if not task.storm_level_number:
            bot.send_message(task.chat_id, '\xE2\x9D\x97 Укажите уровень: <b>/messages номер уровня</b>', parse_mode='HTML')
            return
        send_auth_messages_to_chat_storm(bot, task.chat_id, task.session, task.storm_level_number)


def start_updater(task, bot):
    session = task.main_vars.sessions_dict[task.chat_id]
    if session.active and task.chat_id not in task.main_vars.updater_schedulers_dict.keys():
        session.update_stop_updater = False
        session.put_updater_task = True
        bot.send_message(task.chat_id, 'Слежение запущено')
        name = 'updater_%s' % task.chat_id
        task.main_vars.updater_schedulers_dict[task.chat_id] = threading.Thread(name=name, target=updater_scheduler,
                                                                                args=(task.chat_id, bot, task.main_vars))
        task.main_vars.updater_schedulers_dict[task.chat_id].start()
    else:
        bot.send_message(task.chat_id, 'Нельзя запустить слежение повторно или при неактивной сессии')


def updater_scheduler(chat_id, bot, main_vars):
    session = main_vars.sessions_dict[chat_id]
    while not session.update_stop_updater:
        if session.put_updater_task:
            time.sleep(session.delay)
            updater_task = Task(chat_id, 'updater', session=session, updaters_dict=main_vars.updaters_dict)
            main_vars.task_queue.append(updater_task)
            session.put_updater_task = False
    else:
        bot.send_message(chat_id, 'Слежение остановлено')
        if chat_id in main_vars.updater_schedulers_dict.keys():
            del main_vars.updater_schedulers_dict[chat_id]
        return


def set_updater_delay(task, bot):
    task.session.delay = task.new_delay
    reply = 'Задержка успешно выставлена' if task.session.delay == task.new_delay else 'Задержка не обновлена, повторите'
    bot.send_message(task.chat_id, reply)


def stop_updater(task, bot):
    if task.session.active:
        task.session.update_stop_updater = True
        task.session.put_updater_task = False


def set_channel_name(task, bot):
    if "@" not in task.new_channel_name:
        new_channel_name = "@" + task.new_channel_name
    task.session.channel_name = new_channel_name
    reply = 'Канал успешно задан' if task.session.channel_name == new_channel_name else 'Канал не задан, повторите'
    bot.send_message(task.chat_id, reply)


def start_channel(task, bot):
    task.session.use_channel = True
    bot.send_message(task.chat_id, 'Постинг в канал разрешен')


def stop_channel(task, bot):
    task.session.use_channel = False
    bot.send_message(task.chat_id, 'Постинг в канал запрещен')


def send_code_main(task, bot):
    if not task.session.active:
        bot.send_message(task.chat_id, 'Нельзя сдавать коды при неактивной сессии')
        return
    if not task.session.send_codes:
        bot.send_message(task.chat_id, 'Сдача кодов выключена. Для включения введите команду /codes_on')
        return
    if not task.session.storm_game:
        send_code_to_level(task.code, bot, task.chat_id, task.message_id, task.session)
    else:
        try:
            level_number = re.findall(r'([\d]+)\s*!', task.code)[0]
            code = re.findall(r'!\s*(.+)', task.code)[0]
        except Exception:
            bot.send_message(task.chat_id, '\xE2\x9D\x97 Укажите уровень: <b>!номер уровня!код</b>',
                             reply_to_message_id=task.message_id, parse_mode='HTML')
            return
        send_code_to_storm_level(code, level_number, bot, task.chat_id, task.message_id, task.session)


def send_code_bonus(task, bot):
    if not task.session.active:
        bot.send_message(task.chat_id, 'Нельзя сдавать коды при неактивной сессии')
        return
    if not task.session.send_codes:
        bot.send_message(task.chat_id, 'Сдача кодов выключена. Для включения введите команду /codes_on')
        return
    if not task.session.storm_game:
        send_code_to_level(task.code, bot, task.chat_id, task.message_id, task.session, bonus_only=True)
    else:
        try:
            level_number = re.findall(r'([\d]+)\s*\?', task.code)[0]
            code = re.findall(r'\?\s*(.+)', task.code)[0]
        except Exception:
            bot.send_message(task.chat_id, '\xE2\x9D\x97 Укажите уровень: <b>?номер уровня?код</b>',
                             reply_to_message_id=task.message_id, parse_mode='HTML')
            return
        send_code_to_storm_level(code, level_number, bot, task.chat_id, task.message_id, task.session, bonus_only=True)


def send_coords(task, bot):
    for coord in task.coords:
        latitude = re.findall(r'\d\d\.\d{4,7}', coord)[0]
        longitude = re.findall(r'\d\d\.\d{4,7}', coord)[1]
        bot.send_venue(task.chat_id, latitude, longitude, coord, '')


def join(task, bot):
    DB.insert_add_chat_id(task.chat_id, task.add_chat_id)
    bot.send_message(task.chat_id, 'Теперь вы можете работать с ботом через личный чат',
                     reply_to_message_id=task.message_id)


def reset_join(task, bot):
    # main_chat_id = DB.get_main_chat_id_via_add(add_chat_id)
    DB.delete_add_chat_id(task.add_chat_id)
    bot.send_message(task.chat_id, 'Взаимодействие с ботом через личный чат сброшено',
                     reply_to_message_id=task.message_id)


def enable_codes(task, bot):
    task.session.send_codes = True
    bot.send_message(task.chat_id, 'Сдача кодов включена')


def disable_codes(task, bot):
    task.session.send_codes = False
    bot.send_message(task.chat_id, 'Сдача кодов выключена')


def send_live_locations(task, bot):
    if not task.session.active:
        bot.send_message(task.chat_id, 'Нельзя отправлять live location при неактивной сессии')
        return
    if not task.session.locations and not task.coords:
        bot.send_message(task.chat_id, 'Нет координат для отправки')
        return
    if task.coords and 0 in task.session.live_location_message_ids.keys():
        bot.send_message(task.chat_id, 'Live_location основного бота уже отправлена')
        return
    if task.coords:
        send_live_locations_to_chat(bot, task.chat_id, task.session, coords=task.coords, duration=task.duration)
        return
    if task.session.live_location_message_ids:
        bot.send_message(task.chat_id, 'Live_location уровня уже отправлена(-ы)')
        return
    send_live_locations_to_chat(bot, task.chat_id, task.session)


def stop_live_locations(task, bot):
    if not task.session.active:
        bot.send_message(task.chat_id, 'Нельзя остановить live location при неактивной сессии')
        return
    if not task.session.live_location_message_ids:
        bot.send_message(task.chat_id, 'Live location не отправлена')
        return
    close_live_locations(task.chat_id, bot, task.session, point=task.point)


def edit_live_locations(task, bot):
    if not task.session.active:
        bot.send_message(task.chat_id, 'Нельзя редактировать live location при неактивной сессии')
        return
    if not task.session.live_location_message_ids:
        bot.send_message(task.chat_id, 'Live location не отправлена')
        return
    if not task.point:
        if 0 in task.session.live_location_message_ids.keys():
            for coord in task.coords:
                latitude = re.findall(r'\d\d\.\d{4,7}', coord)[0]
                longitude = re.findall(r'\d\d\.\d{4,7}', coord)[1]
                bot.edit_message_live_location(latitude, longitude, task.chat_id, task.session.live_location_message_ids[0])
        else:
            bot.send_message(task.chat_id, 'Live location основного бота не отправлена. Чтобы изменить координаты точки, '
                                      'надо указать ее номер перед координатами '
                                      '(/edit_ll-пробел-номер-пробел-новые координаты)')
    else:
        if task.point in task.session.live_location_message_ids.keys():
            for coord in task.coords:
                latitude = re.findall(r'\d\d\.\d{4,7}', coord)[0]
                longitude = re.findall(r'\d\d\.\d{4,7}', coord)[1]
                telebot.TeleBot(DB.get_location_bot_token_by_number(task.point)).edit_message_live_location(
                    latitude, longitude, task.chat_id, task.session.live_location_message_ids[task.point])
        else:
            bot.send_message(task.chat_id, 'Проверьте номер точки - соответствующая live location не найдена)')


def add_custom_live_locations(task, bot):
    if not task.session.active:
        bot.send_message(task.chat_id, 'Нельзя отправлять live location при неактивной сессии')
        return
    if task.session.live_location_message_ids:
        close_live_locations(task.chat_id, bot, task.session)
    send_live_locations_to_chat(bot, task.chat_id, task.session, custom_points=task.points_dict, duration=task.duration)
