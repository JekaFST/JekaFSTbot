# -*- coding: utf-8 -*-
from DBMethods import DB


class MainVars(object):
    def __init__(self):
        self.allowed_chats = [
            45839899,
            -1001145974445,
            -1001062839624,
            -1001126631174, #P4
            -1001076545820,
            -1001116652124,
            -169229164,
            -1001135150893,
            -1001184863414
        ]
        self.task_queue = list()
        self.sessions_dict = dict()
        self.additional_ids = dict()
        self.updater_schedulers_dict = dict()
        self.updaters_dict = dict()


class Validations(object):
    @staticmethod
    def check_permission(chat_id, bot):
        main_chat_ids, add_chat_ids = DB.get_allowed_chat_ids()
        if chat_id in main_chat_ids or chat_id in add_chat_ids:
            return True, main_chat_ids, add_chat_ids
        else:
            bot.send_message(chat_id,
                             'Данный чат не является ни основным, ни дополнительным разрешенным для работы с ботом\r\n'
                             'Для отправки запроса на разрешение введите /ask_for_permission')
            return False, _, _

    @staticmethod
    def check_session_available(chat_id, bot, sessions_chats):
        if chat_id in sessions_chats or DB.get_main_chat_id_via_add(chat_id) in sessions_chats:
            return True
        else:
            bot.send_message(chat_id, 'Для данного чата нет сессии. Для создания введите команду /start')
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
    def __init__(self, chat_id, type, session=None, message_id=None, user_id=None):
        self.chat_id = chat_id
        self.type = type
        self.session = session
        self.message_id = message_id
        self.user_id = user_id

    @staticmethod
    def get_session(chat_id, add_chat_ids, sessions_dict):
        session = sessions_dict[chat_id] if chat_id not in add_chat_ids \
            else sessions_dict[DB.get_main_chat_id_via_add(chat_id)]
        return session
