# -*- coding: utf-8 -*-
import threading

import telebot

from BotService import BotService
from BotSession import BotSession
from Updater import Updater

bot = telebot.TeleBot('370362982:AAH5ojKT0LSw8jS-vLfDF1bDE8rWWDyTeso')
bot_service = BotService(bot)
th_flask = threading.Thread(name='th_flask', target=bot_service.start_flask())
th_flask.start()
th_flask.join()
# session = BotSession()
# updater = Updater()
# allowed_chat_ids = allowed_chat_ids

# while True:
#     for task in main_thread.task_queue:
#         if task['task_type'] == 'start':
#             session.active = main_thread.start(task['chat_id'])
#             main_thread.task_queue.remove(task)
