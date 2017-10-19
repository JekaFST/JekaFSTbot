import telebot


class MainVars(object):
    def __init__(self):
        self.allowed_chat_ids = [45839899, -1001145974445, -1001076545820, -1001116652124]
        self.bot = telebot.TeleBot('370362982:AAH5ojKT0LSw8jS-vLfDF1bDE8rWWDyTeso')
        self.task_queue = list()
        self.id = 0
        self.sessions_dict = dict()
        self.updater_schedulers_dict = dict()
