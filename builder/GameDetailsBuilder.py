# -*- coding: utf-8 -*-
import logging
import re
from time import sleep
from DBMethods import DB
from SourceGameDataParcers import get_answers_data, check_ans_block_enabled, check_all_sectors_required
from GameDetailsBuilderMethods import GoogleDocConnection, ENConnection, make_help_data_and_url, make_bonus_data_and_url, \
    make_sector_data_and_url, make_penalty_help_data_and_url, make_task_data_and_url, parse_level_page, \
    make_lvl_name_comment_data_and_url, make_lvl_timeout_data_and_url, clean_empty_first_sector, \
    make_del_answer_data_and_url, make_lvl_ans_block_data_and_url, make_lvl_sectors_required_data_and_url


class Buttons:
    BUTTON_FILL_ENGINE = "Заполнить движок".decode('utf-8')
    BUTTON_CLEAN_ENGINE = "Очистить движок".decode('utf-8')
    BUTTON_TRANSFER_ENGINE = "Перенести движок".decode('utf-8')


class FillEngine(object):
    def get_applications(self):
        return [
            {"name": Buttons.BUTTON_FILL_ENGINE, "fn": self.fill_engine},
        ]

    def __get_fill_engine_data(self, request):
        login = request.get('login').strip()
        password = request.get('password').strip()
        domain = request.get('domain').strip()
        if 'http://' not in domain:
            domain = 'http://' + domain
        game_id = request.get('game_id').strip()
        gdoc_id = request.get('gdoc_id').strip()
        return login, password, domain, game_id, gdoc_id

    def fill_engine(self, request):
        yield 'Заполнение движка запущено'.decode('utf-8')
        login, password, domain, game_id, gdoc_id = self.__get_fill_engine_data(request.json)
        if 'demo' in domain or game_id in DB.get_gameids_for_builder_list():
            google_doc_connection = GoogleDocConnection(gdoc_id)
            en_connection = ENConnection(domain, login, password, game_id)

            levels_details = google_doc_connection.get_levels_details()
            if levels_details:
                logging.log(logging.INFO, "Updating of level details is started")
                yield 'Обновление данных уровней запущено'.decode('utf-8')
                for i, level_details in enumerate(levels_details):
                    if i % 15 == 0:
                        sleep(5)
                    try:
                        logging.log(logging.INFO, "Updating of level %s details is started" % level_details[14])
                        lvl_name_comment_data, level_url, params = make_lvl_name_comment_data_and_url(level_details, en_connection.domain, en_connection.gameid)
                        en_connection.create_en_object(level_url, lvl_name_comment_data, 'level_name', params)

                        lvl_timeout_data, level_url, params = make_lvl_timeout_data_and_url(level_details, en_connection.domain, en_connection.gameid)
                        en_connection.create_en_object(level_url, lvl_timeout_data, 'level', params)

                        if level_details[8]:
                            lvl_ans_block_data, level_url, params = make_lvl_ans_block_data_and_url(level_details, en_connection.domain, en_connection.gameid)
                            en_connection.create_en_object(level_url, lvl_ans_block_data, 'level', params)

                        if level_details[13]:
                            lvl_sectors_required_data, level_sectors_required_url, params = make_lvl_sectors_required_data_and_url(level_details, en_connection.domain, en_connection.gameid)
                            en_connection.create_en_object(level_sectors_required_url, lvl_sectors_required_data, 'level', params)
                        logging.log(logging.INFO, "Updating of level %s details is finished" % level_details[14])
                    except Exception:
                        logging.exception("Exception on level %s details updating" % level_details[14])
                yield 'Обновление данных уровней выполнено'.decode('utf-8')
                logging.log(logging.INFO, "Updating of level details is finished")

            helps = google_doc_connection.get_helps()
            if helps:
                logging.log(logging.INFO, "Filling of helps is started")
                yield 'Заполнение подсказок запущено'.decode('utf-8')
                for i, help in enumerate(helps):
                    if i % 30 == 0:
                        sleep(5)
                    try:
                        logging.log(logging.INFO, "Filling of help %s is started" % str(i+1))
                        help_data, help_url, params = make_help_data_and_url(help, en_connection.domain, game_id)
                        en_connection.create_en_object(help_url, help_data, 'help', params)
                        logging.log(logging.INFO, "Filling of help %s is finished" % str(i + 1))
                    except Exception:
                        logging.exception("Exception on help %s filling" % str(i + 1))
                yield 'Заполнение подсказок выполнено'.decode('utf-8')
                logging.log(logging.INFO, "Filling of helps is finished")

            bonuses = google_doc_connection.get_bonuses()
            if bonuses:
                logging.log(logging.INFO, "Filling of bonuses is started")
                yield 'Заполнение бонусов запущено'.decode('utf-8')
                for i, bonus in enumerate(bonuses):
                    if i % 30 == 0:
                        sleep(5)
                    try:
                        logging.log(logging.INFO, "Filling of bonus %s is started" % str(i + 1))
                        bonus_data, bonus_url, params = make_bonus_data_and_url(bonus, en_connection.domain, game_id, en_connection.level_ids_dict)
                        en_connection.create_en_object(bonus_url, bonus_data, 'bonus', params)
                        logging.log(logging.INFO, "Filling of bonus %s is finished" % str(i + 1))
                    except Exception:
                        logging.exception("Exception on bonus %s filling" % str(i + 1))
                yield 'Заполнение бонусов выполнено'.decode('utf-8')
                logging.log(logging.INFO, "Filling of bonuses is finished")

            level_sectors_dict = google_doc_connection.get_sectors()
            if level_sectors_dict:
                logging.log(logging.INFO, "Filling of sectors is started")
                yield 'Заполнение секторов запущено'.decode('utf-8')
                for level, sectors in level_sectors_dict.items():
                    try:
                        logging.log(logging.INFO, "Filling of sectors for level %s is started" % level)
                        if len(sectors) == 1:
                            answer_data, answer_url, params = make_sector_data_and_url(sectors[0], en_connection.domain, game_id, is_answer=True)
                            en_connection.create_en_object(answer_url, answer_data, 'sector', params)
                        else:
                            for sector in sectors:
                                sector_data, sector_url, params = make_sector_data_and_url(sector, en_connection.domain, game_id)
                                en_connection.create_en_object(sector_url, sector_data, 'sector', params)
                        logging.log(logging.INFO, "Filling of sectors for level %s is finished" % level)
                        clean_empty_first_sector(en_connection, level)
                    except Exception:
                        logging.exception("Exception on sectors filling for level %s" % level)
                yield 'Заполнение секторов выполнено'.decode('utf-8')
                logging.log(logging.INFO, "Filling of sectors is finished")

            penalty_helps = google_doc_connection.get_penalty_helps()
            if penalty_helps:
                logging.log(logging.INFO, "Filling of penalty helps is started")
                yield 'Заполнение штрафных подсказок запущено'.decode('utf-8')
                for i, penalty_help in enumerate(penalty_helps):
                    if i % 30 == 0:
                        sleep(5)
                    try:
                        logging.log(logging.INFO, "Filling of penalty help %s is started" % str(i + 1))
                        pen_help_data, pen_help_url, params = make_penalty_help_data_and_url(penalty_help, en_connection.domain, game_id)
                        en_connection.create_en_object(pen_help_url, pen_help_data, 'PenaltyHelp', params)
                        logging.log(logging.INFO, "Filling of penalty help %s is finished" % str(i + 1))
                    except Exception:
                        logging.exception("Exception on penalty help %s filling" % str(i + 1))
                yield 'Заполнение штрафных подсказок выполнено'.decode('utf-8')
                logging.log(logging.INFO, "Filling of penalty helps is finished")

            tasks = google_doc_connection.get_tasks()
            if tasks:
                logging.log(logging.INFO, "Filling of tasks is started")
                yield 'Заполнение заданий запущено'.decode('utf-8')
                for i, task in enumerate(tasks):
                    if i % 30 == 0:
                        sleep(5)
                    try:
                        logging.log(logging.INFO, "Filling of task %s is started" % str(i + 1))
                        task_data, task_url, params = make_task_data_and_url(task, en_connection.domain, game_id)
                        en_connection.create_en_object(task_url, task_data, 'task', params)
                        logging.log(logging.INFO, "Filling of task %s is finished" % str(i + 1))
                    except Exception:
                        logging.exception("Exception on task %s filling" % str(i + 1))
                yield 'Заполнение заданий выполнено'.decode('utf-8')
                logging.log(logging.INFO, "Filling of tasks is finished")

            yield 'Проверьте правильность переноса данных в движок.'.decode('utf-8')
            logging.log(logging.INFO, "Filling of game is finished successfully")
        else:
            yield 'Заполнение данной игры не разрешено. Напишите @JekaFST в телеграмме для получения разрешения'.decode('utf-8')


class CleanEngine(object):
    def get_applications(self):
        return [
            {"name": Buttons.BUTTON_CLEAN_ENGINE, "fn": self.clean_engine},
        ]

    def __get_clean_engine_data(self, request):
        login = request.get('login').strip()
        password = request.get('password').strip()
        domain = request.get('domain').strip()
        if 'http://' not in domain:
            domain = 'http://' + domain
        game_id = request.get('game_id').strip()
        gdoc_id = request.get('gdoc_id').strip()
        return login, password, domain, game_id, gdoc_id

    def clean_engine(self, request):
        yield 'Очистка движка запущена'.decode('utf-8')
        login, password, domain, game_id, gdoc_id = self.__get_clean_engine_data(request.json)
        if 'demo' in domain or game_id in DB.get_gameids_for_builder_list():
            google_doc_connection = GoogleDocConnection(gdoc_id)
            en_connection = ENConnection(domain, login, password, game_id)

            for i, level_row in enumerate(google_doc_connection.get_cleanup_level_rows()):
                logging.log(logging.INFO, "Cleanup of level %s started" % level_row[4])
                yield str('Очистка данных из уровня %s запущена' % level_row[4]).decode('utf-8')

                level_page = en_connection.get_level_page(level_row[4])
                sectors_to_del, helps_to_del, bonuses_to_del, pen_helps_to_del, _ = parse_level_page(level_row, level_page)

                if helps_to_del:
                    logging.log(logging.INFO, "Cleanup of helps for level %s started" % level_row[4])
                    for help_to_del in helps_to_del:
                        params = {
                            'gid': game_id,
                            'action': 'PromptDelete',
                            'prid': help_to_del,
                            'level': level_row[4]
                        }
                        en_connection.delete_en_object(params, 'help')
                    logging.log(logging.INFO, "Cleanup of helps for level %s finished" % level_row[4])

                if bonuses_to_del:
                    logging.log(logging.INFO, "Cleanup of bonuses for level %s started" % level_row[4])
                    for bonus_to_del in bonuses_to_del:
                        params = {
                            'gid': game_id,
                            'action': 'delete',
                            'bonus': bonus_to_del,
                            'level': level_row[4]
                        }
                        en_connection.delete_en_object(params, 'bonus')
                    logging.log(logging.INFO, "Cleanup of bonuses for level %s finished" % level_row[4])

                if pen_helps_to_del:
                    logging.log(logging.INFO, "Cleanup of penalty helps for level %s started" % level_row[4])
                    for pen_help_to_del in pen_helps_to_del:
                        params = {
                            'gid': game_id,
                            'action': 'PromptDelete',
                            'prid': pen_help_to_del,
                            'level': level_row[4],
                            'penalty': '1'
                        }
                        en_connection.delete_en_object(params, 'pen_help')
                    logging.log(logging.INFO, "Cleanup of penalty helps for level %s finished" % level_row[4])

                if level_row[0].lower() in ['y', 'yes', 'true']:
                    logging.log(logging.INFO, "Cleanup of sectors for level %s started" % level_row[4])
                    if sectors_to_del:
                        for i, sector_to_del in enumerate(sectors_to_del):
                            if i % 30 == 0:
                                sleep(5)
                            params = {
                                'gid': en_connection.game_id,
                                'level': level_row[4],
                                'delsector': sector_to_del,
                                'swanswers': 1
                            }
                            en_connection.delete_en_object(params, 'sector')
                        logging.log(logging.INFO, "Cleanup of sectors for level %s finished" % level_row[4])
                    else:
                        answers = re.findall('divAnswersView_(\d+)', level_page)
                        if answers:
                            read_params = {
                                'gid': en_connection.game_id,
                                'level': level_row[4],
                                'editanswers': answers[0],
                                'swanswers': '1'
                            }
                            response = en_connection.read_en_object(read_params, 'sector')
                            if response:
                                answers_data = get_answers_data(response.text, answers[0])
                                del_answer_data, del_answer_url, params = make_del_answer_data_and_url(en_connection.domain, en_connection.gameid, answers_data, level_row[4], answers[0])
                                en_connection.create_en_object(del_answer_url, del_answer_data, 'sector', params)
                        yield str('Очистка данных из уровня %s выполнена' % level_row[4]).decode('utf-8')
                        logging.log(logging.INFO, "Cleanup of sectors for level %s finished" % level_row[4])

                logging.log(logging.INFO, "Cleanup of level %s finished" % level_row[4])
            yield 'Проверьте правильность удаления данных из движка.'.decode('utf-8')
        else:
            yield 'Очистка данных для данной игры не разрешено. Напишите @JekaFST в телеграмме для получения разрешения'.decode('utf-8')


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
        yield 'Перенос движка запущен'.decode('utf-8')
        s_login, s_password, s_domain, s_game_id, tg_login, tg_password, tg_domain, tg_game_id, gdoc_id = self.__get_transfer_engine_data(request.json)
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
                    message = 'Перенос данных из %s уровня в %s уровень запущен' % (source_ln, source_ln)
                    yield message.decode('utf-8')
                    self.__transfer_level(source_en_conn, target_en_conn, **transfer_settings)
                    message = 'Перенос данных из %s уровня в %s уровень выполнен' % (source_ln, source_ln)
                    yield message.decode('utf-8')
                    logging.log(logging.INFO, "Moving of source level %s to target level %s is finished successfully" % (source_ln, source_ln))
            else:
                move_levels_mappings = google_doc_connection.get_move_levels_mapping()
                for mlm in move_levels_mappings:
                    logging.log(logging.INFO, "Moving of source level %s to target level %s is started" % (mlm['source_ln'], mlm['target_ln']))
                    message = 'Перенос данных из %s уровня в %s уровень запущен' % (mlm['source_ln'], mlm['target_ln'])
                    yield message.decode('utf-8')
                    self.__transfer_level(source_en_conn, target_en_conn, **mlm)
                    message = 'Перенос данных из %s уровня в %s уровень выполнен' % (mlm['source_ln'], mlm['target_ln'])
                    yield message.decode('utf-8')
                    logging.log(logging.INFO, "Moving of source level %s to target level %s is finished successfully" % (mlm['source_ln'], mlm['target_ln']))

            yield 'Проверьте правильность переноса данных.'.decode('utf-8')
        else:
            yield 'Перенос в целевую игру не разрешен. Напишите @JekaFST в телеграмме для получения разрешения'.decode('utf-8')

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
