# -*- coding: utf-8 -*-
from ExceptionHandler import ExceptionHandler
from DBMethods import DB
from GameDetailsBuilderMethods import GoogleDocConnection, ENConnection, make_help_data_and_url, make_bonus_data_and_url, \
    make_sector_data_and_url, make_penalty_help_data_and_url, make_task_data_and_url, parse_level_page
from time import sleep

SOURCE_GAME_DATA = {
    'domain': 'http://demo.en.cx',
    'login': 'jekafst',
    'password': 'hjccbz1412',
    'gameid': '27201'
}
TARGET_GAME_DATA={
    'domain': 'http://demo.en.cx',
    'login': 'jekafst',
    'password': 'hjccbz1412',
    'gameid': '27201'
}


@ExceptionHandler.game_details_builder_exception
def game_details_builder(google_sheets_id, launch_id, fill):
    google_doc_connection = GoogleDocConnection(google_sheets_id)
    login, password, domain, gameid = google_doc_connection.get_setup()
    if 'demo' not in domain and gameid not in DB.get_gameids_for_builder_list():
        return 'Заполнение данной игры не разрешено. Напишите @JekaFST в телеграмме для получения разрешения'
    en_connection = ENConnection(domain, login, password, gameid)

    if fill:
        result = fill_engine(google_doc_connection, en_connection, domain, gameid)
    else:
        result = clean_engine(google_doc_connection, en_connection, gameid)

    return result


def fill_engine(google_doc_connection, en_connection, domain, gameid):
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


def clean_engine(google_doc_connection, en_connection, gameid):
    for i, level_row in enumerate(google_doc_connection.get_cleanup_level_rows()):
        level_page = en_connection.get_level_page(level_row[4])
        _, helps_to_del, bonuses_to_del, pen_helps_to_del, _ = parse_level_page(level_row, level_page)
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

    return 'Успех. Проверьте правильность удаления данных из движка.'


def transfer_game(source_level_number, target_level_number, source_game_data=SOURCE_GAME_DATA, target_game_data=TARGET_GAME_DATA):
    source_en_connection = ENConnection(source_game_data['domain'], source_game_data['login'], source_game_data['password'], source_game_data['gameid'])
    target_en_connection = ENConnection(target_game_data['domain'], target_game_data['login'], target_game_data['password'], target_game_data['gameid'])
    level_page = source_en_connection.get_level_page(source_level_number)
    if not DB.get_game_transfer_row(source_game_data['gameid'], 'gameid'):
        DB.insert_game_transfer_row(source_game_data['gameid'])
    _, help_ids, bonus_ids, pen_help_ids, task_ids = parse_level_page(['', 'all', 'all', 'all'], level_page, transfer=True)

    # for i, task_id in enumerate(task_ids):
    #     if i % 30 == 0:
    #         sleep(5)
    #     transfered_task_ids = DB.get_game_transfer_row(source_game_data['gameid'], 'taskids')
    #     if task_id not in transfered_task_ids:
    #         read_params = {
    #             'gid': source_game_data['gameid'],
    #             'level': source_level_number,
    #             'tid': task_id,
    #             'action': 'TaskEdit'
    #         }
    #         response = source_en_connection.read_en_object(read_params, 'task')
    #         if response:
    #             task_data, task_url, params = make_task_data_and_url(None, target_game_data['domain'], target_game_data['gameid'], response.text, target_level_number)
    #             if target_en_connection.create_en_object(task_url, task_data, 'task', params):
    #                 transfered_task_ids += task_id if not transfered_task_ids else ', ' + task_id
    #                 DB.update_game_transfer(source_game_data['gameid'], 'taskids', transfered_task_ids)
    #
    # for i, bonus_id in enumerate(bonus_ids):
    #     if i % 30 == 0:
    #         sleep(5)
    #     transfered_bonus_ids = DB.get_game_transfer_row(source_game_data['gameid'], 'bonusids')
    #     if bonus_id not in transfered_bonus_ids:
    #         read_params = {
    #             'gid': source_game_data['gameid'],
    #             'level': source_level_number,
    #             'bonus': bonus_id,
    #             'action': 'edit'
    #         }
    #         response = source_en_connection.read_en_object(read_params, 'bonus')
    #         if response:
    #             bonus_data, bonus_url, params = make_bonus_data_and_url(None, target_game_data['domain'], target_game_data['gameid'], target_en_connection.get_level_ids(), response.text, target_level_number)
    #             if target_en_connection.create_en_object(bonus_url, bonus_data, 'bonus', params):
    #                 transfered_bonus_ids += bonus_id if not transfered_bonus_ids else ', ' + bonus_id
    #                 DB.update_game_transfer(source_game_data['gameid'], 'bonusids', transfered_bonus_ids)
    #
    for i, help_id in enumerate(help_ids):
        if i % 30 == 0:
            sleep(5)
        transfered_help_ids = DB.get_game_transfer_row(source_game_data['gameid'], 'helpids')
        if help_id not in transfered_help_ids:
            read_params = {
                'gid': source_game_data['gameid'],
                'level': source_level_number,
                'prid': help_id,
                'action': 'PromptEdit'
            }
            response = source_en_connection.read_en_object(read_params, 'help')
            if response:
                help_data, help_url, params = make_help_data_and_url(None, target_game_data['domain'], target_game_data['gameid'], response.text, target_level_number)
                if target_en_connection.create_en_object(help_url, help_data, 'help', params):
                    transfered_help_ids += help_id if not transfered_help_ids else ', ' + help_id
                    DB.update_game_transfer(source_game_data['gameid'], 'helpids', transfered_help_ids)

    for i, pen_help_id in enumerate(pen_help_ids):
        if i % 30 == 0:
            sleep(5)
        transfered_pen_help_ids = DB.get_game_transfer_row(source_game_data['gameid'], 'penhelpids')
        if pen_help_id not in transfered_pen_help_ids:
            read_params = {
                'gid': source_game_data['gameid'],
                'level': source_level_number,
                'prid': pen_help_id,
                'action': 'PromptEdit',
                'penalty': '1'
            }
            response = source_en_connection.read_en_object(read_params, 'pen_help')
            if response:
                pen_help_data, pen_help_url, params = make_penalty_help_data_and_url(None, target_game_data['domain'], target_game_data['gameid'], response.text, target_level_number)
                if target_en_connection.create_en_object(pen_help_url, pen_help_data, 'PenaltyHelp', params):
                    transfered_pen_help_ids += pen_help_id if not transfered_pen_help_ids else ', ' + pen_help_id
                    DB.update_game_transfer(source_game_data['gameid'], 'penhelpids', transfered_pen_help_ids)


if __name__ == '__main__':
    transfer_game('2', '2')
