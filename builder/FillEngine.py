# -*- coding: utf-8 -*-
import logging
from time import sleep
from DBMethods import DB
from builder.GameDetailsBuilderMethods import GoogleDocConnection, ENConnection, make_help_data_and_url, make_bonus_data_and_url,\
    make_sector_data_and_url, make_penalty_help_data_and_url, make_task_data_and_url, make_lvl_name_comment_data_and_url,\
    make_lvl_timeout_data_and_url, clean_empty_first_sector, make_lvl_ans_block_data_and_url, make_lvl_sectors_required_data_and_url


class Buttons:
    BUTTON_FILL_ENGINE = "Заполнить движок"


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
        login, password, domain, game_id, gdoc_id = self.__get_fill_engine_data(request.json)
        yield 'Заполнение движка из дока %s запущено' % gdoc_id
        if 'demo' in domain or game_id in DB.get_gameids_for_builder_list():
            google_doc_connection = GoogleDocConnection(gdoc_id)
            en_connection = ENConnection(domain, login, password, game_id)

            levels_details = google_doc_connection.get_levels_details()
            if levels_details:
                logging.log(logging.INFO, "Updating of level details is started")
                yield 'Обновление данных уровней запущено'
                for i, level_details in enumerate(levels_details):
                    if i % 15 == 0:
                        sleep(5)
                    try:
                        logging.log(logging.INFO, "Updating of level %s details is started" % level_details[14])
                        lvl_name_comment_data, level_url, params = make_lvl_name_comment_data_and_url(level_details, en_connection.domain, en_connection.gameid)
                        if not en_connection.create_en_object(level_url, lvl_name_comment_data, 'level_name', params):
                            yield 'Проверьте название и комментарий уровня из строки %s' % level_details[14]
                            logging.log(logging.WARNING, 'Check name and comment update for level %s' % level_details[14])

                        lvl_timeout_data, level_url, params = make_lvl_timeout_data_and_url(level_details, en_connection.domain, en_connection.gameid)
                        if not en_connection.create_en_object(level_url, lvl_timeout_data, 'level', params):
                            yield 'Проверьте информацию по автопереходу уровня из строки %s' % level_details[14]
                            logging.log(logging.WARNING, 'Check timeout update for level %s' % level_details[14])

                        if level_details[8]:
                            lvl_ans_block_data, level_url, params = make_lvl_ans_block_data_and_url(level_details, en_connection.domain, en_connection.gameid)
                            if not en_connection.create_en_object(level_url, lvl_ans_block_data, 'level', params):
                                yield 'Проверьте информацию о блокировках уровня из строки %s' % level_details[14]
                                logging.log(logging.WARNING, 'Check answers blocking update for level %s' % level_details[14])

                        if level_details[13]:
                            lvl_sectors_required_data, level_sectors_required_url, params = make_lvl_sectors_required_data_and_url(level_details, en_connection.domain, en_connection.gameid)
                            if not en_connection.create_en_object(level_sectors_required_url, lvl_sectors_required_data, 'level', params):
                                yield 'Проверьте информацию о секторах для взятия уровня из строки %s' % level_details[14]
                                logging.log(logging.WARNING, 'Check number of answers to close for level %s' % level_details[14])

                        logging.log(logging.INFO, "Updating of level %s details is finished" % level_details[14])
                    except Exception:
                        logging.exception("Exception on level %s details updating" % level_details[14])
                yield 'Обновление данных уровней выполнено'
                logging.log(logging.INFO, "Updating of level details is finished")

            helps = google_doc_connection.get_helps()
            if helps:
                logging.log(logging.INFO, "Filling of helps is started")
                yield 'Заполнение подсказок запущено'
                for i, help in enumerate(helps):
                    if i % 30 == 0:
                        sleep(5)
                    try:
                        logging.log(logging.INFO, "Filling of help %s is started" % str(i+1))
                        help_data, help_url, params = make_help_data_and_url(help, en_connection.domain, game_id)
                        if not en_connection.create_en_object(help_url, help_data, 'help', params):
                            yield 'Проверьте заполнение подсказки по строке %s' % str(i + 1)
                            logging.log(logging.WARNING, "Check filling of help %s" % str(i + 1))
                        else:
                            logging.log(logging.INFO, "Filling of help %s is finished" % str(i + 1))
                    except Exception:
                        yield 'Проверьте заполнение подсказки по строке %s' % str(i + 1)
                        logging.exception("Exception on help %s filling" % str(i + 1))
                yield 'Заполнение подсказок выполнено'
                logging.log(logging.INFO, "Filling of helps is finished")

            bonuses = google_doc_connection.get_bonuses()
            if bonuses:
                logging.log(logging.INFO, "Filling of bonuses is started")
                yield 'Заполнение бонусов запущено'
                for i, bonus in enumerate(bonuses):
                    if i % 30 == 0:
                        sleep(5)
                    try:
                        logging.log(logging.INFO, "Filling of bonus %s is started" % str(i + 1))
                        bonus_data, bonus_url, params = make_bonus_data_and_url(bonus, en_connection.domain, game_id, en_connection.level_ids_dict)
                        if not en_connection.create_en_object(bonus_url, bonus_data, 'bonus', params):
                            yield 'Проверьте заполнение бонуса по строке %s' % str(i + 1)
                            logging.log(logging.WARNING, "Check filling of bonus %s" % str(i + 1))
                        else:
                            logging.log(logging.INFO, "Filling of bonus %s is finished" % str(i + 1))
                    except Exception:
                        yield 'Проверьте заполнение бонуса по строке %s' % str(i + 1)
                        logging.exception("Exception on bonus %s filling" % str(i + 1))
                yield 'Заполнение бонусов выполнено'
                logging.log(logging.INFO, "Filling of bonuses is finished")

            level_sectors_dict = google_doc_connection.get_sectors()
            if level_sectors_dict:
                logging.log(logging.INFO, "Filling of sectors is started")
                yield 'Заполнение секторов запущено'
                for level, sectors in level_sectors_dict.items():
                    try:
                        logging.log(logging.INFO, "Filling of sectors for level %s is started" % level)
                        if len(sectors) == 1:
                            answer_data, answer_url, params = make_sector_data_and_url(sectors[0], en_connection.domain, game_id, is_answer=True)
                            if not en_connection.create_en_object(answer_url, answer_data, 'sector', params):
                                yield 'Проверьте заполнение секторов по уровню %s' % level
                                logging.log(logging.WARNING, "Check filling of sectors for level %s" % level)
                        else:
                            for i, sector in enumerate(sectors):
                                sector_data, sector_url, params = make_sector_data_and_url(sector, en_connection.domain, game_id)
                                if not en_connection.create_en_object(sector_url, sector_data, 'sector', params):
                                    yield 'Проверьте заполнение сектора %s по уровню %s' % (str(i + 1), level)
                                    logging.log(logging.WARNING, "Check filling of sector %s for level %s" % (str(i + 1), level))
                        logging.log(logging.INFO, "Filling of sectors for level %s is finished" % level)
                        if not clean_empty_first_sector(en_connection, level):
                            yield 'Проверьте правильность заполнения секторов по уровню %s' % level
                    except Exception:
                        yield 'Проверьте правильность заполнения секторов по уровню %s' % level
                        logging.exception("Exception on sectors filling for level %s" % level)
                yield 'Заполнение секторов выполнено'
                logging.log(logging.INFO, "Filling of sectors is finished")

            penalty_helps = google_doc_connection.get_penalty_helps()
            if penalty_helps:
                logging.log(logging.INFO, "Filling of penalty helps is started")
                yield 'Заполнение штрафных подсказок запущено'
                for i, penalty_help in enumerate(penalty_helps):
                    if i % 30 == 0:
                        sleep(5)
                    try:
                        logging.log(logging.INFO, "Filling of penalty help %s is started" % str(i + 1))
                        pen_help_data, pen_help_url, params = make_penalty_help_data_and_url(penalty_help, en_connection.domain, game_id)
                        if not en_connection.create_en_object(pen_help_url, pen_help_data, 'PenaltyHelp', params):
                            yield 'Проверьте заполнение штрафной подсказки по строке %s' % str(i + 1)
                            logging.log(logging.WARNING, "Check filling of penalty help %s" % str(i + 1))
                        else:
                            logging.log(logging.INFO, "Filling of penalty help %s is finished" % str(i + 1))
                    except Exception:
                        yield 'Проверьте заполнение штрафной подсказки по строке %s' % str(i + 1)
                        logging.exception("Exception on penalty help %s filling" % str(i + 1))
                yield 'Заполнение штрафных подсказок выполнено'
                logging.log(logging.INFO, "Filling of penalty helps is finished")

            tasks = google_doc_connection.get_tasks()
            if tasks:
                logging.log(logging.INFO, "Filling of tasks is started")
                yield 'Заполнение заданий запущено'
                for i, task in enumerate(tasks):
                    if i % 30 == 0:
                        sleep(5)
                    try:
                        logging.log(logging.INFO, "Filling of task %s is started" % str(i + 1))
                        task_data, task_url, params = make_task_data_and_url(task, en_connection.domain, game_id)
                        if not en_connection.create_en_object(task_url, task_data, 'task', params):
                            yield 'Проверьте заполнение задания по строке %s' % str(i + 1)
                            logging.log(logging.WARNING, "Check filling of task %s" % str(i + 1))
                        else:
                            logging.log(logging.INFO, "Filling of task %s is finished" % str(i + 1))
                    except Exception:
                        yield 'Проверьте заполнение задания по строке %s' % str(i + 1)
                        logging.exception("Exception on task %s filling" % str(i + 1))
                yield 'Заполнение заданий выполнено'
                logging.log(logging.INFO, "Filling of tasks is finished")

            yield 'Проверьте правильность переноса данных в движок.'
            logging.log(logging.INFO, "Filling of game is finished successfully")
        else:
            yield 'Приложение платное - заполнение данной игры не разрешено. Напишите @JekaFST в телеграмме для получения разрешения'
