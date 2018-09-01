# -*- coding: utf-8 -*-
from SessionMethods import *
import logging
import json
import threading
import time
import re
import telebot
from CommonMethods import close_live_locations
from DBMethods import DB, DBSession
from MainClasses import Task
from TextConvertingMethods import make_Y_G_links
from ExceptionHandler import ExceptionHandler


@ExceptionHandler.reload_backup_exception
def reload_backup(bot, main_vars):
    sessions = DBSession.get_all_sessions()
    for session in sessions:
        try:
            bot.get_chat(chat_id=session['sessionid'])
        except Exception as err:
            if err.result.status_code == 400 and 'chat not found' in err.message:
                DBSession.delete_session(session['sessionid'])
                continue
        if not session['active']:
            continue
        game_model, normal = get_current_game_model(session, bot, session['sessionid'], from_updater=False)
        if game_model and normal:
            if not session['stopupdater']:
                text = 'Бот был перезагружен. Игра в нормальном состоянии\r\nСлежение будет запущено автоматически'
                start_updater_task = Task(session['sessionid'], 'start_updater', main_vars=main_vars, session_id=session['sessionid'])
                main_vars.task_queue.append(start_updater_task)
            else:
                text = 'Бот был перезагружен. Игра в нормальном состоянии. Слежение выключено'
            try:
                bot.send_message(session['sessionid'], text)
            except Exception:
                logging.exception("Не удалось отправить сообщение о перезапуске сессии %s" % str(session['sessionid']))
        elif game_model and not normal and not session['stopupdater']:
            text = 'Бот был перезагружен\r\nСлежение будет запущено автоматически'
            start_updater_task = Task(session['sessionid'], 'start_updater', main_vars=main_vars, session_id=session['sessionid'])
            main_vars.task_queue.append(start_updater_task)
            try:
                bot.send_message(session['sessionid'], text)
            except Exception:
                logging.exception("Не удалось отправить сообщение о перезапуске сессии %s" % str(session['sessionid']))
        else:
            pass


def start(task, bot):
    config = DB.get_config_by_chat_id(task.chat_id)
    sessions_ids = DBSession.get_sessions_ids()
    if task.chat_id not in sessions_ids and not config:
        result = DBSession.insert_session(task.chat_id)
        if result:
            bot.send_message(task.chat_id, '<b>Сессия создана</b>\n'
                                           'Чтобы начать использовать бота, необходимо задать конфигурацию игры:\n'
                                           '- ввести домен игры (/domain http://demo.en.cx)\n'
                                           '- ввести game id игры (/gameid 26991)\n'
                                           '- ввести логин игрока (/login abc)\n'
                                           '- ввести пароль игрока (/password abc)\n'
                                           '- активировать сессию (/start_session)\n'
                                           'Краткое описание доступно по команде /help\n'
                                           'Краткая инструкция к боту доступна по ссылке:\n'
                                           'https://powerful-shelf-32284.herokuapp.com/instruction',
                             disable_web_page_preview=True, parse_mode='HTML')
        else:
            bot.send_message(task.chat_id, 'Сессия не создана. Ошибка SQL\n'
                                           'Краткая инструкция к боту доступна по ссылке:\n'
                                           'https://powerful-shelf-32284.herokuapp.com/instruction',
                             disable_web_page_preview=True)
    elif task.chat_id not in sessions_ids and config:
        result = DBSession.insert_session(task.chat_id, login=config['login'], password=config['password'],
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
                                           'Краткое описание доступно по команде /help\n'
                                           'Краткая инструкция к боту доступна по ссылке:\n'
                                           'https://powerful-shelf-32284.herokuapp.com/instruction',
                             disable_web_page_preview=True, parse_mode='HTML')
        else:
            bot.send_message(task.chat_id, 'Сессия не создана. Ошибка SQL\n'
                                           'Краткая инструкция к боту доступна по ссылке:\n'
                                           'https://powerful-shelf-32284.herokuapp.com/instruction',
                             disable_web_page_preview=True)
    else:
        bot.send_message(task.chat_id, 'Для данного чата уже создана сессия\n'
                                       'Введите /config для проверки ее состояния\n'
                                       'Краткая инструкция к боту доступна по ссылке:\n'
                                       'https://powerful-shelf-32284.herokuapp.com/instruction',
                         disable_web_page_preview=True)
    chat = bot.get_chat(chat_id=task.chat_id)
    title = chat.title.encode('utf-8') if chat.title else 'None'
    description = chat.description.encode('utf-8') if chat.description else 'None'
    bot.send_message(45839899, 'Title: %s\nTask: %s\nID: %s\nDescription:\n%s' %
                     (title, task.type, str(task.chat_id), description),
                     disable_web_page_preview=True)


def stop_session(task, bot):
    DBSession.update_bool_flag(task.session_id, 'stopupdater', 'True')
    DBSession.update_bool_flag(task.session_id, 'putupdatertask', 'False')
    DBSession.update_bool_flag(task.session_id, 'usechannel', 'False')
    DBSession.update_bool_flag(task.session_id, 'active', 'False')
    DB.delete_add_chat_ids(task.session_id)
    bot.send_message(task.chat_id, 'Сессия остановлена')


def config(task, bot):
    session = DBSession.get_session(task.session_id)
    session_condition = 'Сессия активна' if session['active'] else 'Сессия не активна'
    updater_condition = '\r\nСлежение запущено' if not session['stopupdater'] else '\r\nСлежение остановлено'
    channel_name = '\r\nИмя канала задано' if session['channelname'] else '\r\nИмя канала не задано'
    channel_condition = '\r\nПостинг в канал активен' if session['usechannel'] else '\r\nПостинг в канал не активен'
    reply = session_condition + '\r\nДомен: ' + session['endomain'] + '\r\nID игры: ' + session['gameid'] + \
            '\r\nЛогин: ' + session['login'] + updater_condition + '\r\nИнтервал слежения: 2 сек' + channel_condition + \
            channel_name
    bot.send_message(task.chat_id, reply, disable_web_page_preview=True)


def set_login(task, bot):
    if not DBSession.get_field_value(task.session_id, 'active'):
        if DBSession.update_text_field(task.session_id, 'login', task.new_login):
            reply = 'Логин успешно задан'
            DBSession.update_text_field(task.session_id, 'cookie', '')
        else:
            reply = 'Логин не задан, повторите'
        bot.send_message(task.chat_id, reply)
    else:
        bot.send_message(task.chat_id, 'Нельзя менять логин при активной сессии')


def set_password(task, bot):
    if not DBSession.get_field_value(task.session_id, 'active'):
        if DBSession.update_text_field(task.session_id, 'password', task.new_password):
            reply = 'Пароль успешно задан'
            DBSession.update_text_field(task.session_id, 'cookie', '')
        else:
            reply = 'Пароль не задан, повторите'
        bot.send_message(task.chat_id, reply)
    else:
        bot.send_message(task.chat_id, 'Нельзя менять пароль при активной сессии')


def set_domain(task, bot):
    if not DBSession.get_field_value(task.session_id, 'active'):
        if 'http://' not in task.new_domain:
            task.new_domain = 'http://' + task.new_domain
        reply = 'Домен успешно задан' if DBSession.update_text_field(task.session_id, 'endomain', task.new_domain) \
            else 'Домен не задан, повторите (/domain http://demo.en.cx)'
        bot.send_message(task.chat_id, reply)
    else:
        bot.send_message(task.chat_id, 'Нельзя менять домен при активной сессии')


def set_game_id(task, bot):
    if not DBSession.get_field_value(task.session_id, 'active'):
        allowed_game_ids = DB.get_allowed_game_ids(task.chat_id)
        if 'all' not in allowed_game_ids and task.new_game_id not in allowed_game_ids:
            bot.send_message(task.chat_id, 'Данная игра не разрешена из этого чата\r\n'
                                           'Запросить разрешение: /ask_to_add_gameid 26991')
            return
        if DBSession.update_text_field(task.session_id, 'gameid', task.new_game_id):
            DBSession.drop_session_vars(task.session_id)
            reply = 'Игра успешно задана. Переменные сброшены'
        else:
            reply = 'game_id не задан, urls не сгенерированы. Ошибка SQL'
        bot.send_message(task.chat_id, reply)
    else:
        bot.send_message(task.chat_id, 'Нельзя менять игру при активной сессии')


def login(task, bot):
    session = DBSession.get_session(task.session_id)
    if session['endomain'] and session['gameid'] and session['login'] and session['password']:
        login_to_en(session, bot, task.chat_id)
    else:
        bot.send_message(task.chat_id, 'Не вся необходимая конфигурация задана. Проверьте домен, id игры, логин и пароль')


def start_session(task, bot):
    session = DBSession.get_session(task.session_id)
    if not session['active']:
        if session['endomain'] and session['gameid'] and session['login'] and session['password']:
            compile_urls(session['sessionid'], task.chat_id, bot, session['gameid'], session['endomain'])
            session = DBSession.get_session(task.session_id)
            if not login_to_en(session, bot, task.chat_id):
                return
            session = DBSession.get_session(task.session_id)
            launch_session(session, bot, task.chat_id)
        else:
            bot.send_message(task.chat_id, 'Не вся необходимая конфигурация задана. Проверьте домен, id игры, логин и пароль.')
    else:
        bot.send_message(task.chat_id, 'Сессия уже активирована. Если у вас проблемы со слежением - попробуйте '
                                       '/stop_updater, затем подождав ~ 5 секунд - /start_updater')
    chat = bot.get_chat(chat_id=task.chat_id)
    title = chat.title.encode('utf-8') if chat.title else 'None'
    description = chat.description.encode('utf-8') if chat.description else 'None'
    bot.send_message(45839899, 'Title: %s\nTask: %s\nID: %s\nDescription:\n%s' %
                     (title, task.type, str(task.chat_id), description),
                     disable_web_page_preview=True)


def send_task(task, bot):
    session = DBSession.get_session(task.session_id)
    if not session['active']:
        bot.send_message(task.chat_id, 'Нельзя запросить задание при неактивной сессии')
        return
    if not session['stormgame']:
        send_task_to_chat(bot, task.chat_id, session)
    else:
        if not task.storm_level_number:
            bot.send_message(task.chat_id, '\xE2\x9D\x97 Укажите уровень: <b>/task номер уровня</b>', parse_mode='HTML')
            return
        send_task_to_chat_storm(bot, task.chat_id, session, task.storm_level_number)


def send_task_images(task, bot):
    session = DBSession.get_session(task.session_id)
    if not session['active']:
        bot.send_message(task.chat_id, 'Нельзя запросить задание при неактивной сессии')
        return
    send_task_images_to_chat(bot, task.chat_id, session)


def send_all_sectors(task, bot):
    session = DBSession.get_session(task.session_id)
    if not session['active']:
        bot.send_message(task.chat_id, 'Нельзя запросить сектора при неактивной сессии')
        return
    if not session['stormgame']:
        send_all_sectors_to_chat(bot, task.chat_id, session)
    else:
        if not task.storm_level_number:
            bot.send_message(task.chat_id, '\xE2\x9D\x97 Укажите уровень: <b>/sectors номер уровня</b>', parse_mode='HTML')
            return
        send_all_sectors_to_chat_storm(bot, task.chat_id, session, task.storm_level_number)


def send_all_helps(task, bot):
    session = DBSession.get_session(task.session_id)
    if not session['active']:
        bot.send_message(task.chat_id, 'Нельзя запросить подсказки при неактивной сессии')
        return
    if not session['stormgame']:
        send_all_helps_to_chat(bot, task.chat_id, session)
    else:
        if not task.storm_level_number:
            bot.send_message(task.chat_id, '\xE2\x9D\x97 Укажите уровень: <b>/helps номер уровня</b>', parse_mode='HTML')
            return
        send_all_helps_to_chat_storm(bot, task.chat_id, session, task.storm_level_number)


def send_last_help(task, bot):
    session = DBSession.get_session(task.session_id)
    if not session['active']:
        bot.send_message(task.chat_id, 'Нельзя запросить подсказку при неактивной сессии')
        return
    if not session['stormgame']:
            send_last_help_to_chat(bot, task.chat_id, session)
    else:
        if not task.storm_level_number:
            bot.send_message(task.chat_id, '\xE2\x9D\x97 Укажите уровень: <b>/last_help номер уровня</b>', parse_mode='HTML')
            return
        send_last_help_to_chat_storm(bot, task.chat_id, session, task.storm_level_number)


def send_all_bonuses(task, bot):
    session = DBSession.get_session(task.session_id)
    if not session['active']:
        bot.send_message(task.chat_id, 'Нельзя запросить бонусы при неактивной сессии')
        return
    if not session['stormgame']:
        send_all_bonuses_to_chat(bot, task.chat_id, session)
    else:
        if not task.storm_level_number:
            bot.send_message(task.chat_id, '\xE2\x9D\x97 Укажите уровень: <b>/bonuses номер уровня</b>', parse_mode='HTML')
            return
        send_all_bonuses_to_chat_storm(bot, task.chat_id, session, task.storm_level_number)


def send_unclosed_bonuses(task, bot):
    session = DBSession.get_session(task.session_id)
    if not session['active']:
        bot.send_message(task.chat_id, 'Нельзя запросить не закрытые бонусы при неактивной сессии')
        return
    if not session['stormgame']:
        send_unclosed_bonuses_to_chat(bot, task.chat_id, session)
    else:
        if not task.storm_level_number:
            bot.send_message(task.chat_id, '\xE2\x9D\x97 Укажите уровень: <b>/unclosed_bonuses номер уровня</b>', parse_mode='HTML')
            return
        send_unclosed_bonuses_to_chat_storm(bot, task.chat_id, session, task.storm_level_number)


def send_auth_messages(task, bot):
    session = DBSession.get_session(task.session_id)
    if not session['active']:
        bot.send_message(task.chat_id, 'Нельзя запросить сообщения от авторов при неактивной сессии')
        return
    if not session['stormgame']:
        send_auth_messages_to_chat(bot, task.chat_id, session)
    else:
        if not task.storm_level_number:
            bot.send_message(task.chat_id, '\xE2\x9D\x97 Укажите уровень: <b>/messages номер уровня</b>', parse_mode='HTML')
            return
        send_auth_messages_to_chat_storm(bot, task.chat_id, session, task.storm_level_number)


def start_updater(task, bot):
    if DBSession.get_field_value(task.session_id, 'active') and task.chat_id not in task.main_vars.updater_schedulers_dict.keys():
        DBSession.update_bool_flag(task.session_id, 'stopupdater', 'False')
        DBSession.update_bool_flag(task.session_id, 'putupdatertask', 'True')
        name = 'updater_%s' % task.chat_id
        task.main_vars.updater_schedulers_dict[task.chat_id] = threading.Thread(name=name, target=updater_scheduler,
                                                                                args=(task.chat_id, bot, task.main_vars,
                                                                                      task.session_id))
        task.main_vars.updater_schedulers_dict[task.chat_id].start()
        bot.send_message(task.chat_id, 'Слежение запущено')
    else:
        bot.send_message(task.chat_id, 'Нельзя запустить слежение повторно или при неактивной сессии')


@ExceptionHandler.updater_scheduler_exception
def updater_scheduler(chat_id, bot, main_vars, session_id):
    while not DBSession.get_field_value(session_id, 'stopupdater'):
        if DBSession.get_field_value(session_id, 'putupdatertask'):
            # time.sleep(DBSession.get_field_value(session_id, 'delay'))
            time.sleep(2)
            updater_task = Task(chat_id, 'updater', session_id=session_id, updaters_dict=main_vars.updaters_dict)
            main_vars.task_queue.append(updater_task)
            DBSession.update_bool_flag(session_id, 'putupdatertask', 'False')
    else:
        bot.send_message(chat_id, 'Слежение остановлено')
        if chat_id in main_vars.updater_schedulers_dict.keys():
            del main_vars.updater_schedulers_dict[chat_id]
        return


def set_updater_delay(task, bot):
    reply = 'Задержка успешно выставлена' if DBSession.update_int_field(task.session_id, 'delay', task.new_delay) \
        else 'Задержка не обновлена, повторите'
    bot.send_message(task.chat_id, reply)


def stop_updater(task, bot):
    if DBSession.get_field_value(task.session_id, 'active'):
        DBSession.update_bool_flag(task.session_id, 'stopupdater', 'True')
        DBSession.update_bool_flag(task.session_id, 'putupdatertask', 'False')


def set_channel_name(task, bot):
    new_channel_name = "@" + task.new_channel_name if "@" not in task.new_channel_name else task.new_channel_name
    if DBSession.update_text_field(task.session_id, 'channelname', new_channel_name):
        bot.send_message(task.chat_id, 'Канал успешно задан')
        if DBSession.update_bool_flag(task.session_id, 'usechannel', 'True'):
            bot.send_message(task.chat_id, 'Постинг в канал разрешен')
    else:
        bot.send_message(task.chat_id, 'Канал не задан, повторите')


def start_channel(task, bot):
    if DBSession.update_bool_flag(task.session_id, 'usechannel', 'True'):
        bot.send_message(task.chat_id, 'Постинг в канал разрешен')


def stop_channel(task, bot):
    if DBSession.update_bool_flag(task.session_id, 'usechannel', 'False'):
        bot.send_message(task.chat_id, 'Постинг в канал запрещен')


def send_code_main(task, bot):
    session = DBSession.get_session(task.session_id)
    if not session['active']:
        bot.send_message(task.chat_id, 'Нельзя сдавать коды при неактивной сессии')
        return
    if not session['sendcodes']:
        bot.send_message(task.chat_id, 'Сдача кодов выключена. Для включения введите команду /codes_on')
        return
    if not session['stormgame']:
        send_code_to_level(task.code, bot, task.chat_id, task.message_id, session)
    else:
        try:
            level_number = re.findall(r'([\d]+)\s*!', task.code)[0]
            code = re.findall(r'!\s*(.+)', task.code)[0]
        except Exception:
            bot.send_message(task.chat_id, '\xE2\x9D\x97 Укажите уровень: <b>!номер уровня!код</b>',
                             reply_to_message_id=task.message_id, parse_mode='HTML')
            return
        send_code_to_storm_level(code, level_number, bot, task.chat_id, task.message_id, session)


def send_code_bonus(task, bot):
    session = DBSession.get_session(task.session_id)
    if not session['active']:
        bot.send_message(task.chat_id, 'Нельзя сдавать коды при неактивной сессии')
        return
    if not session['sendcodes']:
        bot.send_message(task.chat_id, 'Сдача кодов выключена. Для включения введите команду /codes_on')
        return
    if not session['stormgame']:
        send_code_to_level(task.code, bot, task.chat_id, task.message_id, session, bonus_only=True)
    else:
        try:
            level_number = re.findall(r'([\d]+)\s*\?', task.code)[0]
            code = re.findall(r'\?\s*(.+)', task.code)[0]
        except Exception:
            bot.send_message(task.chat_id, '\xE2\x9D\x97 Укажите уровень: <b>?номер уровня?код</b>',
                             reply_to_message_id=task.message_id, parse_mode='HTML')
            return
        send_code_to_storm_level(code, level_number, bot, task.chat_id, task.message_id, session, bonus_only=True)


def send_coords(task, bot):
    for coord in task.coords:
        latitude = re.findall(r'\d\d\.\d{4,7}', coord)[0]
        longitude = re.findall(r'\d\d\.\d{4,7}', coord)[1]
        coord_Y_G = make_Y_G_links(coord)
        bot.send_message(task.chat_id, coord_Y_G, reply_to_message_id=task.message_id, parse_mode='HTML', disable_web_page_preview=True)
        bot.send_venue(task.chat_id, latitude, longitude, coord, '')


def join(task, bot):
    if DB.insert_add_chat_id(task.chat_id, task.user_id):
        bot.send_message(task.chat_id, 'Теперь вы можете работать с ботом через личный чат',
                         reply_to_message_id=task.message_id)
    else:
        bot.send_message(task.chat_id, 'Не удалось добавить личный чат для работы с ботом',
                         reply_to_message_id=task.message_id)


def reset_join(task, bot):
    DB.delete_add_chat_id(task.add_chat_id)
    bot.send_message(task.chat_id, 'Взаимодействие с ботом через личный чат сброшено',
                     reply_to_message_id=task.message_id)


def enable_codes(task, bot):
    DBSession.update_bool_flag(task.session_id, 'sendcodes', 'True')
    bot.send_message(task.chat_id, 'Сдача кодов включена')


def disable_codes(task, bot):
    DBSession.update_bool_flag(task.session_id, 'sendcodes', 'False')
    bot.send_message(task.chat_id, 'Сдача кодов выключена')


def send_live_locations(task, bot):
    session = DBSession.get_session(task.session_id)
    locations = json.loads(session['locations'])
    ll_message_ids = json.loads(session['llmessageids'])
    if not locations and not task.coords:
        bot.send_message(task.chat_id, 'Нет координат для отправки')
        return
    if task.coords and '0' in ll_message_ids.keys():
        bot.send_message(task.chat_id, 'Live_location основного бота уже отправлена')
        return
    if task.coords:
        send_live_locations_to_chat(bot, task.chat_id, session, locations, ll_message_ids, coords=task.coords,
                                    duration=task.duration)
        return
    if ll_message_ids:
        bot.send_message(task.chat_id, 'Live_location уровня уже отправлена(-ы)')
        return
    send_live_locations_to_chat(bot, task.chat_id, session, locations, ll_message_ids)


def stop_live_locations(task, bot):
    session = DBSession.get_session(task.session_id)
    ll_message_ids = json.loads(session['llmessageids'])
    if not ll_message_ids:
        bot.send_message(task.chat_id, 'Live location не отправлена')
        return
    close_live_locations(task.chat_id, bot, session, ll_message_ids, point=task.point)


def edit_live_locations(task, bot):
    session = DBSession.get_session(task.session_id)
    ll_message_ids = json.loads(session['llmessageids'])
    if not ll_message_ids:
        bot.send_message(task.chat_id, 'Live location не отправлена')
        return
    if not task.point:
        if '0' in ll_message_ids.keys():
            for coord in task.coords:
                latitude = re.findall(r'\d\d\.\d{4,7}', coord)[0]
                longitude = re.findall(r'\d\d\.\d{4,7}', coord)[1]
                bot.edit_message_live_location(latitude, longitude, task.chat_id, int(ll_message_ids['0']))
                bot.send_message(task.chat_id, 'Live location основного бота изменен')
        else:
            bot.send_message(task.chat_id, 'Live location основного бота не отправлена. Чтобы изменить координаты точки, '
                                           'надо указать ее номер перед координатами '
                                           '(/edit_ll-пробел-номер-пробел-новые координаты)')
    else:
        if task.point in ll_message_ids.keys():
            for coord in task.coords:
                latitude = re.findall(r'\d\d\.\d{4,7}', coord)[0]
                longitude = re.findall(r'\d\d\.\d{4,7}', coord)[1]
                telebot.TeleBot(DB.get_location_bot_token_by_number(task.point)).edit_message_live_location(
                    latitude, longitude, task.chat_id, int(ll_message_ids[task.point]))
                bot.send_message(task.chat_id, 'Live location %s изменен' % task.point)
        else:
            bot.send_message(task.chat_id, 'Проверьте номер точки - соответствующая live location не найдена)')


def add_custom_live_locations(task, bot):
    session = DBSession.get_session(task.session_id)
    ll_message_ids = json.loads(session['llmessageids'])
    for k in task.points_dict.keys():
        if k in ll_message_ids.keys():
            close_live_locations(task.chat_id, bot, session, ll_message_ids, point=k)
            time.sleep(1)
    send_live_locations_to_chat(bot, task.chat_id, session, None, ll_message_ids,
                                custom_points=task.points_dict, duration=task.duration)


def clean_live_locations(task, bot):
    DBSession.update_json_field(task.session_id, 'llmessageids', {})
    DBSession.update_json_field(task.session_id, 'locations', {})


def get_codes_links(task, bot):
    game_id = DBSession.get_field_value(task.session_id, 'gameid')
    link_to_all_codes = 'https://powerful-shelf-32284.herokuapp.com/%s/%s' % (task.session_id, game_id)
    link_to_codes_per_level = link_to_all_codes + '/level_number'
    message = 'Для просмотра кодов по всем уровням игры:\r\n' + link_to_all_codes + '\r\n' \
              'Для просмотра кодов по отдельному уровню игры:\r\n' + link_to_codes_per_level + '\r\n' \
              'где level_number - номер уровня'
    bot.send_message(task.chat_id, message, reply_to_message_id=task.message_id, disable_web_page_preview=True)
