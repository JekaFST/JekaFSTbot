# -*- coding: utf-8 -*-
import threading
from BotService import run_app
from MainMethods import start, stop, login, send_task, start_updater, stop_updater, config, set_domain, \
    set_game_id, send_code_main, send_code_bonus, send_coords, set_login, set_password, set_channel_name, start_channel, \
    stop_channel, set_updater_delay, send_all_sectors, send_all_helps, send_last_help, send_all_bonuses
from MainThreadVars import MainVars
from UpdaterMethods import updater

main_vars = MainVars()

try:
    th_flask = threading.Thread(name='th_flask', target=run_app(main_vars.bot, main_vars).run, args=('0.0.0.0', 443, False))
    th_flask.start()
except Exception:
    main_vars.bot.send_message(45839899, 'Exception в main - не удалось запустить Flask')

while True:
    if main_vars.id >= 2147483000:
        main_vars.id = 0
    for task in main_vars.task_queue:

        # Tasks to start & stop bot, get session config
        if task['task_type'] == 'start':
            try:
                start(task['chat_id'], main_vars.bot, main_vars.sessions_dict)
            except Exception:
                main_vars.bot.send_message(task['chat_id'], 'Exception в main - не удалось обработать команду start')
            main_vars.task_queue.remove(task)
        if task['task_type'] == 'stop':
            if not task['chat_id'] in main_vars.sessions_dict.keys():
                main_vars.bot.send_message(task['chat_id'],
                                           'Для данного чата не создана сессия. Для создания введите команду /start')
                main_vars.task_queue.remove(task)
                continue
            try:
                stop(task['chat_id'], main_vars.bot, main_vars.sessions_dict[task['chat_id']])
            except Exception:
                main_vars.bot.send_message(task['chat_id'], 'Exception в main - не удалось обработать команду stop')
            main_vars.task_queue.remove(task)
        if task['task_type'] == 'config':
            if not task['chat_id'] in main_vars.sessions_dict.keys():
                main_vars.bot.send_message(task['chat_id'],
                                           'Для данного чата не создана сессия. Для создания введите команду /start')
                main_vars.task_queue.remove(task)
                continue
            try:
                config(task['chat_id'], main_vars.bot, main_vars.sessions_dict[task['chat_id']])
            except Exception:
                main_vars.bot.send_message(task['chat_id'], 'Exception в main - не удалось обработать команду config')
            main_vars.task_queue.remove(task)

        # Tasks to set session config
        if task['task_type'] == 'login':
            if not task['chat_id'] in main_vars.sessions_dict.keys():
                main_vars.bot.send_message(task['chat_id'],
                                           'Для данного чата не создана сессия. Для создания введите команду /start')
                main_vars.task_queue.remove(task)
                continue
            try:
                set_login(task['chat_id'], main_vars.bot, main_vars.sessions_dict[task['chat_id']], task['new_login'])
            except Exception:
                main_vars.bot.send_message(task['chat_id'], 'Exception в main - не удалось обработать команду set_login')
            main_vars.task_queue.remove(task)
        if task['task_type'] == 'password':
            if not task['chat_id'] in main_vars.sessions_dict.keys():
                main_vars.bot.send_message(task['chat_id'],
                                           'Для данного чата не создана сессия. Для создания введите команду /start')
                main_vars.task_queue.remove(task)
                continue
            try:
                set_password(task['chat_id'], main_vars.bot, main_vars.sessions_dict[task['chat_id']],
                             task['new_password'])
            except Exception:
                main_vars.bot.send_message(task['chat_id'],
                                           'Exception в main - не удалось обработать команду set_password')
            main_vars.task_queue.remove(task)
        if task['task_type'] == 'domain':
            if not task['chat_id'] in main_vars.sessions_dict.keys():
                main_vars.bot.send_message(task['chat_id'],
                                           'Для данного чата не создана сессия. Для создания введите команду /start')
                main_vars.task_queue.remove(task)
                continue
            try:
                set_domain(task['chat_id'], main_vars.bot, main_vars.sessions_dict[task['chat_id']], task['new_domain'])
            except Exception:
                main_vars.bot.send_message(task['chat_id'], 'Exception в main - не удалось обработать команду set_domain')
            main_vars.task_queue.remove(task)
        if task['task_type'] == 'game_id':
            if not task['chat_id'] in main_vars.sessions_dict.keys():
                main_vars.bot.send_message(task['chat_id'],
                                           'Для данного чата не создана сессия. Для создания введите команду /start')
                main_vars.task_queue.remove(task)
                continue
            try:
                set_game_id(task['chat_id'], main_vars.bot, main_vars.sessions_dict[task['chat_id']], task['new_game_id'])
            except Exception:
                main_vars.bot.send_message(task['chat_id'],
                                           'Exception в main - не удалось обработать команду set_game_id')
            main_vars.task_queue.remove(task)

        # Task to login to encounter
        if task['task_type'] == 'login_to_en':
            if not task['chat_id'] in main_vars.sessions_dict.keys():
                main_vars.bot.send_message(task['chat_id'],
                                           'Для данного чата не создана сессия. Для создания введите команду /start')
                main_vars.task_queue.remove(task)
                continue
            try:
                login(task['chat_id'], main_vars.bot, main_vars.sessions_dict[task['chat_id']])
            except Exception:
                main_vars.bot.send_message(task['chat_id'], 'Exception в main - не удалось обработать команду login')
            main_vars.task_queue.remove(task)

        # Tasks to get some level info
        if task['task_type'] == 'send_task':
            if not task['chat_id'] in main_vars.sessions_dict.keys():
                main_vars.bot.send_message(task['chat_id'],
                                           'Для данного чата не создана сессия. Для создания введите команду /start')
                main_vars.task_queue.remove(task)
                continue
            try:
                send_task(task['chat_id'], main_vars.bot, main_vars.sessions_dict[task['chat_id']])
            except Exception:
                main_vars.bot.send_message(task['chat_id'], 'Exception в main - не удалось обработать команду send_task')
            main_vars.task_queue.remove(task)
        if task['task_type'] == 'send_sectors':
            if not task['chat_id'] in main_vars.sessions_dict.keys():
                main_vars.bot.send_message(task['chat_id'],
                                           'Для данного чата не создана сессия. Для создания введите команду /start')
                main_vars.task_queue.remove(task)
                continue
            try:
                send_all_sectors(task['chat_id'], main_vars.bot, main_vars.sessions_dict[task['chat_id']])
            except Exception:
                main_vars.bot.send_message(task['chat_id'],
                                           'Exception в main - не удалось обработать команду send_all_sectors')
            main_vars.task_queue.remove(task)
        if task['task_type'] == 'send_helps':
            if not task['chat_id'] in main_vars.sessions_dict.keys():
                main_vars.bot.send_message(task['chat_id'],
                                           'Для данного чата не создана сессия. Для создания введите команду /start')
                main_vars.task_queue.remove(task)
                continue
            try:
                send_all_helps(task['chat_id'], main_vars.bot, main_vars.sessions_dict[task['chat_id']])
            except Exception:
                main_vars.bot.send_message(task['chat_id'],
                                           'Exception в main - не удалось обработать команду send_all_helps')
            main_vars.task_queue.remove(task)
        if task['task_type'] == 'send_last_help':
            if not task['chat_id'] in main_vars.sessions_dict.keys():
                main_vars.bot.send_message(task['chat_id'],
                                           'Для данного чата не создана сессия. Для создания введите команду /start')
                main_vars.task_queue.remove(task)
                continue
            try:
                send_last_help(task['chat_id'], main_vars.bot, main_vars.sessions_dict[task['chat_id']])
            except Exception:
                main_vars.bot.send_message(task['chat_id'],
                                           'Exception в main - не удалось обработать команду send_last_helps')
            main_vars.task_queue.remove(task)
        if task['task_type'] == 'send_bonuses':
            if not task['chat_id'] in main_vars.sessions_dict.keys():
                main_vars.bot.send_message(task['chat_id'],
                                           'Для данного чата не создана сессия. Для создания введите команду /start')
                main_vars.task_queue.remove(task)
                continue
            try:
                send_all_bonuses(task['chat_id'], main_vars.bot, main_vars.sessions_dict[task['chat_id']])
            except Exception:
                main_vars.bot.send_message(task['chat_id'],
                                           'Exception в main - не удалось обработать команду send_all_bonuses')
            main_vars.task_queue.remove(task)

        # Tasks to manage updater
        if task['task_type'] == 'start_updater':
            if not task['chat_id'] in main_vars.sessions_dict.keys():
                main_vars.bot.send_message(task['chat_id'],
                                           'Для данного чата не создана сессия. Для создания введите команду /start')
                main_vars.task_queue.remove(task)
                continue
            try:
                start_updater(task['chat_id'], main_vars.bot, main_vars)
            except Exception:
                main_vars.bot.send_message(task['chat_id'],
                                           'Exception в main - не удалось обработать команду start_updater')
            main_vars.task_queue.remove(task)
        if task['task_type'] == 'updater':
            if not task['chat_id'] in main_vars.sessions_dict.keys():
                main_vars.bot.send_message(task['chat_id'],
                                           'Для данного чата не создана сессия. Для создания введите команду /start')
                main_vars.task_queue.remove(task)
                continue
            try:
                updater(task['chat_id'], main_vars.bot, main_vars.sessions_dict[task['chat_id']])
            except Exception:
                main_vars.bot.send_message(task['chat_id'], 'Exception в main - не удалось обработать команду updater')
            main_vars.task_queue.remove(task)
        if task['task_type'] == 'delay':
            if not task['chat_id'] in main_vars.sessions_dict.keys():
                main_vars.bot.send_message(task['chat_id'],
                                           'Для данного чата не создана сессия. Для создания введите команду /start')
                main_vars.task_queue.remove(task)
                continue
            try:
                set_updater_delay(task['chat_id'], main_vars.bot, main_vars.sessions_dict[task['chat_id']],
                                  task['new_delay'])
            except Exception:
                main_vars.bot.send_message(task['chat_id'],
                                           'Exception в main - не удалось обработать команду set_updater_delay')
            main_vars.task_queue.remove(task)
        if task['task_type'] == 'stop_updater':
            if not task['chat_id'] in main_vars.sessions_dict.keys():
                main_vars.bot.send_message(task['chat_id'],
                                           'Для данного чата не создана сессия. Для создания введите команду /start')
                main_vars.task_queue.remove(task)
                continue
            try:
                stop_updater(main_vars.sessions_dict[task['chat_id']])
            except Exception:
                main_vars.bot.send_message(task['chat_id'],
                                           'Exception в main - не удалось обработать команду stop_updater')
            main_vars.task_queue.remove(task)

        # Tasks to manage re-posting to channel
        if task['task_type'] == 'channel_name':
            if not task['chat_id'] in main_vars.sessions_dict.keys():
                main_vars.bot.send_message(task['chat_id'],
                                           'Для данного чата не создана сессия. Для создания введите команду /start')
                main_vars.task_queue.remove(task)
                continue
            try:
                set_channel_name(task['chat_id'], main_vars.bot, main_vars.sessions_dict[task['chat_id']],
                                 task['new_channel_name'])
            except Exception:
                main_vars.bot.send_message(task['chat_id'],
                                           'Exception в main - не удалось обработать команду set_channel_name')
            main_vars.task_queue.remove(task)
        if task['task_type'] == 'start_channel':
            if not task['chat_id'] in main_vars.sessions_dict.keys():
                main_vars.bot.send_message(task['chat_id'],
                                           'Для данного чата не создана сессия. Для создания введите команду /start')
                main_vars.task_queue.remove(task)
                continue
            try:
                start_channel(task['chat_id'], main_vars.bot, main_vars.sessions_dict[task['chat_id']])
            except Exception:
                main_vars.bot.send_message(task['chat_id'],
                                           'Exception в main - не удалось обработать команду start_channel')
            main_vars.task_queue.remove(task)
        if task['task_type'] == 'stop_channel':
            if not task['chat_id'] in main_vars.sessions_dict.keys():
                main_vars.bot.send_message(task['chat_id'],
                                           'Для данного чата не создана сессия. Для создания введите команду /start')
                main_vars.task_queue.remove(task)
                continue
            try:
                stop_channel(task['chat_id'], main_vars.bot, main_vars.sessions_dict[task['chat_id']])
            except Exception:
                main_vars.bot.send_message(task['chat_id'],
                                           'Exception в main - не удалось обработать команду stop_channel')
            main_vars.task_queue.remove(task)

        # Tasks to send codes & coords
        if task['task_type'] == 'send_code_main':
            if not task['chat_id'] in main_vars.sessions_dict.keys():
                main_vars.bot.send_message(task['chat_id'],
                                           'Для данного чата не создана сессия. Для создания введите команду /start')
                main_vars.task_queue.remove(task)
                continue
            try:
                send_code_main(task['chat_id'], main_vars.bot, main_vars.sessions_dict[task['chat_id']],
                               task['message_id'], task['code'])
            except Exception:
                main_vars.bot.send_message(task['chat_id'],
                                           'Exception в main - не удалось обработать команду send_code_main')
            main_vars.task_queue.remove(task)
        if task['task_type'] == 'send_code_bonus':
            if not task['chat_id'] in main_vars.sessions_dict.keys():
                main_vars.bot.send_message(task['chat_id'],
                                           'Для данного чата не создана сессия. Для создания введите команду /start')
                main_vars.task_queue.remove(task)
                continue
            try:
                send_code_bonus(task['chat_id'], main_vars.bot, main_vars.sessions_dict[task['chat_id']],
                                task['message_id'], task['code'])
            except Exception:
                main_vars.bot.send_message(task['chat_id'],
                                           'Exception в main - не удалось обработать команду send_code_bonus')
            main_vars.task_queue.remove(task)
        if task['task_type'] == 'send_coords':
            if not task['chat_id'] in main_vars.sessions_dict.keys():
                main_vars.bot.send_message(task['chat_id'],
                                           'Для данного чата не создана сессия. Для создания введите команду /start')
                main_vars.task_queue.remove(task)
                continue
            try:
                send_coords(task['chat_id'], main_vars.bot, main_vars.sessions_dict[task['chat_id']], task['coords'])
            except Exception:
                main_vars.bot.send_message(task['chat_id'],
                                           'Exception в main - не удалось обработать команду send_coords')
            main_vars.task_queue.remove(task)
