# -*- coding: utf-8 -*-
import threading
from BotService import run_app
from MainMethods import start, stop, login, send_task
from MainThreadVars import MainVars

main_vars = MainVars()
th_flask = threading.Thread(name='th_flask', target=run_app(main_vars.bot, main_vars).run, args=('0.0.0.0', 443, False))
th_flask.start()


while True:
    for task in main_vars.task_queue:
        if task['task_type'] == 'start':
            start(task['chat_id'], main_vars)
            main_vars.task_queue.remove(task)
        if task['task_type'] == 'stop':
            stop(task['chat_id'], main_vars)
            main_vars.task_queue.remove(task)
        if task['task_type'] == 'login':
            login(task['chat_id'], main_vars)
            main_vars.task_queue.remove(task)
        if task['task_type'] == 'send_task':
            send_task(task['chat_id'], main_vars)
            main_vars.task_queue.remove(task)
