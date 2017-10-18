# -*- coding: utf-8 -*-
import threading
from BotService import run_app
from MainMethods import start, stop, login, send_task, start_updater, stop_updater, config
from MainThreadVars import MainVars
from Updater import updater

main_vars = MainVars()

try:
    th_flask = threading.Thread(name='th_flask', target=run_app(main_vars.bot, main_vars).run, args=('0.0.0.0', 443, False))
    th_flask.start()
except Exception:
    main_vars.bot.send_message(45839899, 'Exception в main - не удалось запустить Flask')

while True:
    for task in main_vars.task_queue:
        if task['task_type'] == 'start':
            try:
                start(task['chat_id'], main_vars.bot, main_vars.sessions_dict)
                main_vars.task_queue.remove(task)
            except Exception:
                main_vars.bot.send_message(task['chat_id'], 'Exception в main - не удалось обработать команду start')
        if task['task_type'] == 'stop':
            stop(task['chat_id'], main_vars.bot, main_vars.sessions_dict[task['chat_id']])
            main_vars.task_queue.remove(task)
        if task['task_type'] == 'config':
            try:
                config(task['chat_id'], main_vars.bot, main_vars.sessions_dict[task['chat_id']])
                main_vars.task_queue.remove(task)
            except Exception:
                main_vars.bot.send_message(task['chat_id'], 'Exception в main - не удалось обработать команду config')
        if task['task_type'] == 'login':
            login(task['chat_id'], main_vars.bot, main_vars.sessions_dict[task['chat_id']])
            main_vars.task_queue.remove(task)
        if task['task_type'] == 'send_task':
            send_task(task['chat_id'], main_vars.bot, main_vars.sessions_dict[task['chat_id']])
            main_vars.task_queue.remove(task)
        if task['task_type'] == 'start_updater':
            start_updater(task['chat_id'], main_vars.bot, main_vars)
            main_vars.task_queue.remove(task)
        if task['task_type'] == 'updater':
            updater(task['chat_id'], main_vars.bot, main_vars.sessions_dict[task['chat_id']])
            main_vars.task_queue.remove(task)
        if task['task_type'] == 'stop_updater':
            stop_updater(main_vars.sessions_dict[task['chat_id']])
            main_vars.task_queue.remove(task)
