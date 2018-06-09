# -*- coding: utf-8 -*-
import ExceptionHandler
from GameDetailsBuilderMethods import GoogleDocConnection, ENConnection, make_help_data_and_url, make_bonus_data_and_url, \
    make_sector_data_and_url, make_penalty_help_data_and_url
from time import sleep


@ExceptionHandler.game_details_builder_exception
def game_details_builder(google_sheets_id):
    google_doc_connection = GoogleDocConnection(google_sheets_id)
    login, password, domain, gameid = google_doc_connection.get_setup()
    en_connection = ENConnection(domain, login, password, gameid)
    # bonuses = dict()
    # bonuses = en_connection.get_level_page('2', bonuses)

    for i, help in enumerate(google_doc_connection.get_helps()):
        if i % 30 == 0:
            sleep(5)
        help_data, help_url = make_help_data_and_url(help, domain, gameid)
        en_connection.create_en_object(help_url, help_data, 'help')

    for i, bonus in enumerate(google_doc_connection.get_bonuses()):
        if i % 30 == 0:
            sleep(5)
        bonus_data, bonus_url = make_bonus_data_and_url(bonus, domain, gameid, en_connection.level_ids_dict)
        en_connection.create_en_object(bonus_url, bonus_data, 'bonus')

    for i, sector in enumerate(google_doc_connection.get_sectors()):
        if i % 30 == 0:
            sleep(5)
        sector_data, sector_url = make_sector_data_and_url(sector, domain, gameid)
        en_connection.create_en_object(sector_url, sector_data, 'sector')

    for i, penalty_help in enumerate(google_doc_connection.get_penalty_helps()):
        if i % 30 == 0:
            sleep(5)
        pen_help_data, pen_help_url = make_penalty_help_data_and_url(penalty_help, domain, gameid)
        en_connection.create_en_object(pen_help_url, pen_help_data, 'PenaltyHelp')
