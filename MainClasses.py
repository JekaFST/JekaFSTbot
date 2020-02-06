# -*- coding: utf-8 -*-
from DBMethods import DB, DBSession


class Validations(object):
    @staticmethod
    def check_permission(chat_id, bot):
        main_chat_ids, add_chat_ids = DB.get_allowed_chat_ids()
        if chat_id in main_chat_ids or chat_id in add_chat_ids:
            return True, main_chat_ids, add_chat_ids
        else:
            bot.send_message(chat_id,
                             'Данный чат не является ни основным, ни дополнительным разрешенным для работы с ботом\r\n'
                             'Для отправки запроса на разрешение введите /ask_for_permission\n'
                             'Краткая инструкция к боту доступна по ссылке:\n'
                             'https://jekafstbot.herokuapp.com/instruction', disable_web_page_preview=True)
            return False, main_chat_ids, add_chat_ids

    @staticmethod
    def check_session_available(chat_id, bot):
        sessions_ids = DBSession.get_sessions_ids()
        if chat_id in sessions_ids or DB.get_main_chat_id_via_add(chat_id) in sessions_ids:
            return True
        else:
            bot.send_message(chat_id, 'Для данного чата нет сессии. Для создания введите команду /start')
            return False

    @staticmethod
    def check_from_main_chat(chat_id, bot, main_chat_ids, message_id):
        if chat_id not in main_chat_ids:
            bot.send_message(chat_id, 'Эта команда недоступна из личного чата', reply_to_message_id=message_id)
            return False
        else:
            return True

    @staticmethod
    def check_from_add_chat(chat_id, add_chat_ids):
        if chat_id in add_chat_ids:
            return True
        else:
            return False

    @staticmethod
    def check_join_possible(chat_id, bot, user_id, message_id, add_chat_ids):
        if user_id == chat_id:
            bot.send_message(chat_id, 'Нельзя выполнить команду /join из личного чата. '
                                      'Для сброса взаимодействия из личного чата введите /reset_join',
                             reply_to_message_id=message_id)
            return False
        elif user_id in add_chat_ids:
            bot.send_message(chat_id, 'У вас уже есть сессия, в рамках которой взаимодействие с ботом '
                                      'настроено через личный чат. Для сброса введите /reset_join',
                             reply_to_message_id=message_id)
            return False
        else:
            return True

    @staticmethod
    def check_reset_join_possible(chat_id, bot, user_id, message_id, add_chat_ids):
        if user_id not in add_chat_ids:
            bot.send_message(chat_id, 'Нельзя выполнить команду /reset_join, '
                                      'если взаимодействие с ботом через личный чат не настроено',
                             reply_to_message_id=message_id)
            return False
        else:
            return True


class Task(object):
    def __init__(self, chat_id, type, session_id=None, message_id=None, user_id=None, queue=None, new_delay=None,
                 new_login=None, new_password=None, new_domain=None, duration=None, new_game_id=None, points=None,
                 new_channel_name=None, code=None, coords=None, storm_level_number=None, point=None, points_dict=None):
        self.chat_id = chat_id
        self.type = type
        self.session_id = session_id
        self.message_id = message_id
        self.user_id = user_id
        self.queue = queue
        self.new_delay = new_delay
        self.new_login = new_login
        self.new_password = new_password
        self.new_domain = new_domain
        self.new_game_id = new_game_id
        self.new_channel_name = new_channel_name
        self.code = code
        self.coords = coords
        self.storm_level_number = storm_level_number
        self.duration = duration
        self.point = point
        self.points_dict = points_dict
        self.points = points
