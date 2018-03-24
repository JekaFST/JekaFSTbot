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


class Task(object):
    def __init__(self, chat_id, bot):
        self.main_chat_ids, self.add_chat_ids = DB.get_allowed_chat_ids()
        self.chat_id = chat_id
        self.bot = bot

    def check_permission(self):
        if self.chat_id not in self.main_chat_ids and self.chat_id not in self.add_chat_ids:
            self.bot.send_message(self.chat_id,
                                  'Данный чат не является ни основным, ни дополнительным разрешенным для работы с ботом\r\n'
                                  'Для отправки запроса на разрешение введите /ask_for_permission')
            return False
        else:
            return True

    def create_task_dict(self, task_type, message_id=None, user_id=None):
        task_dict = None
        if self.chat_id in self.main_chat_ids:
            task_dict = {
                'task_type': task_type,
                'chat_id': self.chat_id,
                'additional_chat_id': None if not user_id else user_id,
                'message_id': message_id
            }
        elif self.chat_id in self.add_chat_ids:
            task_dict = {
                'task_type': task_type,
                'chat_id': None,
                'additional_chat_id': self.chat_id,
                'message_id': message_id
            }
        return task_dict
