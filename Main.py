# -*- coding: utf-8 -*-
import os
import threading
import telebot
from Const import prod
from BotService import run_app
from DBMethods import DB
from MainClasses import MainVars
from MainMethods import reload_backup
from TaskMathodMap import TaskMethodMap


main_vars = MainVars()
port = int(os.environ.get('PORT', 5000)) if prod else 443

bot = telebot.TeleBot(DB.get_main_bot_token()) if prod else telebot.TeleBot("583637976:AAEFrQFiAaGuKwmoRV0N1MwU-ujRzmCxCAo")
bot.remove_webhook()
bot.set_webhook(url='https://powerful-shelf-32284.herokuapp.com/webhook') if prod \
    else bot.set_webhook(url='https://4b380b9e.ngrok.io/webhook')

try:
    th_flask = threading.Thread(name='th_flask', target=run_app(bot, main_vars).run, args=('0.0.0.0', port))
    th_flask.start()
except Exception:
    bot.send_message(45839899, 'Exception в main - не удалось запустить Flask')

reload_backup(bot, main_vars)

while True:
    for task in main_vars.task_queue:
        TaskMethodMap.run_task(task, bot)
        main_vars.task_queue.remove(task)
