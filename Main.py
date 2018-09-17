# -*- coding: utf-8 -*-
import os
import time
import threading
import telebot
from Const import prod
from BotService import run_app
from DBMethods import DB
from collections import deque
from MainMethods import reload_backup
from TaskMathodMap import TaskMethodMap


class Counter(object):
    def __init__(self):
        self.code_tasks_in = 0
        self.code_tasks_out = 0
        self.a = float()
        self.b = float()


port = int(os.environ.get('PORT', 5000)) if prod else 443

counter = Counter()
queue = deque()
bot = telebot.TeleBot(DB.get_main_bot_token()) if prod else telebot.TeleBot("583637976:AAEFrQFiAaGuKwmoRV0N1MwU-ujRzmCxCAo")
bot.remove_webhook()
bot.set_webhook(url='https://powerful-shelf-32284.herokuapp.com/webhook') if prod \
    else bot.set_webhook(url='https://30a53a77.ngrok.io/webhook')

try:
    threading.Thread(name='th_flask', target=run_app(bot, queue).run, args=('0.0.0.0', port)).start()
except Exception:
    bot.send_message(45839899, 'Exception в main - не удалось запустить Flask')

reload_backup(bot, queue)

while True:
    if counter.a and counter.b:
        print str(counter.b - counter.a)
        counter.a = 0
        counter.b = 0
    if not len(queue) == 0:
        task = queue.popleft()
        if task.type == 'send_code_main':
            counter.code_tasks_in += 1
        if counter.code_tasks_in == 1:
            counter.a = time.time()
        TaskMethodMap.run_task(task, bot)
        if task.type == 'send_code_main':
            counter.code_tasks_out += 1
        if counter.code_tasks_out == 5:
            counter.b = time.time()
