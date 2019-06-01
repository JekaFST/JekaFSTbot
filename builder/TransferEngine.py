# -*- coding: utf-8 -*-
import re
import logging
from time import sleep
from DBMethods import DB
from SourceGameDataParcers import check_ans_block_enabled, check_all_sectors_required
from GameDetailsBuilderMethods import GoogleDocConnection, ENConnection, make_help_data_and_url, make_bonus_data_and_url, \
    make_sector_data_and_url, make_penalty_help_data_and_url, make_task_data_and_url, parse_level_page, \
    make_lvl_name_comment_data_and_url, make_lvl_timeout_data_and_url, clean_empty_first_sector, make_lvl_ans_block_data_and_url,\
    make_lvl_sectors_required_data_and_url


class Buttons:
    BUTTON_TRANSFER_ENGINE = "Перенести движок"


class TransferEngine(object):
    def get_applications(self):
        return [
            {"name": Buttons.BUTTON_TRANSFER_ENGINE, "fn": self.transfer_game},
        ]

    def __get_transfer_engine_data(self, request):
        s_login = request.get('s_login').strip()
        s_password = request.get('s_password').strip()
        s_domain = request.get('s_domain').strip()
        if 'http://' not in s_domain:
            s_domain = 'http://' + s_domain
        s_game_id = request.get('s_game_id').strip()
        tg_login = request.get('tg_login').strip()
        tg_password = request.get('tg_password').strip()
        tg_domain = request.get('tg_domain').strip()
        if 'http://' not in tg_domain:
            tg_domain = 'http://' + tg_domain
        tg_game_id = request.get('tg_game_id').strip()
        gdoc_id = request.get('gdoc_id').strip()
        return s_login, s_password, s_domain, s_game_id, tg_login, tg_password, tg_domain, tg_game_id, gdoc_id

    def transfer_game(self, request):
        s_login, s_password, s_domain, s_game_id, tg_login, tg_password, tg_domain, tg_game_id, gdoc_id = self.__get_transfer_engine_data(request.json)
        yield 'Перенос движка из дока %s запущен' % gdoc_id
        if 'demo' in tg_domain or tg_game_id in DB.get_gameids_for_builder_list():
            google_doc_connection = GoogleDocConnection(gdoc_id)
            move_all, transfer_settings = google_doc_connection.get_move_setup()
            source_en_conn = ENConnection(s_domain, s_login, s_password, s_game_id)
            target_en_conn = ENConnection(tg_domain, tg_login, tg_password, tg_game_id)

            if move_all:
                sorted_level_ids = sorted(source_en_conn.level_ids_dict.items(), key=lambda item: item[1])
                for sorted_level_id in sorted_level_ids:
                    source_ln = sorted_level_id[0]
                    transfer_settings['source_ln'] = source_ln
                    transfer_settings['target_ln'] = source_ln
                    logging.log(logging.INFO, "Moving of source level %s to target level %s is started" % (source_ln, source_ln))
                    yield 'Перенос данных из %s уровня в %s уровень запущен' % (source_ln, source_ln)
                    self.__transfer_level(source_en_conn, target_en_conn, **transfer_settings)
                    yield 'Перенос данных из %s уровня в %s уровень выполнен' % (source_ln, source_ln)
                    logging.log(logging.INFO, "Moving of source level %s to target level %s is finished successfully" % (source_ln, source_ln))
            else:
                move_levels_mappings = google_doc_connection.get_move_levels_mapping()
                for mlm in move_levels_mappings:
                    logging.log(logging.INFO, "Moving of source level %s to target level %s is started" % (mlm['source_ln'], mlm['target_ln']))
                    yield 'Перенос данных из %s уровня в %s уровень запущен' % (mlm['source_ln'], mlm['target_ln'])
                    self.__transfer_level(source_en_conn, target_en_conn, **mlm)
                    yield 'Перенос данных из %s уровня в %s уровень выполнен' % (mlm['source_ln'], mlm['target_ln'])
                    logging.log(logging.INFO, "Moving of source level %s to target level %s is finished successfully" % (mlm['source_ln'], mlm['target_ln']))

            yield 'Проверьте правильность переноса данных.'
        else:
            yield 'Перенос в целевую игру не разрешен. Напишите @JekaFST в телеграмме для получения разрешения'

    def __transfer_level(self, source_en_conn, target_en_conn, source_ln=None, target_ln=None, level=None, task=None, helps=None, bonuses=None, pen_helps=None, sectors=None):
        level_page = source_en_conn.get_level_page(source_ln)
        sector_ids, help_ids, bonus_ids, pen_help_ids, task_ids = parse_level_page(['y', 'all', 'all', 'all'], level_page, transfer=True)

        if level:
            if check_ans_block_enabled(level_page):
                read_params = {
                    'gid': source_en_conn.gameid,
                    'level': source_ln,
                    'sw': 'answblock',
                }
                response = source_en_conn.read_en_object(read_params, 'level')
                if response:
                    lvl_ans_block_data, level_url, params = make_lvl_ans_block_data_and_url(None, target_en_conn.domain, target_en_conn.gameid, response.text, target_ln)
                    target_en_conn.create_en_object(level_url, lvl_ans_block_data, 'level_name', params)

            if not check_all_sectors_required(level_page):
                read_params = {
                    'gid': source_en_conn.gameid,
                    'level': source_ln,
                    'sw': 'edlvlsectsett',
                }
                response = source_en_conn.read_en_object(read_params, 'level')
                if response:
                    lvl_sectors_required_data, level_sectors_required_url, params = make_lvl_sectors_required_data_and_url(None, target_en_conn.domain, target_en_conn.gameid, response.text, target_ln)
                    target_en_conn.create_en_object(level_sectors_required_url, lvl_sectors_required_data, 'level_name', params)

            read_params = {
                'gid': source_en_conn.gameid,
                'level': source_ln,
            }
            response = source_en_conn.read_en_object(read_params, 'level_name')
            if response:
                lvl_name_comment_data, level_url, params = make_lvl_name_comment_data_and_url(None, target_en_conn.domain, target_en_conn.gameid, response.text, target_ln)
                target_en_conn.create_en_object(level_url, lvl_name_comment_data, 'level_name', params)

            read_params = {
                'gid': source_en_conn.gameid,
                'level': source_ln,
                'object': '4',
            }
            response = source_en_conn.read_en_object(read_params, 'level_timeout')
            if response:
                lvl_timeout_data, level_url, params = make_lvl_timeout_data_and_url(None, target_en_conn.domain, target_en_conn.gameid, response.text, target_ln)
                target_en_conn.create_en_object(level_url, lvl_timeout_data, 'level', params)

        if task:
            for i, task_id in enumerate(task_ids):
                if i % 30 == 0:
                    sleep(5)
                if task_id not in DB.get_game_transfer_ids(source_en_conn.gameid, 'taskid'):
                    read_params = {
                        'gid': source_en_conn.gameid,
                        'level': source_ln,
                        'tid': task_id,
                        'action': 'TaskEdit'
                    }
                    response = source_en_conn.read_en_object(read_params, 'task')
                    if response:
                        task_data, task_url, params = make_task_data_and_url(None, target_en_conn.domain, target_en_conn.gameid, response.text, target_ln)
                        if target_en_conn.create_en_object(task_url, task_data, 'task', params):
                            DB.insert_game_transfer_row(source_en_conn.gameid, 'taskid', task_id)

        if bonuses:
            for i, bonus_id in enumerate(bonus_ids):
                if i % 30 == 0:
                    sleep(5)

                if bonus_id not in DB.get_game_transfer_ids(source_en_conn.gameid, 'bonusid'):
                    read_params = {
                        'gid': source_en_conn.gameid,
                        'level': source_ln,
                        'bonus': bonus_id,
                        'action': 'edit'
                    }
                    response = source_en_conn.read_en_object(read_params, 'bonus')
                    if response:
                        bonus_data, bonus_url, params = make_bonus_data_and_url(None, target_en_conn.domain, target_en_conn.gameid, target_en_conn.level_ids_dict, response.text, target_ln)
                        if target_en_conn.create_en_object(bonus_url, bonus_data, 'bonus', params):
                            DB.insert_game_transfer_row(source_en_conn.gameid, 'bonusid', bonus_id)

        if helps:
            for i, help_id in enumerate(help_ids):
                if i % 30 == 0:
                    sleep(5)
                if help_id not in DB.get_game_transfer_ids(source_en_conn.gameid, 'helpid'):
                    read_params = {
                        'gid': source_en_conn.gameid,
                        'level': source_ln,
                        'prid': help_id,
                        'action': 'PromptEdit'
                    }
                    response = source_en_conn.read_en_object(read_params, 'help')
                    if response:
                        help_data, help_url, params = make_help_data_and_url(None, target_en_conn.domain, target_en_conn.gameid, response.text, target_ln)
                        if target_en_conn.create_en_object(help_url, help_data, 'help', params):
                            DB.insert_game_transfer_row(source_en_conn.gameid, 'helpid', help_id)

        if pen_helps:
            for i, pen_help_id in enumerate(pen_help_ids):
                if i % 30 == 0:
                    sleep(5)
                if pen_help_id not in DB.get_game_transfer_ids(source_en_conn.gameid, 'penhelpid'):
                    read_params = {
                        'gid': source_en_conn.gameid,
                        'level': source_ln,
                        'prid': pen_help_id,
                        'action': 'PromptEdit',
                        'penalty': '1'
                    }
                    response = source_en_conn.read_en_object(read_params, 'pen_help')
                    if response:
                        pen_help_data, pen_help_url, params = make_penalty_help_data_and_url(None, target_en_conn.domain, target_en_conn.gameid, response.text, target_ln)
                        if target_en_conn.create_en_object(pen_help_url, pen_help_data, 'PenaltyHelp', params):
                            DB.insert_game_transfer_row(source_en_conn.gameid, 'penhelpid', pen_help_id)

        if sectors:
            if sector_ids:
                for i, sector_id in enumerate(sector_ids):
                    if i % 30 == 0:
                        sleep(5)
                    if sector_id not in DB.get_game_transfer_ids(source_en_conn.gameid, 'sectorid'):
                        read_params = {
                            'gid': source_en_conn.gameid,
                            'level': source_ln,
                            'editanswers': sector_id,
                            'swanswers': '1'
                        }
                        response = source_en_conn.read_en_object(read_params, 'sector')
                        if response:
                            sector_data, sector_url, params = make_sector_data_and_url(None, target_en_conn.domain, target_en_conn.gameid, response.text, target_ln, sector_id)
                            target_en_conn.create_en_object(sector_url, sector_data, 'sector', params)
                            DB.insert_game_transfer_row(source_en_conn.gameid, 'sectorid', sector_id)
                clean_empty_first_sector(target_en_conn, target_ln)
            else:
                answers = re.findall('divAnswersView_(\d+)', level_page)
                if answers:
                    read_params = {
                        'gid': source_en_conn.gameid,
                        'level': source_ln,
                        'editanswers': answers[0],
                        'swanswers': '1'
                    }
                    response = source_en_conn.read_en_object(read_params, 'sector')
                    if response:
                        sector_data, sector_url, params = make_sector_data_and_url(None, target_en_conn.domain, target_en_conn.gameid, response.text, target_ln, answers[0])
                        target_en_conn.create_en_object(sector_url, sector_data, 'sector', params)
                        DB.insert_game_transfer_row(source_en_conn.gameid, 'answersid', answers[0])
