# -*- coding: utf-8 -*-
from bs4 import BeautifulSoup
from CommonMethods import send_task
from SessionMethods import *


class BotSession(object):
    def __init__(self):
        self.config = {
                    'game_url_ending': '/gameengines/encounter/play/',
                    'login_url_ending': '/Login.aspx',
                    'json': '?json=1',
                    'Login': 'jekafst_bot',
                    'Password': 'jekabot_1412',
                    'code_request': {},
                    'en_domain': 'http://deadline.en.cx',
                    'game_id': '59833'
                   }
        self.current_level = None
        self.urls = dict()
        self.updater = None
        self.number_of_levels = None
        self.channel_name = '@r4channel'
        self.use_channel = False
        self.game_answered_bonus_ids = list()
        self.active = False

    def make_urls(self):
        self.urls = compile_urls(self.urls, self.config)

    def login_to_en(self, bot, chat_id):
        try:
            response = requests.post(self.urls['login_url'], data={'Login': self.config['Login'],
                                                                   'Password': self.config['Password']},
                                     headers={'Cookie': 'lang=ru'})
        except Exception:
            reply = '<b>Exception</b>\r\nПроверьте конфигурацию игры и попробуйте еще раз'
            return reply
        if not response.status_code == 200:
            reply = 'Бот не залогинился\r\nResponse code is %s\r\nТекст: %s' % (str(response.status_code), response.text)
            return reply

        self.config['cookie'] = response.request.headers['Cookie']
        if not 'stoken' in self.config['cookie']:
            soup = BeautifulSoup(response.content)
            for title in soup.find_all('title'):
                text = title.text.encode('utf-8')
                reply = 'Бот не залогинился\r\nResponse title: %s' % text
                return reply

        self.current_level = self.get_current_level(bot, chat_id)
        if not self.current_level:
            reply = 'Бот залогинился. Чтобы начать им пользоваться, нужно чтобы игра была в нормальном состоянии'
        else:
            self.number_of_levels = self.current_level['number_of_levels']
            reply = 'Бот успешно залогинился, игра в нормальном состоянии\r\n' \
                    'для запуска слежения введите /start_updater\r\n' \
                    'для остановки слежения введите /stop_updater'

        return reply

    def get_current_level(self, bot, chat_id, from_updater=False):
        game_model = get_current_game_model(self.urls, self.config, self.updater, bot, chat_id, from_updater)
        if game_model:
            current_level_info = game_model['Level']
            current_level_info['number_of_levels'] = len(game_model['Levels'])
            return current_level_info
        else:
            return None

    def send_code_to_level(self, code, bot, chat_id, message_id, bonus_only=False):
        level = self.get_current_level(bot, chat_id)
        if not level:
            return
        is_repeat_code = check_repeat_code(level, code)
        send_code(self.config, level, code, self.urls, self.updater, bot, chat_id, message_id, is_repeat_code,
                  bonus_only)

    def send_task(self, bot, chat_id):
        level = self.get_current_level(bot, chat_id)
        if not level:
            return
        send_task(level, bot, chat_id)

    def send_all_sectors(self, bot, chat_id):
        level = self.get_current_level(bot, chat_id)
        if not level:
            return
        send_sectors(level, bot, chat_id)

    def send_all_helps(self, bot, chat_id):
        level = self.get_current_level(bot, chat_id)
        if not level:
            return
        send_helps(level, bot, chat_id)

    def send_last_help(self, bot, chat_id):
        level = self.get_current_level(bot, chat_id)
        if not level:
            return
        send_last_help(level, bot, chat_id)

    def send_all_bonuses(self, bot, chat_id):
        level = self.get_current_level(bot, chat_id)
        if not level:
            return
        send_bonuses(level, bot, chat_id)
