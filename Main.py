# -*- coding: utf-8 -*-
import threading
from BotService import run_app
from MainMethods import start, stop, login, send_task, start_updater, stop_updater, config, set_domain, \
    set_game_id, send_code_main, send_code_bonus, send_coords, set_login, set_password, set_channel_name, start_channel, \
    stop_channel
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
            try:
                stop(task['chat_id'], main_vars.bot, main_vars.sessions_dict[task['chat_id']])
                main_vars.task_queue.remove(task)
            except Exception:
                main_vars.bot.send_message(task['chat_id'], 'Exception в main - не удалось обработать команду stop')
        if task['task_type'] == 'config':
            try:
                config(task['chat_id'], main_vars.bot, main_vars.sessions_dict[task['chat_id']])
                main_vars.task_queue.remove(task)
            except Exception:
                main_vars.bot.send_message(task['chat_id'], 'Exception в main - не удалось обработать команду config')
        if task['task_type'] == 'login':
            try:
                set_login(task['chat_id'], main_vars.bot, main_vars.sessions_dict[task['chat_id']], task['new_login'])
                main_vars.task_queue.remove(task)
            except Exception:
                main_vars.bot.send_message(task['chat_id'], 'Exception в main - не удалось обработать команду set_login')
        if task['task_type'] == 'password':
            try:
                set_password(task['chat_id'], main_vars.bot, main_vars.sessions_dict[task['chat_id']],
                             task['new_password'])
                main_vars.task_queue.remove(task)
            except Exception:
                main_vars.bot.send_message(task['chat_id'],
                                           'Exception в main - не удалось обработать команду set_password')
        if task['task_type'] == 'domain':
            try:
                set_domain(task['chat_id'], main_vars.bot, main_vars.sessions_dict[task['chat_id']], task['new_domain'])
                main_vars.task_queue.remove(task)
            except Exception:
                main_vars.bot.send_message(task['chat_id'], 'Exception в main - не удалось обработать команду set_domain')
        if task['task_type'] == 'game_id':
            try:
                set_game_id(task['chat_id'], main_vars.bot, main_vars.sessions_dict[task['chat_id']], task['new_game_id'])
                main_vars.task_queue.remove(task)
            except Exception:
                main_vars.bot.send_message(task['chat_id'],
                                           'Exception в main - не удалось обработать команду set_game_id')
        if task['task_type'] == 'login':
            try:
                login(task['chat_id'], main_vars.bot, main_vars.sessions_dict[task['chat_id']])
                main_vars.task_queue.remove(task)
            except Exception:
                main_vars.bot.send_message(task['chat_id'], 'Exception в main - не удалось обработать команду login')
        if task['task_type'] == 'send_task':
            try:
                send_task(task['chat_id'], main_vars.bot, main_vars.sessions_dict[task['chat_id']])
                main_vars.task_queue.remove(task)
            except Exception:
                main_vars.bot.send_message(task['chat_id'], 'Exception в main - не удалось обработать команду send_task')
        if task['task_type'] == 'start_updater':
            try:
                start_updater(task['chat_id'], main_vars.bot, main_vars)
                main_vars.task_queue.remove(task)
            except Exception:
                main_vars.bot.send_message(task['chat_id'], 'Exception в main - не удалось обработать команду start_updater')
        if task['task_type'] == 'updater':
            try:
                updater(task['chat_id'], main_vars.bot, main_vars.sessions_dict[task['chat_id']])
                main_vars.task_queue.remove(task)
            except Exception:
                main_vars.bot.send_message(task['chat_id'], 'Exception в main - не удалось обработать команду updater')
        if task['task_type'] == 'stop_updater':
            try:
                stop_updater(main_vars.sessions_dict[task['chat_id']])
                main_vars.task_queue.remove(task)
            except Exception:
                main_vars.bot.send_message(task['chat_id'], 'Exception в main - не удалось обработать команду stop_updater')
        if task['task_type'] == 'channel_name':
            try:
                set_channel_name(task['chat_id'], main_vars.bot, main_vars.sessions_dict[task['chat_id']],
                                 task['new_channel_name'])
                main_vars.task_queue.remove(task)
            except Exception:
                main_vars.bot.send_message(task['chat_id'],
                                           'Exception в main - не удалось обработать команду set_channel_name')
        if task['task_type'] == 'start_channel':
            try:
                start_channel(task['chat_id'], main_vars.bot, main_vars.sessions_dict[task['chat_id']])
                main_vars.task_queue.remove(task)
            except Exception:
                main_vars.bot.send_message(task['chat_id'],
                                           'Exception в main - не удалось обработать команду start_channel')
        if task['task_type'] == 'stop_channel':
            try:
                stop_channel(task['chat_id'], main_vars.bot, main_vars.sessions_dict[task['chat_id']])
                main_vars.task_queue.remove(task)
            except Exception:
                main_vars.bot.send_message(task['chat_id'],
                                           'Exception в main - не удалось обработать команду stop_channel')
        if task['task_type'] == 'send_code_main':
            try:
                send_code_main(task['chat_id'], main_vars.bot, main_vars.sessions_dict[task['chat_id']],
                               task['message_id'], task['code'])
                main_vars.task_queue.remove(task)
            except Exception:
                main_vars.bot.send_message(task['chat_id'],
                                           'Exception в main - не удалось обработать команду send_code_main')
        if task['task_type'] == 'send_code_bonus':
            try:
                send_code_bonus(task['chat_id'], main_vars.bot, main_vars.sessions_dict[task['chat_id']],
                                task['message_id'], task['code'])
                main_vars.task_queue.remove(task)
            except Exception:
                main_vars.bot.send_message(task['chat_id'],
                                           'Exception в main - не удалось обработать команду send_code_bonus')
        if task['task_type'] == 'send_coords':
            try:
                send_coords(task['chat_id'], main_vars.bot, main_vars.sessions_dict[task['chat_id']], task['coords'])
                main_vars.task_queue.remove(task)
            except Exception:
                main_vars.bot.send_message(task['chat_id'],
                                           'Exception в main - не удалось обработать команду send_coords')
