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

    # # Updater task
        # if task['task_type'] == 'updater':
        #     if not task['chat_id'] in main_vars.sessions_dict.keys():
        #         bot.send_message(task['chat_id'],
        #                                    'Для данного чата не создана сессия. Для создания введите команду /start')
        #         main_vars.task_queue.remove(task)
        #         continue
        #     try:
        #         updater(task['chat_id'], bot, main_vars.sessions_dict[task['chat_id']], main_vars.updaters_dict)
        #         main_vars.task_queue.remove(task)
        #     except Exception:
        #         bot.send_message(task['chat_id'], 'Exception в main - не удалось обработать команду updater')
        #         main_vars.task_queue.remove(task)
        #         main_vars.sessions_dict[task['chat_id']].put_updater_task = True
        #     continue
        #
        # # Tasks to send codes & coords
        # if task['task_type'] == 'send_code_main':
        #     if task['chat_id']:
        #         if not task['chat_id'] in main_vars.sessions_dict.keys():
        #             bot.send_message(task['chat_id'],
        #                                        'Для данного чата не создана сессия. Для создания введите команду /start')
        #             main_vars.task_queue.remove(task)
        #             continue
        #         chat_id = task['chat_id']
        #         session = main_vars.sessions_dict[task['chat_id']]
        #     else:
        #         if not DB.get_main_chat_id_via_add(task['additional_chat_id']) in main_vars.sessions_dict.keys():
        #             bot.send_message(task['chat_id'],
        #                                        'Для данного дополнительного чата не создана (или удалена) сессия')
        #             continue
        #         chat_id = task['additional_chat_id']
        #         session = main_vars.sessions_dict[main_vars.additional_ids[task['additional_chat_id']]]
        #     try:
        #         send_code_main(chat_id, bot, session, task['message_id'], task['code'])
        #     except Exception:
        #         bot.send_message(task['chat_id'],
        #                                    'Exception в main - не удалось обработать команду send_code_main')
        #     main_vars.task_queue.remove(task)
        #     continue
        #
        # if task['task_type'] == 'send_code_bonus':
        #     if task['chat_id']:
        #         if not task['chat_id'] in main_vars.sessions_dict.keys():
        #             bot.send_message(task['chat_id'],
        #                                        'Для данного чата не создана сессия. Для создания введите команду /start')
        #             main_vars.task_queue.remove(task)
        #             continue
        #         chat_id = task['chat_id']
        #         session = main_vars.sessions_dict[task['chat_id']]
        #     else:
        #         if not DB.get_main_chat_id_via_add(task['additional_chat_id']) in main_vars.sessions_dict.keys():
        #             bot.send_message(task['chat_id'],
        #                                        'Для данного дополнительного чата не создана (или удалена) сессия')
        #             continue
        #         chat_id = task['additional_chat_id']
        #         session = main_vars.sessions_dict[main_vars.additional_ids[task['additional_chat_id']]]
        #     try:
        #         send_code_bonus(chat_id, bot, session, task['message_id'], task['code'])
        #     except Exception:
        #         bot.send_message(task['chat_id'],
        #                                    'Exception в main - не удалось обработать команду send_code_bonus')
        #     main_vars.task_queue.remove(task)
        #     continue
        #
        # if task['task_type'] == 'send_coords':
        #     try:
        #         send_coords(task['chat_id'], bot, task['coords'])
        #     except Exception:
        #         bot.send_message(task['chat_id'],
        #                                    'Exception в main - не удалось обработать команду send_coords')
        #     main_vars.task_queue.remove(task)
        #     continue
        #
        # # live_location tasks
        # if task['task_type'] == 'live_location':
        #     if task['chat_id']:
        #         if not task['chat_id'] in main_vars.sessions_dict.keys():
        #             bot.send_message(task['chat_id'],
        #                                        'Для данного чата не создана сессия. Для создания введите команду /start')
        #             main_vars.task_queue.remove(task)
        #             continue
        #         chat_id = task['chat_id']
        #         session = main_vars.sessions_dict[task['chat_id']]
        #     else:
        #         if not DB.get_main_chat_id_via_add(task['additional_chat_id']) in main_vars.sessions_dict.keys():
        #             bot.send_message(task['chat_id'],
        #                                        'Для данного дополнительного чата не создана (или удалена) сессия')
        #             continue
        #         chat_id = main_vars.additional_ids[task['additional_chat_id']]
        #         session = main_vars.sessions_dict[main_vars.additional_ids[task['additional_chat_id']]]
        #     try:
        #         send_live_locations(chat_id, bot, session, task['coords'], task['duration'])
        #     except Exception:
        #         bot.send_message(task['chat_id'],
        #                                    'Exception в main - не удалось обработать команду send_live_location')
        #     main_vars.task_queue.remove(task)
        #     continue
        #
        # if task['task_type'] == 'stop_live_location':
        #     if task['chat_id']:
        #         if not task['chat_id'] in main_vars.sessions_dict.keys():
        #             bot.send_message(task['chat_id'],
        #                                        'Для данного чата не создана сессия. Для создания введите команду /start')
        #             main_vars.task_queue.remove(task)
        #             continue
        #         chat_id = task['chat_id']
        #         session = main_vars.sessions_dict[task['chat_id']]
        #     else:
        #         if not DB.get_main_chat_id_via_add(task['additional_chat_id']) in main_vars.sessions_dict.keys():
        #             bot.send_message(task['chat_id'],
        #                                        'Для данного дополнительного чата не создана (или удалена) сессия')
        #             continue
        #         chat_id = main_vars.additional_ids[task['additional_chat_id']]
        #         session = main_vars.sessions_dict[main_vars.additional_ids[task['additional_chat_id']]]
        #     try:
        #         stop_live_locations(chat_id, bot, session, task['point'])
        #     except Exception:
        #         bot.send_message(task['chat_id'],
        #                                    'Exception в main - не удалось обработать команду stop_live_location')
        #     main_vars.task_queue.remove(task)
        #     continue
        #
        # if task['task_type'] == 'edit_live_location':
        #     if task['chat_id']:
        #         if not task['chat_id'] in main_vars.sessions_dict.keys():
        #             bot.send_message(task['chat_id'],
        #                                        'Для данного чата не создана сессия. Для создания введите команду /start')
        #             main_vars.task_queue.remove(task)
        #             continue
        #         chat_id = task['chat_id']
        #         session = main_vars.sessions_dict[task['chat_id']]
        #     else:
        #         if not DB.get_main_chat_id_via_add(task['additional_chat_id']) in main_vars.sessions_dict.keys():
        #             bot.send_message(task['chat_id'],
        #                                        'Для данного дополнительного чата не создана (или удалена) сессия')
        #             continue
        #         chat_id = main_vars.additional_ids[task['additional_chat_id']]
        #         session = main_vars.sessions_dict[main_vars.additional_ids[task['additional_chat_id']]]
        #     try:
        #         edit_live_locations(chat_id, bot, session, task['point'], task['coords'])
        #     except Exception:
        #         bot.send_message(task['chat_id'],
        #                                    'Exception в main - не удалось обработать команду edit_live_location')
        #     main_vars.task_queue.remove(task)
        #     continue
        #
        # if task['task_type'] == 'add_points_ll':
        #     if task['chat_id']:
        #         if not task['chat_id'] in main_vars.sessions_dict.keys():
        #             bot.send_message(task['chat_id'],
        #                                        'Для данного чата не создана сессия. Для создания введите команду /start')
        #             main_vars.task_queue.remove(task)
        #             continue
        #         chat_id = task['chat_id']
        #         session = main_vars.sessions_dict[task['chat_id']]
        #     else:
        #         if not DB.get_main_chat_id_via_add(task['additional_chat_id']) in main_vars.sessions_dict.keys():
        #             bot.send_message(task['chat_id'],
        #                                        'Для данного дополнительного чата не создана (или удалена) сессия')
        #             continue
        #         chat_id = main_vars.additional_ids[task['additional_chat_id']]
        #         session = main_vars.sessions_dict[main_vars.additional_ids[task['additional_chat_id']]]
        #     try:
        #         add_custom_live_locations(chat_id, bot, session, task['points_dict'], task['duration'])
        #     except Exception:
        #         bot.send_message(task['chat_id'],
        #                                    'Exception в main - не удалось обработать команду add_custom_live_location')
        #     main_vars.task_queue.remove(task)
        #     continue