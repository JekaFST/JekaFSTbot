# -*- coding: utf-8 -*-
import re
import os
import logging
import requests
import json
import telebot
import simplekml
from bs4 import BeautifulSoup
from CommonMethods import send_help, send_time_to_help, send_bonus_info, send_bonus_award_answer, send_task, send_adm_message, \
    channel_error_handling
from Const import game_wrong_statuses, urls
from DBMethods import DB, DBSession, DBLevels, DBSectors
from TextConvertingMethods import make_Y_G_links


def compile_urls(session_id, chat_id, bot, game_id, en_domain):
    session_urls = dict()
    session_urls['game_url'] = str(en_domain + urls['game_url_ending'] + game_id)
    session_urls['login_url'] = str(en_domain + urls['login_url_ending'])
    if DBSession.update_session_urls(session_id, session_urls):
        return True
    else:
        bot.send_message(chat_id, 'Ошибка SQL при создании URL игры')
        return False


def login_to_en(session, bot, chat_id):
    got_cookies = upd_session_cookie(session, bot, chat_id)
    if got_cookies:
        bot.send_message(chat_id, 'Бот успешно залогинился')
        return True
    else:
        return False


def launch_session(session, bot, chat_id):
    if 'stoken' not in session['cookie']:
        bot.send_message(chat_id, 'Бот не залогинен, попробуйте повторно задать логин, пароль и перезапустить сессию')
        return
    game_loaded, normal, storm = initiate_session_vars(session, bot, chat_id)
    if not game_loaded:
        reply = 'Сессия активирована, не удалось загрузить игру\r\n' \
                'для запуска слежения введите /start_updater\r\n' \
                'для остановки слежения введите /stop_updater\r\n' \
                'для использования репостинга в канал задайте имя канала /set_channel_name\r\n' \
                'и запустите репстинг в канал /start_channel\r\n' \
                'если имя канала задано по умолчания, постинг уже активирован\r\n' \
                'для остановки репостинга в канал введите /stop_channel'
    elif normal and not storm:
        reply = 'Сессия активирована, линейная игра в активном состоянии\r\n' \
                'для запуска слежения введите /start_updater\r\n' \
                'для остановки слежения введите /stop_updater\r\n' \
                'для использования репостинга в канал задайте имя канала /set_channel_name\r\n' \
                'и запустите репстинг в канал /start_channel\r\n' \
                'если имя канала задано по умолчания, постинг уже активирован\r\n' \
                'для остановки репостинга в канал введите /stop_channel'
    elif normal and storm:
        reply = 'Сессия активирована, штурмовая игра в активном состоянии\r\n' \
                'для запуска слежения введите /start_updater\r\n' \
                'для остановки слежения введите /stop_updater\r\n' \
                'для использования репостинга в канал задайте имя канала /set_channel_name\r\n' \
                'и запустите репстинг в канал /start_channel\r\n' \
                'если имя канала задано по умолчания, постинг уже активирован\r\n' \
                'для остановки репостинга в канал введите /stop_channel'
    elif not storm:
        reply = 'Сессия активирована. Линейная игра не в активном состоянии\r\n' \
                'для запуска слежения введите /start_updater\r\n' \
                'для остановки слежения введите /stop_updater\r\n' \
                'для использования репостинга в канал задайте имя канала /set_channel_name\r\n' \
                'и запустите репстинг в канал /start_channel\r\n' \
                'для остановки репостинга в канал введите /stop_channel'
    else:
        reply = 'Сессия активирована. Штурмовая игра не в активном состоянии\r\n' \
                'для запуска слежения введите /start_updater\r\n' \
                'для остановки слежения введите /stop_updater\r\n' \
                'для использования репостинга в канал задайте имя канала /set_channel_name\r\n' \
                'и запустите репстинг в канал /start_channel\r\n' \
                'для остановки репостинга в канал введите /stop_channel'
    if DBSession.update_bool_flag(session['sessionid'], 'active', 'True'):
        bot.send_message(chat_id, reply)
    else:
        bot.send_message(chat_id, 'Не удалось запустить сессию')


def upd_session_cookie(session, bot, chat_id):
    try:
        if session['endomain'] not in session['loginurl']:
            if compile_urls(session['sessionid'], chat_id, bot, session['gameid'], session['endomain']):
                session = DBSession.get_session(session['sessionid'])
            else:
                return False
        response = requests.post(session['loginurl'], data={'Login': session['login'], 'Password': session['password']},
                                 headers={'Cookie': 'lang=ru'})
    except Exception:
        reply = 'Бот не залогинился - ошибка в конфигурации\r\nПроверьте конфигурацию сессии и попробуйте еще раз'
        bot.send_message(chat_id, reply, parse_mode='HTML')
        return False
    if not response.status_code == 200:
        reply = 'Бот не залогинился - движок вернул ошибку\r\nResponse code is %s\r\nТекст: %s' % (str(response.status_code), response.text)
        bot.send_message(chat_id, reply)
        return False

    cookie = response.request.headers['Cookie']
    if not 'stoken' in cookie:
        soup = BeautifulSoup(response.content)
        for div in soup.find_all('div'):
            if div.attrs['class'][0] == 'error':
                error = div.text.encode('utf-8')
                reply = 'Бот не залогинился - ошибка\r\nResponse error: %s' % error
                bot.send_message(chat_id, reply)
                return
        reply = 'Бот не смог обновить авторизовацию для взаимодействия с джижком\r\n' \
                'Если это повторяющееся сообщение - попробуйте выключить слежение, проверьте, что домен доступен, ' \
                'подождите минуту или несколько минут и снова запустите слежение'
        bot.send_message(chat_id, reply)
        return False
    if DBSession.update_text_field(session['sessionid'], 'cookie', cookie):
        return True
    else:
        return False


def initiate_session_vars(session, bot, chat_id, from_updater=False):
    game_model, normal = get_current_game_model(session, bot, chat_id, from_updater)
    if game_model:
        if game_model['LevelSequence'] == 3:
            DBSession.update_bool_flag(session['sessionid'], 'stormgame', 'True')
            storm = True
        else:
            DBSession.update_bool_flag(session['sessionid'], 'stormgame', 'False')
            storm = False
        if normal:
            existing_levels = DBLevels.get_level_ids_per_game(session['sessionid'], session['gameid'])
            for level in game_model['Levels']:
                if level['LevelId'] not in existing_levels:
                    DBLevels.insert_level(session['sessionid'], session['gameid'], level)
            if not game_model['LevelSequence'] == 3:
                current_level_info = game_model['Level']
                DBSession.update_int_field(session['sessionid'], 'currlevelid', current_level_info['LevelId'])
        game_loaded = True
        return game_loaded, normal, storm
    else:
        return None, None, None


def get_current_game_model(session, bot, chat_id, from_updater, params=None):
    if not params:
        params = {'json': '1'}
    game_model = None
    normal = None
    for i in xrange(2):
        if not i == 0:
            _ = upd_session_cookie(session, bot, chat_id)
            session = DBSession.get_session(session['sessionid'])
        try:
            response = requests.get(session['gameurl'], params=params, headers={'Cookie': session['cookie']})
            game_model = json.loads(response.text)
            if game_model['Event'] == 0:
                normal = True
            else:
                handle_inactive_game_model(game_model, session, bot, chat_id, from_updater)
                normal = False
            break
        except Exception:
            if i == 0:
                continue
            if "Your requests have been classified as robot's requests." in response.text:
                DBSession.update_bool_flag(session['sessionid'], 'stopupdater', 'True')
                reply = 'Сработала защита движка от повторяющихся запросов. Необходимо перезапустить слежение.\r\n/start_updater'
                bot.send_message(chat_id, reply)
            else:
                logging.exception('Exception - game model не является json объектом. Сессия %s' % session['sessionid'])
                bot.send_message(45839899, 'Exception - game model не является json объектом. Сессия %s' % session['sessionid'])
                reply = 'Updater не смог загрузить игру\r\nЕсли это повторяющееся сообщение - попробуйте выключить слежение, ' \
                        'подождать минуту или несколько минут и снова запустить слежение'
                bot.send_message(chat_id, reply)
                try:
                    print response
                    print response.text
                except:
                    pass
    return game_model, normal


def handle_inactive_game_model(game_model, session, bot, chat_id, from_updater=False):
    loaded_game_wrong_status = None
    if game_model['Event'] in game_wrong_statuses.keys():
        if game_model['Event'] == 17:
            DBSession.update_bool_flag(session['sessionid'], 'stopupdater', 'True')
            DBSession.update_bool_flag(session['sessionid'], 'usechannel', 'False')
            DBSession.update_bool_flag(session['sessionid'], 'active', 'False')
            DBSession.drop_session_vars(session['sessionid'])
            DB.cleanup_for_ended_game(session['sessionid'], session['gameid'])
            loaded_game_wrong_status = game_wrong_statuses[17] + '\r\nСессия остановлена, переменные сброшены'
            session = DBSession.get_session(session['sessionid'])
        else:
            for k, v in game_wrong_statuses.items():
                if game_model['Event'] == k:
                    loaded_game_wrong_status = v
    else:
        loaded_game_wrong_status = 'Состояние игры не соответствует ни одному из ожидаемых. Проверьте настройки бота'

    if not from_updater or not session['gamemodelstatus'] == loaded_game_wrong_status:
        DBSession.update_text_field(session['sessionid'], 'gamemodelstatus', loaded_game_wrong_status)
        bot.send_message(chat_id, loaded_game_wrong_status)


def get_current_level(session, bot, chat_id, from_updater=False):
    game_model, normal = get_current_game_model(session, bot, chat_id, from_updater)
    if normal:
        current_level = game_model['Level']
        levels = game_model['Levels']
        return current_level, levels
    else:
        return None, None


def get_storm_level(level_number, session, bot, chat_id, from_updater):
    storm_level_game_model, normal = get_current_game_model(session, bot, chat_id, from_updater,
                                                            params={'json': '1', 'level': str(level_number)})
    if normal:
        storm_level = storm_level_game_model['Level']
        return storm_level
    else:
        return None



def send_code_to_level(code, bot, chat_id, message_id, session, bonus_only=False):
    level, _ = get_current_level(session, bot, chat_id)
    if not level:
        return
    is_repeat_code = check_repeat_code(level, code)
    send_code(session, level, code, bot, chat_id, message_id, is_repeat_code, bonus_only)


def send_code_to_storm_level(code, level_number, bot, chat_id, message_id, session, bonus_only=False):
    storm_level = get_storm_level(level_number, session, bot, chat_id, from_updater=False)
    if not storm_level:
        return
    is_repeat_code = check_repeat_code(storm_level, code)
    send_code(session, storm_level, code, bot, chat_id, message_id, is_repeat_code, bonus_only)


def send_task_to_chat(bot, chat_id, session):
    level, _ = get_current_level(session, bot, chat_id)
    if not level:
        return
    send_task(session['sessionid'], level, bot, chat_id)


def send_task_to_chat_storm(bot, chat_id, session, storm_level_number):
    storm_level = get_storm_level(storm_level_number, session, bot, chat_id, from_updater=False)
    if not storm_level:
        return
    send_task(session['sessionid'], storm_level, bot, chat_id, storm=True)


def send_task_images_to_chat(bot, chat_id, session):
    level, _ = get_current_level(session, bot, chat_id)
    if not level:
        return
    send_task_images(level, bot, chat_id)


def send_all_sectors_to_chat(bot, chat_id, session):
    level, _ = get_current_level(session, bot, chat_id)
    if not level:
        return
    send_sectors(level, bot, chat_id)


def send_all_sectors_to_chat_storm(bot, chat_id, session, storm_level_number):
    storm_level = get_storm_level(storm_level_number, session, bot, chat_id, from_updater=False)
    if not storm_level:
        return
    send_sectors(storm_level, bot, chat_id)


def send_all_helps_to_chat(bot, chat_id, session):
    level, _ = get_current_level(session, bot, chat_id)
    if not level:
        return
    send_helps(session['sessionid'], level, bot, chat_id)


def send_all_helps_to_chat_storm(bot, chat_id, session, storm_level_number):
    storm_level = get_storm_level(storm_level_number, session, bot, chat_id, from_updater=False)
    if not storm_level:
        return
    send_helps(session['sessionid'], storm_level, bot, chat_id, storm=True)


def send_last_help_to_chat(bot, chat_id, session):
    level, _ = get_current_level(session, bot, chat_id)
    if not level:
        return
    send_last_help(session['sessionid'], level, bot, chat_id)


def send_last_help_to_chat_storm(bot, chat_id, session, storm_level_number):
    storm_level = get_storm_level(storm_level_number, session, bot, chat_id, from_updater=False)
    if not storm_level:
        return
    send_last_help(session['sessionid'], storm_level, bot, chat_id, storm=True)


def send_all_bonuses_to_chat(bot, chat_id, session):
    level, _ = get_current_level(session, bot, chat_id)
    if not level:
        return
    send_bonuses(session['sessionid'], level, bot, chat_id)


def send_all_bonuses_to_chat_storm(bot, chat_id, session, storm_level_number):
    storm_level = get_storm_level(storm_level_number, session, bot, chat_id, from_updater=False)
    if not storm_level:
        return
    levelmark = '<b>Уровень %s: %s</b>' % (str(storm_level['Number']), storm_level['Name'].encode('utf-8')) \
        if storm_level['Name'] else '<b>Уровень %s</b>' % str(storm_level['Number'])
    send_bonuses(session['sessionid'], storm_level, bot, chat_id, storm=True, levelmark=levelmark)


def send_unclosed_bonuses_to_chat(bot, chat_id, session):
    level, _ = get_current_level(session, bot, chat_id)
    if not level:
        return
    send_unclosed_bonuses(level, bot, chat_id)


def send_unclosed_bonuses_to_chat_storm(bot, chat_id, session, storm_level_number):
    storm_level = get_storm_level(storm_level_number, session, bot, chat_id, from_updater=False)
    if not storm_level:
        return
    send_unclosed_bonuses(storm_level, bot, chat_id)


def send_auth_messages_to_chat(bot, chat_id, session):
    level, _ = get_current_level(session, bot, chat_id)
    if not level:
        return
    send_auth_messages(session['sessionid'], level, bot, chat_id)


def send_auth_messages_to_chat_storm(bot, chat_id, session, storm_level_number):
    storm_level = get_storm_level(storm_level_number, session, bot, chat_id, from_updater=False)
    if not storm_level:
        return
    send_auth_messages(session['sessionid'], storm_level, bot, chat_id, storm=True)


def check_repeat_code(level, code, is_repeat_code=False):
    answered_sectors = get_answered_sectors(level['Sectors'])
    opened_bonuses = get_opened_bonuses(level['Bonuses'])
    code_answered_objects = get_answered_objects_for_code(code, answered_sectors, opened_bonuses)

    if code_answered_objects:
        is_repeat_code = True

    return is_repeat_code


def get_answered_sectors(sectors):
    answered_sectors = list() if not sectors else [sector for sector in sectors if sector['IsAnswered']]
    return answered_sectors


def get_opened_bonuses(bonuses):
    opened_bonuses = list() if not bonuses else [bonus for bonus in bonuses if bonus['IsAnswered']]
    return opened_bonuses


def get_answered_objects_for_code(code, answered_sectors, opened_bonuses):
    answered_objects = ''

    for sector in answered_sectors:
        if code == (sector['Answer']['Answer']).lower().encode('utf-8'):
            answered_objects += sector['Name'].encode('utf-8') if not answered_objects \
                else ', ' + sector['Name'].encode('utf-8')

    for bonus in opened_bonuses:
        if code == (bonus['Answer']['Answer']).lower().encode('utf-8'):
            bonus_name = bonus['Name'].encode('utf-8') if bonus['Name'] else "Бонус " + str(bonus['Number'])
            answered_objects += bonus_name if not answered_objects else ', ' + bonus_name

    return answered_objects


def send_code(session, level, code, bot, chat_id, message_id, is_repeat_code, bonus_only):
    has_answer_block_rule = level['HasAnswerBlockRule']
    if has_answer_block_rule and not bonus_only:
        bot.send_message(chat_id, '\xE2\x9B\x94\r\nСдача в основное окно выкл <b>(БЛОКИРОВКА)</b>'
                                  '\r\nБонусы сдавать в виде ?код', reply_to_message_id=message_id, parse_mode='HTML')
        return

    code_request = generate_code_request(level, code, bonus_only)

    for i in xrange(2):
        if not i == 0:
            _ = upd_session_cookie(session, bot, chat_id)
            session = DBSession.get_session(session['sessionid'])
        try:
            response = requests.post(session['gameurl'], data=code_request, headers={'Cookie': session['cookie']}, params={'json': '1'})
            game_model = json.loads(response.text)
            break
        except Exception:
            if i == 0:
                continue
            logging.exception('Exception - game model не является json объектом. Сессия %s' % session['sessionid'])
            bot.send_message(45839899, 'Exception - game model не является json объектом. Сессия %s' % session['sessionid'])
            bot.send_message(chat_id, '\xE2\x9D\x97\xE2\x9D\x97\xE2\x9D\x97\r\nОтправьте код повторно. Движок вернул некорректный ответ',
                             reply_to_message_id=message_id)
            return

    if not game_model['Event'] == 0:
        handle_inactive_game_model(game_model, session, bot, chat_id)
        return
    if is_repeat_code:
        bot.send_message(chat_id, '\xf0\x9f\x94\x84\r\nПовторный код', reply_to_message_id=message_id)
        return

    send_code_result = str(game_model['EngineAction']['LevelAction']['IsCorrectAnswer']) if not bonus_only else \
        str(game_model['EngineAction']['BonusAction']['IsCorrectAnswer'])
    reply = get_send_code_reply(code, send_code_result, level, game_model)
    bot.send_message(chat_id, reply, reply_to_message_id=message_id, parse_mode='HTML')
    if 'следующий' in reply:
        not_answered_sector_ids = list()
        for sector in level['Sectors']:
            if not sector['IsAnswered']:
                not_answered_sector_ids.append(sector['SectorId'])
        if len(not_answered_sector_ids) == 1:
            level_last_sector_id = not_answered_sector_ids[0]
            DBSectors.update_level_last_code(session['sessionid'], session['gameid'], level_last_sector_id, code,
                                             session['login'])


def generate_code_request(level, code, bonus_only):
    code_request = {
        'LevelId': level['LevelId'],
        'LevelNumber': level['Number']
    }
    if not bonus_only:
        code_request['LevelAction.Answer'] = code
    else:
        code_request['BonusAction.Answer'] = code
    return code_request


def get_send_code_reply(code, send_code_result, level, game_model):
    if send_code_result == 'True' and level['LevelId'] == game_model['Level']['LevelId']:
        reply = '\xE2\x9C\x85\r\nКод "%s" <b>принят</b>' % code
    elif send_code_result == 'True' and level['LevelId'] != game_model['Level']['LevelId']:
        reply = '\xE2\x9C\x85\r\nКод "%s" принят. Выдан следующий уровень' % code

    else:
        reply = '\xE2\x9D\x8C\r\nКод "%s" <b>НЕ принят</b>' % code

    return reply


def send_sectors(level, bot, chat_id):
    sectors = level['Sectors']
    if not sectors:
        bot.send_message(chat_id, 'На уровне 1 сектор')
        return

    for sector in sectors:
        name = sector['Name'].encode('utf-8')
        if sector['IsAnswered']:
            code = sector['Answer']['Answer'].encode('utf-8')
            player = sector['Answer']['Login'].encode('utf-8')
            message = '<b>C-р: ' + name + ' - </b>' + '\xE2\x9C\x85' + '<b> (' + player + ': ' + code + ')</b>'
        else:
            message = 'C-р: ' + name + ' - ' + '\xE2\x9D\x8C'
        bot.send_message(chat_id, message, parse_mode='HTML')


def send_helps(session_id, level, bot, chat_id, storm=False):
    helps = level['Helps']
    if helps:
        if not isinstance(helps, list):
            bot.send_message(chat_id, helps)
            return

        for help in helps:
            send_help(help, bot, chat_id, session_id, storm=storm) if help['HelpText'] is not None else send_time_to_help(help, bot, chat_id)
    else:
        bot.send_message(chat_id, 'Подсказок нет')


def send_last_help(session_id, level, bot, chat_id, storm=False):
    helps = level['Helps']
    if helps:
        if not isinstance(helps, list):
            bot.send_message(chat_id, helps)
            return

        for help in helps:
            if not help['HelpText']:
                helps.remove(help)

        send_help(helps[-1], bot, chat_id, session_id, storm=storm) if len(helps) > 0 else bot.send_message(chat_id,
                                                                                   'Еще нет пришедших подсказок')


def send_bonuses(session_id, level, bot, chat_id, storm=False, levelmark=None):
    bonuses = level['Bonuses']
    if bonuses:
        if not isinstance(bonuses, list):
            bot.send_message(chat_id, bonuses)
            return

        for bonus in bonuses:
            send_bonus_info(bonus, bot, chat_id, session_id, storm=storm, levelmark=levelmark) if not bonus['IsAnswered'] else \
                send_bonus_award_answer(bonus, bot, chat_id, session_id, storm=storm, levelmark=levelmark)
    else:
        bot.send_message(chat_id, 'Бонусов нет')


def send_unclosed_bonuses(level, bot, chat_id):
    bonuses = level['Bonuses']
    unclosed_bonuses = list()
    bonus_nums = ''
    if bonuses:
        if not isinstance(bonuses, list):
            bot.send_message(chat_id, bonuses)
            return

        for bonus in bonuses:
            if not bonus['IsAnswered']:
                unclosed_bonuses.append(bonus)
                bonus_nums += str(bonus['Number']) if not bonus_nums else ', ' + str(bonus['Number'])
        if unclosed_bonuses:
            num = 'Не закрыто <b>%s бонусов</b>:\r\n' % str(len(unclosed_bonuses))
            bot.send_message(chat_id, num + bonus_nums, parse_mode='HTML')
    else:
        bot.send_message(chat_id, 'Не закрытых бонусов нет')


def send_auth_messages(session_id, level, bot, chat_id, storm=False):
    messages = level['Messages']
    if messages:
        if not isinstance(messages, list):
            bot.send_message(chat_id, messages)
            return

        for message in messages:
            send_adm_message(message, bot, chat_id, session_id, storm=storm)
    else:
        bot.send_message(chat_id, 'Сообщений от авторов нет')


def send_task_images(level, bot, chat_id):
    images = list()
    tasks = level['Tasks']
    if tasks:
        text = tasks[0]['TaskText'].encode('utf-8')
    else:
        bot.send_message(chat_id, 'Задание не предусмотрено')

    soup = BeautifulSoup(text)
    for img in soup.find_all('img'):
        images.append(img.get('src').encode('utf-8'))
    if images:
        for image in images:
            bot.send_photo(chat_id, image)
    else:
        bot.send_message(chat_id, 'Картинки отсутствуют')


def send_live_locations_to_chat(bot, chat_id, session, locations, ll_message_ids, coords=None, duration=None, custom_points=None):
    not_in_chat_bots = list()
    if not custom_points:
        if not coords:
            level, _ = get_current_level(session, bot, chat_id)
            if level['LevelId'] != session['currlevelid']:
                bot.send_message(chat_id, 'Уровень изменился. '
                                          'Повторите команду, если хотите поставить live_location для нового уровня')
                return
            for k, v in locations.items():
                if int(k) > 20:
                    continue
                latitude = re.findall(r'\d\d\.\d{4,7}', str(v))[0]
                longitude = re.findall(r'\d\d\.\d{4,7}', str(v))[1]
                live_period = level['TimeoutSecondsRemain'] if level['TimeoutSecondsRemain'] else 10800
                try:
                    response = telebot.TeleBot(DB.get_location_bot_token_by_number(k)).send_location(
                        chat_id, latitude, longitude, live_period=live_period)
                    ll_message_ids[k] = str(response.message_id)
                except Exception as e:
                    response_text = json.loads(e.result.text)['description'].encode('utf-8')
                    if "chat not found" in response_text:
                        not_in_chat_bots.append(str(k))
                    else:
                        bot.send_message(chat_id, 'Live location точки %s не отправлена.\r\n%s' % (str(k), response_text))
            if not_in_chat_bots:
                bot.send_message(chat_id, 'Live location для следующих точек не отправлен: %s.\r\n'
                                          'В чате нет соответствующего(-их) бота(-ов)\r\n'
                                          'Найти и добавить ботов можно по следующему шаблону: @JekaLocation1Bot' % str(not_in_chat_bots))
            DBSession.update_json_field(session['sessionid'], 'llmessageids', ll_message_ids)
        else:
            latitude = re.findall(r'\d\d\.\d{4,7}', str(coords))[0]
            longitude = re.findall(r'\d\d\.\d{4,7}', str(coords))[1]
            live_period = duration if duration else 10800
            response = bot.send_location(chat_id, latitude, longitude, live_period=live_period)
            ll_message_ids['0'] = str(response.message_id)
            coord_Y_G = make_Y_G_links(str(coords))
            bot.send_message(chat_id, coord_Y_G, parse_mode='HTML', disable_web_page_preview=True)
            DBSession.update_json_field(session['sessionid'], 'llmessageids', ll_message_ids)
    else:
        for k, v in custom_points.items():
            if int(k) > 20:
                bot.send_message(chat_id, 'Нельзя поставить точку с номером %s. Доступные номера: 1-15' % k)
                continue
            latitude = re.findall(r'\d\d\.\d{4,7}', v)[0]
            longitude = re.findall(r'\d\d\.\d{4,7}', v)[1]
            live_period = duration if duration else 10800
            try:
                response = telebot.TeleBot(DB.get_location_bot_token_by_number(k)).send_location(
                    chat_id, latitude, longitude, live_period=live_period)
                ll_message_ids[k] = str(response.message_id)
                coord_Y_G = make_Y_G_links(v) + ' - ' + k
                bot.send_message(chat_id, coord_Y_G, parse_mode='HTML', disable_web_page_preview=True)
            except Exception as e:
                response_text = json.loads(e.result.text)['description'].encode('utf-8')
                if "chat not found" in response_text:
                    not_in_chat_bots.append(str(k))
                else:
                    bot.send_message(chat_id, 'Live location точки %s не отправлена.\r\n%s' % (k, response_text))
        if not_in_chat_bots:
            bot.send_message(chat_id, 'Live location для следующих точек не отправлен: %s.\r\n'
                                      'В чате нет соответствующего(-их) бота(-ов)\r\n'
                                      'Найти и добавить ботов можно по следующему шаблону: @JekaLocation1Bot' % str(not_in_chat_bots))
        DBSession.update_json_field(session['sessionid'], 'llmessageids', ll_message_ids)


def send_map_file(bot, chat_id, session, locations, message_id):
    # os.chdir(os.getcwd() + '/static/map')
    kml = simplekml.Kml()
    level_number = DBLevels.get_level_number(session['sessionid'], session['currlevelid'])
    filename = 'level' + str(level_number) + '_' + str(session['sessionid'])[-4:] + '.kml'
    for k, v in locations.items():
        latitude = re.findall(r'\d\d\.\d{4,7}', str(v))[0]
        longitude = re.findall(r'\d\d\.\d{4,7}', str(v))[1]
        kml.newpoint(name=str(k), coords=[(float(longitude), float(latitude))])  # lon, lat, optional height
    if os.path.exists(filename):
        os.remove(filename)
    kml.save(filename)
    doc = open(filename, 'rb')
    bot.send_document(chat_id, doc, reply_to_message_id=message_id)
    doc.close()


def check_channel(bot, chat_id, new_channel_name):
    try:
        bot.send_message(new_channel_name, 'Тестовое сообщение')
        return True
    except Exception as error:
        channel_error_handling(bot, chat_id, error, 'Тестовое сообщение не отправлено в канал.\r\n')
        logging.exception('Exception - updater не смог прислать тестовое сообщение в канал')
        return False
