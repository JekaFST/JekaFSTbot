# -*- coding: utf-8 -*-
import os
import threading
import time
from Queue import PriorityQueue
import telebot
from Const import prod, num_worker_threads
from BotService import run_app
from DBMethods import DB
from MainMethods import reload_backup
from TaskMathodMap import TaskMethodMap


class Counter(object):
    def __init__(self):
        self.code_tasks_in = 0
        self.code_tasks_out = 0
        self.a = float()
        self.b = float()

    def drop_counter(self):
        self.code_tasks_in = 0
        self.code_tasks_out = 0
        self.a = float()
        self.b = float()


def worker():
    while True:
        if counter.a and counter.b:
            print str(counter.b-counter.a)
            counter.drop_counter()
        if not queue.empty():
            task = queue.get()[1]
            if task.type == 'send_code_bonus':
                counter.code_tasks_in += 1
            if counter.code_tasks_in == 1:
                counter.a = time.time()
            TaskMethodMap.run_task(task, bot)
            queue.task_done()
            if task.type == 'send_code_bonus':
                counter.code_tasks_out += 1
            if counter.code_tasks_out == 100:
                counter.b = time.time()


port = int(os.environ.get('PORT', 5000)) if prod else 443

counter = Counter()
queue = PriorityQueue()
bot = telebot.TeleBot(DB.get_main_bot_token()) if prod else telebot.TeleBot("583637976:AAEFrQFiAaGuKwmoRV0N1MwU-ujRzmCxCAo")
bot.remove_webhook()
bot.set_webhook(url='https://powerful-shelf-32284.herokuapp.com/webhook') if prod \
    else bot.set_webhook(url='https://30a53a77.ngrok.io/webhook')

try:
    threading.Thread(name='th_flask', target=run_app(bot, queue).run, args=('0.0.0.0', port)).start()
except Exception:
    bot.send_message(45839899, 'Exception в main - не удалось запустить Flask')

reload_backup(bot, queue)
for i in range(num_worker_threads):
    threading.Thread(target=worker).start()
