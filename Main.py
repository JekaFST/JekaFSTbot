# -*- coding: utf-8 -*-
import os
import threading
import telebot
from Const import prod
from BotService import run_app
from DBMethods import DB
from collections import deque
from MainMethods import reload_backup
from TaskMathodMap import TaskMethodMap


port = int(os.environ.get('PORT', 5000)) if prod else 443

queue = deque()
bot = telebot.TeleBot(DB.get_main_bot_token()) if prod else telebot.TeleBot("583637976:AAEFrQFiAaGuKwmoRV0N1MwU-ujRzmCxCAo")
bot.remove_webhook()
bot.set_webhook(url='https://powerful-shelf-32284.herokuapp.com/webhook') if prod \
    else bot.set_webhook(url='https://9cc3d30b.ngrok.io/webhook')

try:
    threading.Thread(name='th_flask', target=run_app(bot, queue).run, args=('0.0.0.0', port)).start()
except Exception:
    bot.send_message(45839899, 'Exception в main - не удалось запустить Flask')

reload_backup(bot, queue)

while True:
    if not len(queue) == 0:
        TaskMethodMap.run_task(queue.popleft(), bot)
