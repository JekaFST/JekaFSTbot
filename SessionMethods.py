# -*- coding: utf-8 -*-
import re
import requests
import json
from bs4 import BeautifulSoup
from CommonMethods import send_help, send_time_to_help, send_bonus_info, send_bonus_award_answer, send_task, \
    send_adm_message
from Config import game_wrong_statuses, coord_bots


def compile_urls(config):
    urls = dict()
    urls['game_url'] = str(config['en_domain'] + config['game_url_ending'] + config['game_id'])
    urls['game_url_js'] = str(config['en_domain'] + config['game_url_ending'] + config['game_id'] + config['json'])
    urls['login_url'] = str(config['en_domain'] + config['login_url_ending'])
    return urls


def login_to_en(session, bot, chat_id):
    got_cookies = upd_session_cookie(session, bot, chat_id)
    if got_cookies:
        bot.send_message(chat_id, 'Бот успешно залогинился')


def launch_session(session, bot, chat_id):
    if 'stoken' not in session.config['cookie']:
        bot.send_message(chat_id, 'Сессия не активирована - бот не залогинен\n'
                                  'Проверьте конфигурацию /config и залогиньтесь /login_to_en')
        return
    session.active = True
    session.current_level, session.storm_levels = initiate_session_vars(session, bot, chat_id)
    if session.current_level:
        reply = 'Сессия активирована, игра в нормальном состоянии\r\n' \
                'для запуска слежения введите /start_updater\r\n' \
                'для остановки слежения введите /stop_updater\r\n' \
                'для использования репостинга в канал задайте имя канала /set_channel_name\r\n' \
                'и запустите репстинг в канал /start_channel\r\n' \
                'для остановки репостинга в канал введите /stop_channel'
        bot.send_message(chat_id, reply)
    elif session.storm_levels:
        reply = 'Сессия активирована, штурмовая игра в нормальном состоянии\r\n' \
                'для запуска слежения введите /start_updater\r\n' \
                'для остановки слежения введите /stop_updater\r\n' \
                'для использования репостинга в канал задайте имя канала /set_channel_name\r\n' \
                'и запустите репстинг в канал /start_channel\r\n' \
                'для остановки репостинга в канал введите /stop_channel'
        bot.send_message(chat_id, reply)
    else:
        reply = 'Сессия активирована. Игра не в нормальном состоянии\r\n' \
                'для запуска слежения введите /start_updater\r\n' \
                'для остановки слежения введите /stop_updater\r\n' \
                'для использования репостинга в канал задайте имя канала /set_channel_name\r\n' \
                'и запустите репстинг в канал /start_channel\r\n' \
                'для остановки репостинга в канал введите /stop_channel'
        bot.send_message(chat_id, reply)


def upd_session_cookie(session, bot, chat_id):
    try:
        if session.config['en_domain'] not in session.urls['login_url']:
            session.urls = compile_urls(session.config)
        response = requests.post(session.urls['login_url'], data={'Login': session.config['Login'],
                                                                  'Password': session.config['Password']},
                                 headers={'Cookie': 'lang=ru'})
    except Exception:
        reply = '<b>Exception</b>\r\nПроверьте конфигурацию игры и попробуйте еще раз'
        bot.send_message(chat_id, reply, parse_mode='HTML')
        return False
    if not response.status_code == 200:
        reply = 'Бот не залогинился\r\nResponse code is %s\r\nТекст: %s' % (str(response.status_code), response.text)
        bot.send_message(chat_id, reply)
        return False

    session.config['cookie'] = response.request.headers['Cookie']
    if not 'stoken' in session.config['cookie']:
        soup = BeautifulSoup(response.content)
        for div in soup.find_all('div'):
            if div.attrs['class'][0] == 'error':
                error = div.text.encode('utf-8')
                reply = 'Бот не залогинился\r\nResponse error: %s' % error
                bot.send_message(chat_id, reply)
                return
        reply = 'Бот не залогинился, попробуйте еще раз'
        bot.send_message(chat_id, reply)
        return False
    return True


def initiate_session_vars(session, bot, chat_id, from_updater=False):
    game_model = get_current_game_model(session, bot, chat_id, from_updater)
    if game_model and game_model['LevelSequence'] == 3:
        levels = game_model['Levels']
        storm_levels = get_storm_levels(len(levels), session, bot, chat_id, from_updater)
        session.storm_game = True
        return None, storm_levels
    elif game_model:
        current_level_info = game_model['Level']
        return current_level_info, None
    else:
        return None, None


def get_current_game_model(session, bot, chat_id, from_updater, storm_level_url=None):
    for i in xrange(2):
        if not i == 0:
            _ = upd_session_cookie(session, bot, chat_id)
        if session.config['en_domain'] not in session.urls['game_url_js'] or session.config['game_id'] not in session.urls['game_url_js']:
            session.urls = compile_urls(session.config)
        if not storm_level_url:
            response = requests.get(session.urls['game_url_js'], headers={'Cookie': session.config['cookie']})
        else:
            response = requests.get(storm_level_url, headers={'Cookie': session.config['cookie']})
        try:
            response_json = json.loads(response.text)
            break
        except Exception:
            if i == 0:
                continue
            if "Your requests have been classified as robot's requests." in response.text:
                session.stop_updater = True
                reply = 'Сработала защита движка от повторяющихся запросов.' \
                        ' Необходимо перелогиниться и перезапустить апдейтер.\r\n/login_to_en\r\n/start_updater'
                bot.send_message(chat_id, reply)
                return False
            else:
                session.stop_updater = True
                bot.send_message(chat_id, '<b>Exception</b>\r\nGame model не является json объектом', parse_mode='HTML')
                return False

    game_model = check_game_model(response_json, session, bot, chat_id, from_updater)
    return game_model


def check_game_model(game_model, session, bot, chat_id, from_updater=False):
    if game_model['Event'] == 0:
        # session.current_game_model = game_model
        return game_model

    loaded_game_wrong_status = None
    if game_model['Event'] in game_wrong_statuses.keys():
        if game_model['Event'] == 17:
            session.stop_updater = True
            session.use_channel = False
            session.active = False
            drop_session_vars(session)
            loaded_game_wrong_status = game_wrong_statuses.keys[17] + '\r\nСессия остановлена, переменные сброшены'
        else:
            for k, v in game_wrong_statuses.items():
                if game_model['Event'] == k:
                    loaded_game_wrong_status = v
    else:
        loaded_game_wrong_status = 'Состояние игры не соответствует ни одному из ожидаемых. Проверьте настройки бота'

    if not from_updater or not session.game_model_status == loaded_game_wrong_status:
        bot.send_message(chat_id, loaded_game_wrong_status)
        session.game_model_status = loaded_game_wrong_status

    return False


def get_current_level(session, bot, chat_id, from_updater=False):
    game_model = get_current_game_model(session, bot, chat_id, from_updater)
    if game_model:
        current_level = game_model['Level']
        levels = game_model['Levels']
        return current_level, levels
    else:
        return None, None


def get_storm_levels(levels_qty, session, bot, chat_id, from_updater=False):
    storm_levels = list()
    for i in xrange(levels_qty):
        storm_levels.append(get_storm_level(i+1, session, bot, chat_id, from_updater))
    return storm_levels


def get_storm_level(level_number, session, bot, chat_id, from_updater):
    url_ending = '?level=%s&json=1' % str(level_number)
    url = str(session.config['en_domain'] + session.config['game_url_ending'] + session.config['game_id'] + url_ending)
    storm_level_game_model = get_current_game_model(session, bot, chat_id, from_updater, storm_level_url=url)
    if not storm_level_game_model:
        return
    storm_level = storm_level_game_model['Level']
    return storm_level


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
    send_task(level, bot, chat_id, session.locations)


def send_task_to_chat_storm(bot, chat_id, session, storm_level_number):
    storm_level = get_storm_level(storm_level_number, session, bot, chat_id, from_updater=False)
    if not storm_level:
        return
    send_task(storm_level, bot, chat_id, session.locations, storm=True)


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
    send_helps(level, bot, chat_id, session.locations)


def send_all_helps_to_chat_storm(bot, chat_id, session, storm_level_number):
    storm_level = get_storm_level(storm_level_number, session, bot, chat_id, from_updater=False)
    if not storm_level:
        return
    send_helps(storm_level, bot, chat_id, session.locations, storm=True)


def send_last_help_to_chat(bot, chat_id, session):
    level, _ = get_current_level(session, bot, chat_id)
    if not level:
        return
    send_last_help(level, bot, chat_id, session.locations)


def send_last_help_to_chat_storm(bot, chat_id, session, storm_level_number):
    storm_level = get_storm_level(storm_level_number, session, bot, chat_id, from_updater=False)
    if not storm_level:
        return
    send_last_help(storm_level, bot, chat_id, session.locations, storm=True)


def send_all_bonuses_to_chat(bot, chat_id, session):
    level, _ = get_current_level(session, bot, chat_id)
    if not level:
        return
    send_bonuses(level, bot, chat_id, session.locations)


def send_all_bonuses_to_chat_storm(bot, chat_id, session, storm_level_number):
    storm_level = get_storm_level(storm_level_number, session, bot, chat_id, from_updater=False)
    if not storm_level:
        return
    send_bonuses(storm_level, bot, chat_id, session.locations, storm=True)


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
    send_auth_messages(level, bot, chat_id, session.locations)


def send_auth_messages_to_chat_storm(bot, chat_id, session, storm_level_number):
    storm_level = get_storm_level(storm_level_number, session, bot, chat_id, from_updater=False)
    if not storm_level:
        return
    send_auth_messages(storm_level, bot, chat_id, session.locations, storm=True)


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

    response = requests.post(session.urls['game_url_js'], data=code_request,
                             headers={'Cookie': session.config['cookie']})
    try:
        response_json = json.loads(response.text)
    except Exception:
        bot.send_message(chat_id, '<b>Exception</b>\r\nGame model не является json объектом', parse_mode='HTML')
        return
    game_model = check_game_model(response_json, session, bot, chat_id)
    if not game_model:
        return
    if is_repeat_code:
        bot.send_message(chat_id, '\xf0\x9f\x94\x84\r\nПовторный код', reply_to_message_id=message_id)
        return

    send_code_result = str(game_model['EngineAction']['LevelAction']['IsCorrectAnswer']) if not bonus_only else \
        str(game_model['EngineAction']['BonusAction']['IsCorrectAnswer'])
    reply = get_send_code_reply(code, send_code_result, level, game_model)
    bot.send_message(chat_id, reply, reply_to_message_id=message_id, parse_mode='HTML')


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


def send_helps(level, bot, chat_id, locations, storm=False):
    helps = level['Helps']
    if helps:
        if not isinstance(helps, list):
            bot.send_message(chat_id, helps)
            return

        for help in helps:
            send_help(help, bot, chat_id, locations, storm=storm) if help['HelpText'] is not None else send_time_to_help(help, bot, chat_id)
    else:
        bot.send_message(chat_id, 'Подсказок нет')


def send_last_help(level, bot, chat_id, locations, storm=False):
    helps = level['Helps']
    if helps:
        if not isinstance(helps, list):
            bot.send_message(chat_id, helps)
            return

        for help in helps:
            if not help['HelpText']:
                helps.remove(help)

        send_help(helps[-1], bot, chat_id, locations, storm=storm) if len(helps) > 0 else bot.send_message(chat_id,
                                                                                   'Еще нет пришедших подсказок')


def send_bonuses(level, bot, chat_id, locations, storm=False):
    bonuses = level['Bonuses']
    if bonuses:
        if not isinstance(bonuses, list):
            bot.send_message(chat_id, bonuses)
            return

        for bonus in bonuses:
            send_bonus_info(bonus, bot, chat_id, locations, storm=storm) if not bonus['IsAnswered'] else \
                send_bonus_award_answer(bonus, bot, chat_id, locations, storm=storm)
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


def send_auth_messages(level, bot, chat_id, locations, storm=False):
    messages = level['Messages']
    if messages:
        if not isinstance(messages, list):
            bot.send_message(chat_id, messages)
            return

        for message in messages:
            send_adm_message(message, bot, chat_id, locations, storm=storm)
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


def send_live_locations_to_chat(bot, chat_id, session, coords=None, duration=None, custom_points=None):
    not_in_chat_bots = list()
    if not custom_points:
        if not coords:
            level, _ = get_current_level(session, bot, chat_id)
            if level['LevelId'] != session.current_level['LevelId']:
                bot.send_message(chat_id, 'Уровень изменился. '
                                          'Повторите команду, если хотите поставить live_location для нового уровня')
                return
            for k, v in session.locations.items():
                if k > 15:
                    continue
                latitude = re.findall(r'\d\d\.\d{4,7}', v)[0]
                longitude = re.findall(r'\d\d\.\d{4,7}', v)[1]
                live_period = level['TimeoutSecondsRemain'] if level['TimeoutSecondsRemain'] else 10800
                try:
                    response = coord_bots[k].send_location(chat_id, latitude, longitude, live_period=live_period)
                    session.live_location_message_ids[k] = response.message_id
                except Exception as e:
                    response_text = json.loads(e.result.text)['description'].encode('utf-8')
                    if "chat not found" in response_text:
                        not_in_chat_bots.append(k)
                    else:
                        bot.send_message(chat_id, 'Live location точки %s не отправлена.\r\n%s' % (str(k)),
                                         response_text)
            if not_in_chat_bots:
                bot.send_message(chat_id, 'Live location для следующих точек не отправлен: %s.\r\n'
                                          'В чате нет соответствующего(-их) бота(-ов)' % str(not_in_chat_bots))
        else:
            latitude = re.findall(r'\d\d\.\d{4,7}', str(coords))[0]
            longitude = re.findall(r'\d\d\.\d{4,7}', str(coords))[1]
            live_period = duration if duration else 10800
            response = bot.send_location(chat_id, latitude, longitude, live_period=live_period)
            session.live_location_message_ids[0] = response.message_id
    else:
        for k, v in custom_points.items():
            if k > 15:
                bot.send_message(chat_id, 'Нельзя поставить точку с номером %s. Доступные номера: 1-15' % k)
                continue
            latitude = re.findall(r'\d\d\.\d{4,7}', v)[0]
            longitude = re.findall(r'\d\d\.\d{4,7}', v)[1]
            live_period = duration if duration else 10800
            try:
                response = coord_bots[k].send_location(chat_id, latitude, longitude, live_period=live_period)
                session.live_location_message_ids[k] = response.message_id
            except Exception as e:
                response_text = json.loads(e.result.text)['description'].encode('utf-8')
                if "chat not found" in response_text:
                    not_in_chat_bots.append(k)
                else:
                    bot.send_message(chat_id, 'Live location точки %s не отправлена.\r\n%s' % (str(k)),
                                     response_text)
        if not_in_chat_bots:
            bot.send_message(chat_id, 'Live location для следующих точек не отправлен: %s.\r\n'
                                      'В чате нет соответствующего(-их) бота(-ов)' % str(not_in_chat_bots))


def drop_session_vars(session):
    session.channel_name = None
    session.current_level = None
    session.storm_levels = None
    session.urls = {
            'game_url': '',
            'game_url_js': '',
            'login_url': ''
        }
    session.game_answered_bonus_ids = list()
    session.help_statuses = dict()
    session.bonus_statuses = dict()
    session.sector_statuses = dict()
    session.message_statuses = dict()
    session.sent_messages = list()
    session.time_to_up_sent = None
    session.sectors_to_close = None
    session.sectors_message_id = None
    session.game_model_status = None
    session.put_updater_task = None
    session.send_codes = True
    session.dismissed_level_ids = list()
    session.storm_game = False
