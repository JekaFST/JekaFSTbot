# -*- coding: utf-8 -*-
import requests
import json
from bs4 import BeautifulSoup
from CommonMethods import send_help, send_time_to_help, send_bonus_info, send_bonus_award_answer, send_task
from Config import game_wrong_statuses


def compile_urls(urls, config):
    urls['game_url'] = str(config['en_domain'] + config['game_url_ending'] + config['game_id'])
    urls['game_url_js'] = str(config['en_domain'] + config['game_url_ending'] + config['game_id'] + config['json'])
    urls['login_url'] = str(config['en_domain'] + config['login_url_ending'])
    return urls


def login_to_en(session, bot, chat_id):
    got_cookies = upd_session_cookie(session, bot, chat_id)
    if got_cookies:
        bot.send_message(chat_id, 'Бот успешно залогинился')


def launch_session(session, bot, chat_id):
    if not 'stoken' in session.config['cookie']:
        bot.send_message(chat_id, 'Сессия не активирована - бот не залогинен\n'
                                  'Проверьте конфигурацию /config и залогиньтесь /login_to_en')
    session.active = True
    session.current_level = get_current_level(session, bot, chat_id)
    if not session.current_level:
        reply = 'Сессия активирована. Игра не в нормальном состоянии' \
                'для запуска слежения введите /start_updater\r\n' \
                'для остановки слежения введите /stop_updater\r\n' \
                'для использования репостинга в канал задайте имя канала /set_channel_name\r\n' \
                'и запустите репстинг в канал /start_channel\r\n' \
                'для остановки репостинга в канал введите /stop_channel'
        bot.send_message(chat_id, reply)
    else:
        session.number_of_levels = session.current_level['number_of_levels']
        reply = 'Сессия активирована, игра в нормальном состоянии\r\n' \
                'для запуска слежения введите /start_updater\r\n' \
                'для остановки слежения введите /stop_updater\r\n' \
                'для использования репостинга в канал задайте имя канала /set_channel_name\r\n' \
                'и запустите репстинг в канал /start_channel\r\n' \
                'для остановки репостинга в канал введите /stop_channel'
        bot.send_message(chat_id, reply)


def upd_session_cookie(session, bot, chat_id):
    try:
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


def get_current_level(session, bot, chat_id, from_updater=False):
    game_model = get_current_game_model(session, bot, chat_id, from_updater)
    if game_model:
        current_level_info = game_model['Level']
        current_level_info['number_of_levels'] = len(game_model['Levels'])
        return current_level_info
    else:
        return None


def send_code_to_level(code, bot, chat_id, message_id, session, bonus_only=False):
    level = get_current_level(session, bot, chat_id)
    if not level:
        return
    is_repeat_code = check_repeat_code(level, code)
    send_code(session, level, code, bot, chat_id, message_id, is_repeat_code, bonus_only)


def send_task_to_chat(bot, chat_id, session):
    level = get_current_level(session, bot, chat_id)
    if not level:
        return
    send_task(level, bot, chat_id)


def send_task_images_to_chat(bot, chat_id, session):
    level = get_current_level(session, bot, chat_id)
    if not level:
        return
    send_task_images(level, bot, chat_id)


def send_all_sectors_to_chat(bot, chat_id, session):
    level = get_current_level(session, bot, chat_id)
    if not level:
        return
    send_sectors(level, bot, chat_id)


def send_all_helps_to_chat(bot, chat_id, session):
    level = get_current_level(session, bot, chat_id)
    if not level:
        return
    send_helps(level, bot, chat_id)


def send_last_help_to_chat(bot, chat_id, session):
    level = get_current_level(session, bot, chat_id)
    if not level:
        return
    send_last_help(level, bot, chat_id)


def send_all_bonuses_to_chat(bot, chat_id, session):
    level = get_current_level(session, bot, chat_id)
    if not level:
        return
    send_bonuses(level, bot, chat_id)


def get_current_game_model(session, bot, chat_id, from_updater):
    for i in xrange(2):
        if not i == 0:
            _ = upd_session_cookie(session, bot, chat_id)
        response = requests.get(session.urls['game_url_js'], headers={'Cookie': session.config['cookie']})
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
        session.current_game_model = game_model
        return game_model

    loaded_game_wrong_status = None
    if game_model['Event'] in game_wrong_statuses.keys():
        if game_model['Event'] == 17:
            session.stop_updater = True
            session.use_channel = False
            session.active = False
        for k, v in game_wrong_statuses.items():
            if game_model['Event'] == k:
                loaded_game_wrong_status = v
    else:
        loaded_game_wrong_status = 'Состояние игры не соответствует ни одному из ожидаемых. Проверьте настройки бота'

    if not from_updater or not session.game_model_status == loaded_game_wrong_status:
        bot.send_message(chat_id, loaded_game_wrong_status)
        session.game_model_status = loaded_game_wrong_status

    return False


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
            answered_objects = answered_objects + sector['Name'].encode('utf-8') if not answered_objects else \
                answered_objects + ', ' + sector['Name'].encode('utf-8')

    for bonus in opened_bonuses:
        if code == (bonus['Answer']['Answer']).lower().encode('utf-8'):
            bonus_name = bonus['Name'].encode('utf-8') if bonus['Name'] else "Бонус " + str(bonus['Number'])
            answered_objects = answered_objects + bonus_name if not answered_objects else \
                answered_objects + ', ' + bonus_name

    return answered_objects


def send_code(session, level, code, bot, chat_id, message_id, is_repeat_code, bonus_only):
    has_answer_block_rule = level['HasAnswerBlockRule']
    if has_answer_block_rule and not bonus_only:
        bot.send_message(chat_id, '\xE2\x9B\x94\r\nСдача в основное окно выкл <b>(БЛОКИРОВКА)</b>'
                                  '\r\nБонусы сдавать в виде ?код', reply_to_message_id=message_id, parse_mode='HTML')
        return

    code_request = generate_code_request(session.config['code_request'], level, code, bonus_only)

    response = requests.post(session.urls['game_url_js'], data=code_request, headers={'Cookie': session.config['cookie']})
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


def generate_code_request(code_request, level, code, bonus_only):
    code_request['LevelId'] = level['LevelId']
    code_request['LevelNumber'] = level['Number']
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


def send_helps(level, bot, chat_id):
    helps = level['Helps']
    if helps:
        if not isinstance(helps, list):
            bot.send_message(chat_id, helps)
            return

        for help in helps:
            send_help(help, bot, chat_id) if help['HelpText'] is not None else send_time_to_help(help, bot, chat_id)
    else:
        bot.send_message(chat_id, 'Подсказок нет')


def send_last_help(level, bot, chat_id):
    helps = level['Helps']
    if helps:
        if not isinstance(helps, list):
            bot.send_message(chat_id, helps)
            return

        for help in helps:
            if not help['HelpText']:
                helps.remove(help)

        send_help(helps[-1], bot, chat_id) if len(helps) > 0 else bot.send_message(chat_id,
                                                                                   'Еще нет пришедших подсказок')


def send_bonuses(level, bot, chat_id):
    bonuses = level['Bonuses']
    if bonuses:
        if not isinstance(bonuses, list):
            bot.send_message(chat_id, bonuses)
            return

        for bonus in bonuses:
            send_bonus_info(bonus, bot, chat_id) if not bonus['IsAnswered'] else send_bonus_award_answer(bonus, bot,
                                                                                                         chat_id)
    else:
        bot.send_message(chat_id, 'Бонусов нет')


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
