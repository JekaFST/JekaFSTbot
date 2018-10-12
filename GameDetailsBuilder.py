# -*- coding: utf-8 -*-
from ExceptionHandler import ExceptionHandler
from DBMethods import DB
from GameDetailsBuilderMethods import GoogleDocConnection, ENConnection, make_help_data_and_url, make_bonus_data_and_url, \
    make_sector_data_and_url, make_penalty_help_data_and_url, make_task_data_and_url, parse_level_page
from time import sleep


@ExceptionHandler.game_details_builder_exception
def game_details_builder(google_sheets_id, launch_id):
    google_doc_connection = GoogleDocConnection(google_sheets_id)
    login, password, domain, gameid = google_doc_connection.get_setup()
    if 'demo' not in domain and gameid not in DB.get_gameids_for_builder_list():
        return 'Заполнение данной игры не разрешено. Напишите @JekaFST в телеграмме для получения разрешения'
    en_connection = ENConnection(domain, login, password, gameid)

    for i, level_row in enumerate(google_doc_connection.get_cleanup_level_rows()):
        level_page = en_connection.get_level_page(level_row[4])
        sectors_to_del, helps_to_del, bonuses_to_del, pen_helps_to_del = parse_level_page(level_row, level_page)
        for help_to_del in helps_to_del:
            params = {
                'gid': gameid,
                'action': 'PromptDelete',
                'prid': help_to_del,
                'level': level_row[4]
            }
            en_connection.delete_en_object(params, 'help')

        for bonus_to_del in bonuses_to_del:
            params = {
                'gid': gameid,
                'action': 'delete',
                'bonus': bonus_to_del,
                'level': level_row[4]
            }
            en_connection.delete_en_object(params, 'bonus')

        for pen_help_to_del in pen_helps_to_del:
            params = {
                'gid': gameid,
                'action': 'PromptDelete',
                'prid': pen_help_to_del,
                'level': level_row[4],
                'penalty': '1'
            }
            en_connection.delete_en_object(params, 'pen_help')

    for i, help in enumerate(google_doc_connection.get_helps()):
        if i % 30 == 0:
            sleep(5)
        help_data, help_url, params = make_help_data_and_url(help, domain, gameid)
        en_connection.create_en_object(help_url, help_data, 'help', params)

    for i, bonus in enumerate(google_doc_connection.get_bonuses()):
        if i % 30 == 0:
            sleep(5)
        bonus_data, bonus_url, params = make_bonus_data_and_url(bonus, domain, gameid, en_connection.level_ids_dict)
        en_connection.create_en_object(bonus_url, bonus_data, 'bonus', params)

    for i, sector in enumerate(google_doc_connection.get_sectors()):
        if i % 30 == 0:
            sleep(5)
        sector_data, sector_url, params = make_sector_data_and_url(sector, domain, gameid)
        en_connection.create_en_object(sector_url, sector_data, 'sector', params)

    for i, penalty_help in enumerate(google_doc_connection.get_penalty_helps()):
        if i % 30 == 0:
            sleep(5)
        pen_help_data, pen_help_url, params = make_penalty_help_data_and_url(penalty_help, domain, gameid)
        en_connection.create_en_object(pen_help_url, pen_help_data, 'PenaltyHelp', params)

    for i, task in enumerate(google_doc_connection.get_tasks()):
        if i % 30 == 0:
            sleep(5)
        task_data, task_url, params = make_task_data_and_url(task, domain, gameid)
        en_connection.create_en_object(task_url, task_data, 'task', params)

    return 'Успех. Проверьте правильность переноса данных в движок.'
