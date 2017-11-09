# -*- coding: utf-8 -*-
import threading
from BotService import run_app
from MainMethods import start, stop_session, login, send_task, start_updater, stop_updater, config, set_domain, \
    set_game_id, send_code_main, send_code_bonus, send_coords, set_login, set_password, set_channel_name, start_channel, \
    stop_channel, set_updater_delay, send_all_sectors, send_all_helps, send_last_help, send_all_bonuses, join, \
    reset_join, send_task_images, enable_codes, disable_codes, start_session, send_auth_messages, send_unclosed_bonuses
from MainThreadVars import MainVars
from UpdaterMethods import updater

main_vars = MainVars()

try:
    th_flask = threading.Thread(name='th_flask', target=run_app(main_vars.bot, main_vars).run, args=('0.0.0.0', 443, False))
    th_flask.start()
except Exception:
    main_vars.bot.send_message(45839899, 'Exception в main - не удалось запустить Flask')

while True:
    for task in main_vars.task_queue:

        # Updater task
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
            main_vars.sessions_dict[task['chat_id']].put_updater_task = True
            continue

        # Tasks to send codes & coords
        if task['task_type'] == 'send_code_main':
            if task['chat_id']:
                if not task['chat_id'] in main_vars.sessions_dict.keys():
                    main_vars.bot.send_message(task['chat_id'],
                                               'Для данного чата не создана сессия. Для создания введите команду /start')
                    main_vars.task_queue.remove(task)
                    continue
                chat_id = task['chat_id']
                session = main_vars.sessions_dict[task['chat_id']]
            else:
                if not main_vars.additional_ids[task['additional_chat_id']] in main_vars.sessions_dict.keys():
                    main_vars.bot.send_message(task['chat_id'],
                                               'Для данного дополнительного чата не создана (или удалена) сессия')
                    continue
                chat_id = task['additional_chat_id']
                session = main_vars.sessions_dict[main_vars.additional_ids[task['additional_chat_id']]]
            try:
                send_code_main(chat_id, main_vars.bot, session, task['message_id'], task['code'])
            except Exception:
                main_vars.bot.send_message(task['chat_id'],
                                           'Exception в main - не удалось обработать команду send_code_main')
            main_vars.task_queue.remove(task)
            continue

        if task['task_type'] == 'send_code_bonus':
            if task['chat_id']:
                if not task['chat_id'] in main_vars.sessions_dict.keys():
                    main_vars.bot.send_message(task['chat_id'],
                                               'Для данного чата не создана сессия. Для создания введите команду /start')
                    main_vars.task_queue.remove(task)
                    continue
                chat_id = task['chat_id']
                session = main_vars.sessions_dict[task['chat_id']]
            else:
                if not main_vars.additional_ids[task['additional_chat_id']] in main_vars.sessions_dict.keys():
                    main_vars.bot.send_message(task['chat_id'],
                                               'Для данного дополнительного чата не создана (или удалена) сессия')
                    continue
                chat_id = task['additional_chat_id']
                session = main_vars.sessions_dict[main_vars.additional_ids[task['additional_chat_id']]]
            try:
                send_code_bonus(chat_id, main_vars.bot, session, task['message_id'], task['code'])
            except Exception:
                main_vars.bot.send_message(task['chat_id'],
                                           'Exception в main - не удалось обработать команду send_code_bonus')
            main_vars.task_queue.remove(task)
            continue

        if task['task_type'] == 'send_coords':
            if not task['chat_id'] in main_vars.sessions_dict.keys():
                main_vars.bot.send_message(task['chat_id'],
                                           'Для данного чата не создана сессия. Для создания введите команду /start')
                main_vars.task_queue.remove(task)
                continue
            try:
                send_coords(task['chat_id'], main_vars.bot, main_vars.sessions_dict[task['chat_id']],
                            task['coords'])
            except Exception:
                main_vars.bot.send_message(task['chat_id'],
                                           'Exception в main - не удалось обработать команду send_coords')
            main_vars.task_queue.remove(task)
            continue

        # Tasks to get level info
        if task['task_type'] == 'send_task':
            if task['chat_id']:
                if not task['chat_id'] in main_vars.sessions_dict.keys():
                    main_vars.bot.send_message(task['chat_id'],
                                               'Для данного чата не создана сессия. Для создания введите команду /start')
                    main_vars.task_queue.remove(task)
                    continue
                chat_id = task['chat_id']
                session = main_vars.sessions_dict[task['chat_id']]
            else:
                if not main_vars.additional_ids[task['additional_chat_id']] in main_vars.sessions_dict.keys():
                    main_vars.bot.send_message(task['chat_id'],
                                               'Для данного дополнительного чата не создана (или удалена) сессия')
                    continue
                chat_id = task['additional_chat_id']
                session = main_vars.sessions_dict[main_vars.additional_ids[task['additional_chat_id']]]
            try:
                send_task(chat_id, main_vars.bot, session, task['storm_level'])
            except Exception:
                main_vars.bot.send_message(task['chat_id'], 'Exception в main - не удалось обработать команду send_task')
            main_vars.task_queue.remove(task)
            continue

        if task['task_type'] == 'task_images':
            if not task['chat_id'] in main_vars.sessions_dict.keys():
                main_vars.bot.send_message(task['chat_id'],
                                           'Для данного чата не создана сессия. Для создания введите команду /start')
                main_vars.task_queue.remove(task)
                continue
            try:
                send_task_images(task['chat_id'], main_vars.bot, main_vars.sessions_dict[task['chat_id']])
            except Exception:
                main_vars.bot.send_message(task['chat_id'],
                                           'Exception в main - не удалось обработать команду send_task_images')
            main_vars.task_queue.remove(task)
            continue

        if task['task_type'] == 'send_sectors':
            if task['chat_id']:
                if not task['chat_id'] in main_vars.sessions_dict.keys():
                    main_vars.bot.send_message(task['chat_id'],
                                               'Для данного чата не создана сессия. Для создания введите команду /start')
                    main_vars.task_queue.remove(task)
                    continue
                chat_id = task['chat_id']
                session = main_vars.sessions_dict[task['chat_id']]
            else:
                if not main_vars.additional_ids[task['additional_chat_id']] in main_vars.sessions_dict.keys():
                    main_vars.bot.send_message(task['chat_id'],
                                               'Для данного дополнительного чата не создана (или удалена) сессия')
                    continue
                chat_id = task['additional_chat_id']
                session = main_vars.sessions_dict[main_vars.additional_ids[task['additional_chat_id']]]
            try:
                send_all_sectors(chat_id, main_vars.bot, session, task['storm_level'])
            except Exception:
                main_vars.bot.send_message(task['chat_id'],
                                           'Exception в main - не удалось обработать команду send_all_sectors')
            main_vars.task_queue.remove(task)
            continue

        if task['task_type'] == 'send_helps':
            if task['chat_id']:
                if not task['chat_id'] in main_vars.sessions_dict.keys():
                    main_vars.bot.send_message(task['chat_id'],
                                               'Для данного чата не создана сессия. Для создания введите команду /start')
                    main_vars.task_queue.remove(task)
                    continue
                chat_id = task['chat_id']
                session = main_vars.sessions_dict[task['chat_id']]
            else:
                if not main_vars.additional_ids[task['additional_chat_id']] in main_vars.sessions_dict.keys():
                    main_vars.bot.send_message(task['chat_id'],
                                               'Для данного дополнительного чата не создана (или удалена) сессия')
                    continue
                chat_id = task['additional_chat_id']
                session = main_vars.sessions_dict[main_vars.additional_ids[task['additional_chat_id']]]
            try:
                send_all_helps(chat_id, main_vars.bot, session, task['storm_level'])
            except Exception:
                main_vars.bot.send_message(task['chat_id'],
                                           'Exception в main - не удалось обработать команду send_all_helps')
            main_vars.task_queue.remove(task)
            continue

        if task['task_type'] == 'send_last_help':
            if task['chat_id']:
                if not task['chat_id'] in main_vars.sessions_dict.keys():
                    main_vars.bot.send_message(task['chat_id'],
                                               'Для данного чата не создана сессия. Для создания введите команду /start')
                    main_vars.task_queue.remove(task)
                    continue
                chat_id = task['chat_id']
                session = main_vars.sessions_dict[task['chat_id']]
            else:
                if not main_vars.additional_ids[task['additional_chat_id']] in main_vars.sessions_dict.keys():
                    main_vars.bot.send_message(task['chat_id'],
                                               'Для данного дополнительного чата не создана (или удалена) сессия')
                    continue
                chat_id = task['additional_chat_id']
                session = main_vars.sessions_dict[main_vars.additional_ids[task['additional_chat_id']]]
            try:
                send_last_help(chat_id, main_vars.bot, session, task['storm_level'])
            except Exception:
                main_vars.bot.send_message(task['chat_id'],
                                           'Exception в main - не удалось обработать команду send_last_helps')
            main_vars.task_queue.remove(task)
            continue

        if task['task_type'] == 'send_bonuses':
            if task['chat_id']:
                if not task['chat_id'] in main_vars.sessions_dict.keys():
                    main_vars.bot.send_message(task['chat_id'],
                                               'Для данного чата не создана сессия. Для создания введите команду /start')
                    main_vars.task_queue.remove(task)
                    continue
                chat_id = task['chat_id']
                session = main_vars.sessions_dict[task['chat_id']]
            else:
                if not main_vars.additional_ids[task['additional_chat_id']] in main_vars.sessions_dict.keys():
                    main_vars.bot.send_message(task['chat_id'],
                                               'Для данного дополнительного чата не создана (или удалена) сессия')
                    continue
                chat_id = task['additional_chat_id']
                session = main_vars.sessions_dict[main_vars.additional_ids[task['additional_chat_id']]]
            try:
                send_all_bonuses(chat_id, main_vars.bot, session)
            except Exception:
                main_vars.bot.send_message(task['chat_id'],
                                           'Exception в main - не удалось обработать команду send_all_bonuses')
            main_vars.task_queue.remove(task)
            continue

        if task['task_type'] == 'unclosed_bonuses':
            if task['chat_id']:
                if not task['chat_id'] in main_vars.sessions_dict.keys():
                    main_vars.bot.send_message(task['chat_id'],
                                               'Для данного чата не создана сессия. Для создания введите команду /start')
                    main_vars.task_queue.remove(task)
                    continue
                chat_id = task['chat_id']
                session = main_vars.sessions_dict[task['chat_id']]
            else:
                if not main_vars.additional_ids[task['additional_chat_id']] in main_vars.sessions_dict.keys():
                    main_vars.bot.send_message(task['chat_id'],
                                               'Для данного дополнительного чата не создана (или удалена) сессия')
                    continue
                chat_id = task['additional_chat_id']
                session = main_vars.sessions_dict[main_vars.additional_ids[task['additional_chat_id']]]
            try:
                send_unclosed_bonuses(chat_id, main_vars.bot, session)
            except Exception:
                main_vars.bot.send_message(task['chat_id'],
                                           'Exception в main - не удалось обработать команду send_unclosed_bonuses')
            main_vars.task_queue.remove(task)
            continue

        if task['task_type'] == 'send_messages':
            if task['chat_id']:
                if not task['chat_id'] in main_vars.sessions_dict.keys():
                    main_vars.bot.send_message(task['chat_id'],
                                               'Для данного чата не создана сессия. Для создания введите команду /start')
                    main_vars.task_queue.remove(task)
                    continue
                chat_id = task['chat_id']
                session = main_vars.sessions_dict[task['chat_id']]
            else:
                if not main_vars.additional_ids[task['additional_chat_id']] in main_vars.sessions_dict.keys():
                    main_vars.bot.send_message(task['chat_id'],
                                               'Для данного дополнительного чата не создана (или удалена) сессия')
                    continue
                chat_id = task['additional_chat_id']
                session = main_vars.sessions_dict[main_vars.additional_ids[task['additional_chat_id']]]
            try:
                send_auth_messages(chat_id, main_vars.bot, session)
            except Exception:
                main_vars.bot.send_message(task['chat_id'],
                                           'Exception в main - не удалось обработать команду send_auth_messages')
            main_vars.task_queue.remove(task)
            continue

        # Tasks to start & stop bot, get session config
        if task['task_type'] == 'start':
            try:
                start(task['chat_id'], main_vars.bot, main_vars.sessions_dict)
            except Exception:
                main_vars.bot.send_message(task['chat_id'], 'Exception в main - не удалось обработать команду start')
            main_vars.task_queue.remove(task)
            continue

        if task['task_type'] == 'start_session':
            if not task['chat_id'] in main_vars.sessions_dict.keys():
                main_vars.bot.send_message(task['chat_id'],
                                           'Для данного чата не создана сессия. Для создания введите команду /start')
                main_vars.task_queue.remove(task)
                continue
            try:
                start_session(task['chat_id'], main_vars.bot, main_vars.sessions_dict[task['chat_id']])
            except Exception:
                main_vars.bot.send_message(task['chat_id'], 'Exception в main - не удалось обработать команду start_session')
            main_vars.task_queue.remove(task)
            continue

        if task['task_type'] == 'stop_session':
            if not task['chat_id'] in main_vars.sessions_dict.keys():
                main_vars.bot.send_message(task['chat_id'],
                                           'Для данного чата не создана сессия. Для создания введите команду /start')
                main_vars.task_queue.remove(task)
                continue
            try:
                stop_session(task['chat_id'], main_vars.bot, main_vars.sessions_dict[task['chat_id']], main_vars.additional_ids)
            except Exception:
                main_vars.bot.send_message(task['chat_id'], 'Exception в main - не удалось обработать команду stop_session')
            main_vars.task_queue.remove(task)
            continue

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
            continue

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
            continue

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
            continue

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
            continue

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
            continue

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
            continue

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
            continue

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
            continue

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
            continue

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
            continue

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
            continue

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
            continue

        # Additional tasks to make bot more convenient
        if task['task_type'] == 'join':
            if task['additional_chat_id'] in main_vars.additional_ids.keys():
                main_vars.bot.send_message(task['chat_id'], 'У вас уже есть сессия, в рамках которой взаимодействие с '
                                                            'ботом настроено через личный чат. Для сброса введите /reset_join',
                                           reply_to_message_id=task['message_id'])
                main_vars.task_queue.remove(task)
                continue
            if not task['chat_id'] in main_vars.sessions_dict.keys():
                main_vars.bot.send_message(task['chat_id'],
                                           'Для данного чата не создана сессия. Для создания введите команду /start')
                main_vars.task_queue.remove(task)
                continue
            try:
                join(task['chat_id'], main_vars.bot, task['message_id'],
                     task['additional_chat_id'], main_vars.additional_ids)
            except Exception:
                main_vars.bot.send_message(task['chat_id'], 'Exception в main - не удалось обработать команду join')
            main_vars.task_queue.remove(task)
            continue

        if task['task_type'] == 'reset_join':
            if task['chat_id']:
                if not task['chat_id'] in main_vars.sessions_dict.keys():
                    main_vars.bot.send_message(task['chat_id'],
                                               'Для данного чата не создана сессия. Для создания введите команду /start')
                    main_vars.task_queue.remove(task)
                    continue
                chat_id = task['chat_id']
            else:
                if not main_vars.additional_ids[task['additional_chat_id']] in main_vars.sessions_dict.keys():
                    main_vars.bot.send_message(task['chat_id'],
                                               'Для данного дополнительного чата не создана (или удалена) сессия')
                    continue
                chat_id = task['additional_chat_id']
            try:
                reset_join(chat_id, main_vars.bot, task['message_id'],
                           task['additional_chat_id'], main_vars.additional_ids)
            except Exception:
                main_vars.bot.send_message(task['chat_id'], 'Exception в main - не удалось обработать команду reset_join')
            main_vars.task_queue.remove(task)
            continue

        if task['task_type'] == 'codes_on':
            if not task['chat_id'] in main_vars.sessions_dict.keys():
                main_vars.bot.send_message(task['chat_id'],
                                           'Для данного чата не создана сессия. Для создания введите команду /start')
                main_vars.task_queue.remove(task)
                continue
            try:
                enable_codes(task['chat_id'], main_vars.bot, main_vars.sessions_dict[task['chat_id']])
            except Exception:
                main_vars.bot.send_message(task['chat_id'],
                                           'Exception в main - не удалось обработать команду enable_codes')
            main_vars.task_queue.remove(task)
            continue

        if task['task_type'] == 'codes_off':
            if not task['chat_id'] in main_vars.sessions_dict.keys():
                main_vars.bot.send_message(task['chat_id'],
                                           'Для данного чата не создана сессия. Для создания введите команду /start')
                main_vars.task_queue.remove(task)
                continue
            try:
                disable_codes(task['chat_id'], main_vars.bot, main_vars.sessions_dict[task['chat_id']])
            except Exception:
                main_vars.bot.send_message(task['chat_id'],
                                           'Exception в main - не удалось обработать команду disable_codes')
            main_vars.task_queue.remove(task)
            continue
