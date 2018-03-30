# -*- coding: utf-8 -*-
import os
import threading
import telebot
from BotService import run_app
from DBMethods import DB
from MainClasses import MainVars
from TaskMathodMap import TaskMethodMap

main_vars = MainVars()
# Bind to PORT if defined, otherwise default to 5000.
# port = int(os.environ.get('PORT', 5000))
port = 443
bot = telebot.TeleBot(DB.get_main_bot_token())

try:
    th_flask = threading.Thread(name='th_flask', target=run_app(bot, main_vars).run, args=('0.0.0.0', port))
    th_flask.start()
except Exception:
    bot.send_message(45839899, 'Exception в main - не удалось запустить Flask')

while True:
    for task in main_vars.task_queue:
        try:
            TaskMethodMap.run_task(task, bot)
        except Exception as e:
            bot.send_message(task.chat_id, 'Exception в main - не удалось обработать команду %s' % task.type)
            print e
        main_vars.task_queue.remove(task)
