# -*- coding: utf-8 -*-
from ExceptionHandler import ExceptionHandler
from DBMethods import DB
from GameDetailsBuilderMethods import GoogleDocConnection, ENConnection, make_help_data_and_url, make_bonus_data_and_url, \
    make_sector_data_and_url, make_penalty_help_data_and_url, make_task_data_and_url, parse_level_page, \
    get_bonus_help_text
from time import sleep


SOURCE_GAME_DATA = {
    'domain': 'http://demo.en.cx',
    'login': 'prinncessa',
    'password': 'h323232z',
    'gameid': '29413'
}
TARGET_GAME_DATA={
    'domain': 'http://demo.en.cx',
    'login': 'jekafst',
    'password': 'hjccbz1412',
    'gameid': '28793'
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

    return 'Успех. Проверьте правильность удаления данных из движка.'


def transfer_game(source_game_data=SOURCE_GAME_DATA, target_game_data=TARGET_GAME_DATA, source_level_number='1', target_level_number='1'):
    source_en_connection = ENConnection(source_game_data['domain'], source_game_data['login'], source_game_data['password'], source_game_data['gameid'])
    target_en_connection = ENConnection(target_game_data['domain'], target_game_data['login'], target_game_data['password'], target_game_data['gameid'])
    level_page = source_en_connection.get_level_page(source_level_number)
    _, help_ids, bonus_ids, pen_help_ids = parse_level_page(['', 'all', 'all', 'all'], level_page)
    for bonus_id in bonus_ids:
        read_params = {
            'gid': source_game_data['gameid'],
            'level': source_level_number,
            'bonus': bonus_id,
            'action': 'edit'
        }
        response = source_en_connection.read_en_object(read_params, 'bonus')
        bonus_data, bonus_url, params = make_bonus_data_and_url(None, source_game_data['domain'], source_game_data['gameid'], target_en_connection.get_level_ids(), response.text, target_level_number)
        target_en_connection.create_en_object(bonus_url, bonus_data, 'bonus', params)


if __name__ == '__main__':
    transfer_game()
