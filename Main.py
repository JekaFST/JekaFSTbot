# -*- coding: utf-8 -*-
import os
import threading
import telebot
from BotService import run_app
from DBMethods import DB
from MainMethods import start, stop_session, login, send_task, start_updater, stop_updater, config, set_domain, \
    set_game_id, send_code_main, send_code_bonus, send_coords, set_login, set_password, set_channel_name, start_channel, \
    stop_channel, set_updater_delay, send_all_sectors, send_all_helps, send_last_help, send_all_bonuses, join, \
    reset_join, send_task_images, enable_codes, disable_codes, start_session, send_auth_messages, send_unclosed_bonuses, \
    send_live_locations, stop_live_locations, edit_live_locations, add_custom_live_locations
from MainClasses import MainVars
from TaskMathodMap import TaskMethodMap
from UpdaterMethods import updater

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
