# -*- coding: utf-8 -*-
import json
from DBConnectionPool import ConnectionPool


connection_pool = ConnectionPool()
connection_pool.init_pool()


class DBSession(object):
    @staticmethod
    def get_sessions_ids():
        sql = "SELECT session_id FROM session_config"
        with connection_pool.get_conn() as db_connection:
            rows = db_connection.execute_select_cur(sql)
            return [row[0] for row in rows] if rows else list()

    @staticmethod
    def insert_session(main_chat_id):
        sql = f"""
                    INSERT INTO session_config
                    (session_id, active, login, password, en_domain, game_id, channel_name, cookie, game_url, login_url,
                    game_model_status, use_channel, stop_updater, put_updater_task, delay, send_codes, storm_game,
                    curr_level_id, sectors_to_close, sectors_message_id, locations, ll_message_ids)
                    VALUES ({main_chat_id}, False, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL,
                    NULL, False, True, NULL, 2, True, NULL,
                    NULL, NULL, NULL, NULL, NULL)
              """
        with connection_pool.get_conn() as db_connection:
            return db_connection.execute_insert_cur(sql)

    @staticmethod
    def get_session(session_id):
        sql = f"SELECT * FROM session_config WHERE session_id = {session_id}"
        with connection_pool.get_conn() as db_connection:
            rows = db_connection.execute_dict_select_cur(sql)
            return rows[0] if rows else None

    @staticmethod
    def delete_session(session_id):
        sql = f"DELETE FROM session_config WHERE session_id = {session_id}"
        with connection_pool.get_conn() as db_connection:
            db_connection.execute_insert_cur(sql)

    @staticmethod
    def get_all_sessions():
        sql = "SELECT * FROM session_config"
        with connection_pool.get_conn() as db_connection:
            rows = db_connection.execute_dict_select_cur(sql)
            return rows if rows else list()

    @staticmethod
    def update_session_urls(session_id, urls):
        sql = f"""
                    UPDATE session_config
                    SET game_url = '{urls['game_url']}', login_url = '{urls['login_url']}'
                    WHERE session_id = {session_id}
              """
        with connection_pool.get_conn() as db_connection:
            return db_connection.execute_insert_cur(sql)

    @staticmethod
    def drop_session_vars(session_id):
        sql = f"""
                    UPDATE session_config
                    SET curr_level_id = NULL, game_url = NULL, login_url = NULL, storm_game = NULL,
                    send_codes = True, game_model_status = NULL, put_updater_task = NULL, stop_updater = True,
                    locations = NULL, ll_message_ids = NULL
                    WHERE session_id = {session_id}
              """
        with connection_pool.get_conn() as db_connection:
            db_connection.execute_insert_cur(sql)

    @staticmethod
    def get_locations(session_id):
        sql = f"SELECT locations FROM session_config WHERE session_id = {session_id}"
        with connection_pool.get_conn() as db_connection:
            rows = db_connection.execute_select_cur(sql)
            return json.loads(rows[0][0]) if rows[0][0] is not None else rows[0][0]

    @staticmethod
    def update_json_field(session_id, header, value):
        sql = f"""
                    UPDATE session_config
                    SET {header} = '{json.dumps(value)}' if value else NULL
                    WHERE session_id = {session_id}
              """
        with connection_pool.get_conn() as db_connection:
            return db_connection.execute_insert_cur(sql)

    @staticmethod
    def update_text_field(session_id, header, value):
        sql = f"""
                    UPDATE session_config
                    SET {header} = $${value}$$
                    WHERE session_id = {session_id}
              """
        with connection_pool.get_conn() as db_connection:
            return db_connection.execute_insert_cur(sql)

    @staticmethod
    def get_field_value(session_id, header):
        sql = f"SELECT {header} FROM session_config WHERE session_id = {session_id}"
        with connection_pool.get_conn() as db_connection:
            rows = db_connection.execute_select_cur(sql)
            return rows[0][0]

    @staticmethod
    def update_bool_flag(session_id, header, value):
        sql = f"""
                    UPDATE session_config
                    SET {header} = {value}
                    WHERE session_id = {session_id}
              """
        with connection_pool.get_conn() as db_connection:
            return db_connection.execute_insert_cur(sql)

    @staticmethod
    def update_int_field(session_id, header, value):
        sql = f"""
                    UPDATE session_config
                    SET {header} = {value}
                    WHERE session_id = {session_id}
              """
        with connection_pool.get_conn() as db_connection:
            return db_connection.execute_insert_cur(sql)


class DBLevels(object):
    @staticmethod
    def insert_level(session_id, game_id, level):
        name = level['LevelName'].encode('utf-8') if level['LevelName'] else ''
        sql = f"""
                    INSERT INTO levels
                    (session_id, level_id, game_id, number, is_passed, dismissed, time_to_up_sent, level_name)
                    VALUES ({session_id}, {level['LevelId']}, '{game_id}', {level['LevelNumber']}, {level['IsPassed']}, {level['Dismissed']}, False, $${name}$$)
              """
        with connection_pool.get_conn() as db_connection:
            return db_connection.execute_insert_cur(sql)

    @staticmethod
    def get_dismissed_level_ids(session_id, game_id):
        sql = f"""
                    SELECT level_id FROM levels
                    WHERE session_id = {session_id} AND game_id = '{game_id}' AND dismissed = True
              """
        with connection_pool.get_conn() as db_connection:
            rows = db_connection.execute_select_cur(sql)
            return [row[0] for row in rows] if rows else list()

    @staticmethod
    def get_passed_level_ids(session_id, game_id):
        sql = f"""
                    SELECT level_id FROM levels
                    WHERE session_id = {session_id} AND game_id = '{game_id}' AND is_passed = True
              """
        with connection_pool.get_conn() as db_connection:
            rows = db_connection.execute_select_cur(sql)
            return [row[0] for row in rows] if rows else list()

    @staticmethod
    def update_bool_field(session_id, game_id, level_id, header, active):
        sql = f"""
                    UPDATE levels
                    SET {header} = {active}
                    WHERE session_id = {session_id} AND game_id = '{game_id}' AND level_id = {level_id}
              """
        with connection_pool.get_conn() as db_connection:
            db_connection.execute_insert_cur(sql)

    @staticmethod
    def get_level_ids_per_game(session_id, game_id):
        sql = """SELECT LevelId FROM levels
                    WHERE sessionid = %s AND gameid = '%s'
                    """ % (session_id, game_id)
        with connection_pool.get_conn() as db_connection:
            rows = db_connection.execute_select_cur(sql)
            return [row[0] for row in rows] if rows else list()

    @staticmethod
    def get_time_to_up_sent(session_id, level_id):
        sql = f"SELECT time_to_up_sent FROM levels WHERE session_id = {session_id} AND level_id = {level_id}"
        with connection_pool.get_conn() as db_connection:
            rows = db_connection.execute_select_cur(sql)
            return rows[0][0]

    @staticmethod
    def get_level_number(session_id, level_id):
        sql = f"SELECT number FROM levels WHERE session_id = {session_id} AND level_id = {level_id}"
        with connection_pool.get_conn() as db_connection:
            rows = db_connection.execute_select_cur(sql)
            return rows[0][0]

    @staticmethod
    def update_time_to_up_sent(session_id, level_id, active):
        sql = f"""
                    UPDATE levels
                    SET time_to_up_sent = {active}
                    WHERE session_id = {session_id} AND level_id = {level_id}
              """
        with connection_pool.get_conn() as db_connection:
            db_connection.execute_insert_cur(sql)


class DBHelps(object):
    @staticmethod
    def insert_help(session_id, game_id, help_id):
        sql = f"""
                    INSERT INTO helps
                    (session_id, hint_id, game_id, not_sent, time_not_sent)
                    VALUES ({session_id}, {help_id}, '{game_id}', True, True)
              """
        with connection_pool.get_conn() as db_connection:
            return db_connection.execute_insert_cur(sql)

    @staticmethod
    def get_help_ids_per_game(session_id, game_id):
        sql = f"""
                    SELECT hint_id FROM helps
                    WHERE session_id = {session_id} AND game_id = '{game_id}'
              """
        with connection_pool.get_conn() as db_connection:
            rows = db_connection.execute_select_cur(sql)
            return [row[0] for row in rows] if rows else list()

    @staticmethod
    def get_not_sent_help_ids_per_game(session_id, game_id):
        sql = f"""
                    SELECT hint_id FROM helps
                    WHERE session_id = {session_id} AND game_id = '{game_id}' AND not_sent = True
              """
        with connection_pool.get_conn() as db_connection:
            rows = db_connection.execute_select_cur(sql)
            return [row[0] for row in rows] if rows else list()

    @staticmethod
    def get_time_not_sent_help_ids_per_game(session_id, game_id):
        sql = f"""
                    SELECT hint_id FROM helps
                    WHERE session_id = {session_id} AND game_id = '{game_id}' AND time_not_sent = True
              """
        with connection_pool.get_conn() as db_connection:
            rows = db_connection.execute_select_cur(sql)
            return [row[0] for row in rows] if rows else list()

    @staticmethod
    def update_bool_flag(session_id, game_id, help_id, header, value):
        sql = f"""
                    UPDATE helps
                    SET {header} = {value}
                    WHERE session_id = {session_id} AND game_id = '{game_id}' AND hint_id = {help_id}
              """
        with connection_pool.get_conn() as db_connection:
            db_connection.execute_insert_cur(sql)


class DBPenHelps(object):
    @staticmethod
    def insert_pen_help(session_id, game_id, pen_help_id):
        sql = f"""
                    INSERT INTO pen_helps
                    (session_id, pen_hint_id, game_id, not_sent)
                    VALUES ({session_id}, {pen_help_id}, '{game_id}', True)
              """
        with connection_pool.get_conn() as db_connection:
            return db_connection.execute_insert_cur(sql)

    @staticmethod
    def get_pen_help_ids_per_game(session_id, game_id):
        sql = f"""
                    SELECT pen_hint_id FROM pen_helps
                    WHERE session_id = {session_id} AND game_id = '{game_id}'
              """
        with connection_pool.get_conn() as db_connection:
            rows = db_connection.execute_select_cur(sql)
            return [row[0] for row in rows] if rows else list()

    @staticmethod
    def get_not_sent_pen_help_ids_per_game(session_id, game_id):
        sql = f"""
                    SELECT pen_hint_id FROM pen_helps
                    WHERE session_id = {session_id} AND game_id = '{game_id}' AND not_sent = True
              """
        with connection_pool.get_conn() as db_connection:
            rows = db_connection.execute_select_cur(sql)
            return [row[0] for row in rows] if rows else list()

    @staticmethod
    def update_bool_flag(session_id, game_id, pen_help_id, header, value):
        sql = f"""
                    UPDATE pen_helps
                    SET {header} = {value}
                    WHERE session_id = {session_id} AND game_id = '{game_id}' AND pen_hint_id = {pen_help_id}
              """
        with connection_pool.get_conn() as db_connection:
            db_connection.execute_insert_cur(sql)


class DBBonuses(object):
    @staticmethod
    def insert_bonus(session_id, game_id, bonus, level_id, info_not_sent, award_not_sent):
        bonus_name = bonus['Name'].encode('utf-8') if bonus['Name'] else "Бонус " + str(bonus['Number'])
        bonus_number = bonus['Number']
        bonus_id = bonus['BonusId']
        player = bonus['Answer']['Login'].encode('utf-8') if bonus['IsAnswered'] else ''
        code = bonus['Answer']['Answer'].encode('utf-8') if bonus['IsAnswered'] else 'NULL'
        sql = f"""
                    INSERT INTO bonuses
                    (session_id, bonus_id, game_id, info_not_sent, award_not_sent, level_id, code, bonus_name, bonus_number, player)
                    VALUES ({session_id}, {bonus_id}, '{game_id}', {info_not_sent}, {award_not_sent}, {level_id}, $${code}$$, $${bonus_name}$$, {bonus_number}, $${player}$$)
              """
        with connection_pool.get_conn() as db_connection:
            return db_connection.execute_insert_cur(sql)

    @staticmethod
    def get_bonus_ids_per_level(session_id, game_id, level_id):
        sql = f"""
                    SELECT bonus_id FROM bonuses
                    WHERE session_id = {session_id} AND game_id = '{game_id}' AND level_id = {level_id}
              """
        with connection_pool.get_conn() as db_connection:
            rows = db_connection.execute_select_cur(sql)
            return [row[0] for row in rows] if rows else list()

    @staticmethod
    def get_award_not_sent_bonus_ids_per_game(session_id, game_id):
        sql = f"""
                    SELECT DISTINCT bonus_id FROM bonuses
                    WHERE session_id = {session_id} AND game_id = '{game_id}' AND award_not_sent = True
              """
        with connection_pool.get_conn() as db_connection:
            rows = db_connection.execute_select_cur(sql)
            return [row[0] for row in rows] if rows else list()

    @staticmethod
    def get_award_sent_bonus_ids_per_game(session_id, game_id):
        sql = f"""
                    SELECT DISTINCT bonus_id FROM bonuses
                    WHERE session_id = {session_id} AND game_id = '{game_id}' AND award_not_sent = False
              """
        with connection_pool.get_conn() as db_connection:
            rows = db_connection.execute_select_cur(sql)
            return [row[0] for row in rows] if rows else list()

    @staticmethod
    def get_info_not_sent_bonus_ids_per_game(session_id, game_id):
        sql = f"""
                    SELECT DISTINCT bonus_id FROM bonuses
                    WHERE session_id = {session_id} AND game_id = '{game_id}' AND info_not_sent = True
              """
        with connection_pool.get_conn() as db_connection:
            rows = db_connection.execute_select_cur(sql)
            return [row[0] for row in rows] if rows else list()

    @staticmethod
    def get_info_sent_bonus_ids_per_game(session_id, game_id):
        sql = f"""
                    SELECT DISTINCT bonus_id FROM bonuses
                    WHERE session_id = {session_id} AND game_id = '{game_id}' AND info_not_sent = False
              """
        with connection_pool.get_conn() as db_connection:
            rows = db_connection.execute_select_cur(sql)
            return [row[0] for row in rows] if rows else list()

    @staticmethod
    def get_field_value(session_id, game_id, bonus_id, header):
        sql = f"SELECT {header} FROM bonuses WHERE session_id = {session_id} AND gameid = '{game_id}' AND bonus_id = {bonus_id}"
        with connection_pool.get_conn() as db_connection:
            rows = db_connection.execute_select_cur(sql)
            return rows[0][0]

    @staticmethod
    def update_bool_flag(session_id, game_id, bonus_id, header, value):
        sql = f"""
                    UPDATE bonuses
                    SET {header} = {value}
                    WHERE session_id = {session_id} AND game_id = '{game_id}' AND bonus_id = {bonus_id}
              """
        with connection_pool.get_conn() as db_connection:
            db_connection.execute_insert_cur(sql)

    @staticmethod
    def update_answer_info_not_sent(session_id, game_id, bonus, header, value):
        player = bonus['Answer']['Login'].encode('utf-8')
        code = bonus['Answer']['Answer'].encode('utf-8')
        bonus_id = bonus['BonusId']
        sql = f"""
                    UPDATE bonuses
                    SET {header} = {value}, code = $${code}$$, player = $${player}$$
                    WHERE session_id = {session_id} AND game_id = '{game_id}' AND bonus_id = {bonus_id}
              """
        with connection_pool.get_conn() as db_connection:
            db_connection.execute_insert_cur(sql)


class DBSectors(object):
    @staticmethod
    def insert_sector(session_id, game_id, sector, level_id, code='NULL', player=''):
        sector_id = sector['SectorId']
        sector_name = sector['Name'].encode('utf-8')
        sector_order = sector['Order']
        sql = f"""
                    INSERT INTO sectors
                    (session_id, sector_id, game_id, answer_info_not_sent, code, level_id, sector_name, sector_order, player)
                    VALUES ({session_id}, {sector_id}, '{game_id}', True, {code}, {level_id}, $${sector_name}$$, {sector_order}, $${player}$$)
              """
        with connection_pool.get_conn() as db_connection:
            return db_connection.execute_insert_cur(sql)

    @staticmethod
    def get_sector_ids_per_game(session_id, game_id):
        sql = f"""
                    SELECT sector_id FROM sectors
                    WHERE session_id = {session_id} AND game_id = '{game_id}'
              """
        with connection_pool.get_conn() as db_connection:
            rows = db_connection.execute_select_cur(sql)
            return [row[0] for row in rows] if rows else list()

    @staticmethod
    def get_answer_info_not_sent_sector_ids_per_game(session_id, game_id):
        sql = f"""
                    SELECT sector_id FROM sectors
                    WHERE session_id = {session_id} AND game_id = '{game_id}' AND answer_info_not_sent = True
              """
        with connection_pool.get_conn() as db_connection:
            rows = db_connection.execute_select_cur(sql)
            return [row[0] for row in rows] if rows else list()

    @staticmethod
    def get_answer_info_not_sent(session_id, game_id, sector_id):
        sql = f"SELECT answer_info_not_sent FROM sectors WHERE session_id = {session_id} AND game_id = '{game_id}' AND sector_id = {sector_id}"
        with connection_pool.get_conn() as db_connection:
            rows = db_connection.execute_select_cur(sql)
            return rows[0][0]

    @staticmethod
    def update_answer_info_not_sent(session_id, game_id, sector_id, active, code, player):
        sql = f"""
                    UPDATE sectors
                    SET answer_info_not_sent = {active}, code = $${code}$$, player = $${player}$$
                    WHERE session_id = {session_id} AND game_id = '{game_id}' AND sector_id = {sector_id}
              """
        with connection_pool.get_conn() as db_connection:
            db_connection.execute_insert_cur(sql)

    @staticmethod
    def update_level_last_code(session_id, game_id, sector_id, code, player):
        sql = f"""
                    UPDATE sectors
                    SET code = $${code}$$, player = $${player}$$
                    WHERE session_id = {session_id} AND game_id = '{game_id}' AND sector_id = {sector_id}
              """
        with connection_pool.get_conn() as db_connection:
            db_connection.execute_insert_cur(sql)


class DBMessages(object):
    @staticmethod
    def insert_message(session_id, game_id, message_id):
        sql = f"""
                    INSERT INTO messages
                    (session_id, message_id, game_id, message_not_sent)
                    VALUES ({session_id}, {message_id}, '{game_id}', True)
              """
        with connection_pool.get_conn() as db_connection:
            return db_connection.execute_insert_cur(sql)

    @staticmethod
    def get_message_ids_per_game(session_id, game_id):
        sql = f"""
                    SELECT message_id FROM messages
                    WHERE session_id = {session_id} AND game_id = '{game_id}'
              """
        with connection_pool.get_conn() as db_connection:
            rows = db_connection.execute_select_cur(sql)
            return [row[0] for row in rows] if rows else list()

    @staticmethod
    def get_not_sent_message_ids_per_game(session_id, game_id):
        sql = f"""
                    SELECT message_id FROM messages
                    WHERE session_id = {session_id} AND game_id = '{game_id}' AND message_not_sent = True
              """
        with connection_pool.get_conn() as db_connection:
            rows = db_connection.execute_select_cur(sql)
            return [row[0] for row in rows] if rows else list()

    @staticmethod
    def get_message_not_sent(session_id, game_id, message_id):
        sql = f"SELECT message_not_sent FROM messages WHERE session_id = {session_id} AND game_id = '{game_id}' AND message_id = {message_id}"
        with connection_pool.get_conn() as db_connection:
            rows = db_connection.execute_select_cur(sql)
            return rows[0][0]

    @staticmethod
    def update_message_not_sent(session_id, game_id, message_id, active):
        sql = f"""
                    UPDATE messages
                    SET message_not_sent = {active}
                    WHERE session_id = {session_id} AND game_id = '{game_id}' AND message_id = {message_id}
              """
        with connection_pool.get_conn() as db_connection:
            db_connection.execute_insert_cur(sql)


class DB(object):
    @staticmethod
    def get_tags_list():
        sql = "SELECT DISTINCT * FROM tags_to_cut"
        with connection_pool.get_conn() as db_connection:
            rows = db_connection.execute_select_cur(sql)
            return [row[0] for row in rows]

    @staticmethod
    def insert_tag_in_tags_list(tag_to_add):
        sql = f"""
                    INSERT INTO tags_to_cut (tag)
                    VALUES ('{tag_to_add}')
              """
        with connection_pool.get_conn() as db_connection:
            return db_connection.execute_insert_cur(sql)

    @staticmethod
    def get_main_bot_token():
        sql = "SELECT bot_token FROM bot_tokens WHERE type = 'main'"
        with connection_pool.get_conn() as db_connection:
            rows = db_connection.execute_select_cur(sql)
            return rows[0][0]

    @staticmethod
    def get_location_bot_token_by_number(number):
        sql = f"SELECT bot_token FROM bot_tokens WHERE type = 'location' and number = '{number}'"
        with connection_pool.get_conn() as db_connection:
            rows = db_connection.execute_select_cur(sql)
            return rows[0][0]

    @staticmethod
    def get_additional_chat_ids():
        sql = f"SELECT add_chat_id FROM additional_chats"
        with connection_pool.get_conn() as db_connection:
            rows = db_connection.execute_select_cur(sql)
            return [row[0] for row in rows] if rows else list()

    @staticmethod
    def insert_add_chat_id(main_chat_id, add_chat_id):
        sql = f"INSERT INTO additional_chats (add_chat_id, session_id) VALUES ({add_chat_id}, {main_chat_id})"
        with connection_pool.get_conn() as db_connection:
            return db_connection.execute_insert_cur(sql)

    @staticmethod
    def delete_add_chat_id(add_chat_id):
        sql = f"DELETE FROM additional_chats WHERE add_chat_id = {add_chat_id}"
        with connection_pool.get_conn() as db_connection:
            db_connection.execute_insert_cur(sql)

    @staticmethod
    def delete_add_chat_ids(session_id):
        sql = f"DELETE FROM additional_chats WHERE session_id = {session_id}"
        with connection_pool.get_conn() as db_connection:
            db_connection.execute_insert_cur(sql)

    @staticmethod
    def get_main_chat_id_via_add(add_chat_id):
        sql = f"SELECT session_id FROM additional_chats WHERE add_chat_id = {add_chat_id}"
        with connection_pool.get_conn() as db_connection:
            rows = db_connection.execute_select_cur(sql)
            return rows[0][0] if rows else None

    @staticmethod
    def get_add_chat_ids_for_main(main_chat_id):
        sql = f"SELECT add_chat_id FROM additional_chats WHERE session_id = {main_chat_id}"
        with connection_pool.get_conn() as db_connection:
            rows = db_connection.execute_select_cur(sql)
            return [row[0] for row in rows] if rows else list()

    @staticmethod
    def cleanup_for_ended_game(session_id, game_id):
        sql = f"""
                    DELETE FROM levels WHERE session_id = {session_id} AND game_id = '{game_id}';
                    DELETE FROM sectors WHERE session_id = {session_id} AND game_id = '{game_id}';
                    DELETE FROM bonuses WHERE session_id = {session_id} AND game_id = '{game_id}';
                    DELETE FROM helps WHERE session_id = {session_id} AND game_id = '{game_id}';
                    DELETE FROM penhelps WHERE session_id = {session_id} AND game_id = '{game_id}';
                    DELETE FROM messages WHERE session_id = {session_id} AND game_id = '{game_id}';
              """
        with connection_pool.get_conn() as db_connection:
            db_connection.execute_insert_cur(sql)

    # @staticmethod
    # def get_sectors_per_game(session_id, game_id):
    #     sql = """
    #             SELECT l.levelname, l.number, s.code, s.sectorname, s.sectororder, s.player
    #             FROM levels l JOIN sectors s ON
    #             (
    #             l.levelid = s.levelid
    #             AND l.sessionid = s.sessionid
    #             AND l.gameid = s.gameid
    #             )
    #             WHERE
    #             l.sessionid = %s
    #             AND l.gameid = '%s'
    #             ORDER BY l.number, s.sectororder;
    #             """ % (session_id, game_id)
    #     with connection_pool.get_conn() as db_connection:
    #         rows = db_connection.execute_dict_select_cur(sql)
    #         return rows
    #
    # @staticmethod
    # def get_bonuses_per_game(session_id, game_id):
    #     sql = """
    #                 SELECT l.levelname, l.number, b.code, b.bonusname, b.bonusnumber, b.player
    #                 FROM levels l JOIN bonuses b ON
    #                 (
    #                 l.levelid = b.levelid
    #                 AND l.sessionid = b.sessionid
    #                 AND l.gameid = b.gameid
    #                 )
    #                 WHERE
    #                 l.sessionid = %s
    #                 AND l.gameid = '%s'
    #                 ORDER BY l.number, b.bonusnumber;
    #                 """ % (session_id, game_id)
    #     with connection_pool.get_conn() as db_connection:
    #         rows = db_connection.execute_dict_select_cur(sql)
    #         return rows
    #
    # @staticmethod
    # def get_sectors_per_level(session_id, game_id, level_number):
    #     sql = """
    #             SELECT l.levelname, l.number, s.code, s.sectorname, s.sectororder, s.player
    #             FROM levels l JOIN sectors s ON
    #             (
    #             l.levelid = s.levelid
    #             AND l.sessionid = s.sessionid
    #             AND l.gameid = s.gameid
    #             )
    #             WHERE
    #             l.sessionid = %s
    #             AND l.gameid = '%s'
    #             AND l.number = %s
    #             ORDER BY l.number, s.sectororder;
    #             """ % (session_id, game_id, level_number)
    #     with connection_pool.get_conn() as db_connection:
    #         rows = db_connection.execute_dict_select_cur(sql)
    #         return rows
    #
    # @staticmethod
    # def get_bonuses_per_level(session_id, game_id, level_number):
    #     sql = """
    #                 SELECT l.levelname, l.number, b.code, b.bonusname, b.bonusnumber, b.player
    #                 FROM levels l JOIN bonuses b ON
    #                 (
    #                 l.levelid = b.levelid
    #                 AND l.sessionid = b.sessionid
    #                 AND l.gameid = b.gameid
    #                 )
    #                 WHERE
    #                 l.sessionid = %s
    #                 AND l.gameid = '%s'
    #                 AND l.number = %s
    #                 ORDER BY l.number, b.bonusnumber;
    #                 """ % (session_id, game_id, level_number)
    #     with connection_pool.get_conn() as db_connection:
    #         rows = db_connection.execute_dict_select_cur(sql)
    #         return rows

    @staticmethod
    def get_gameurls_levels():
        sql = """
                    SELECT DISTINCT sc.game_url, sc.login_url, sc.session_id, sc.game_id
                    FROM session_config sc JOIN levels l ON
                    (
                        l.session_id = sc.session_id
                        AND l.game_id = sc.game_id
                    )
              """
        with connection_pool.get_conn() as db_connection:
            rows = db_connection.execute_dict_select_cur(sql)
            return rows

    @staticmethod
    def get_gameurls_bonuses():
        sql = """
                    SELECT DISTINCT sc.game_url, sc.login_url, sc.session_id, sc.game_id
                    FROM session_config sc JOIN bonuses b ON
                    (
                        b.session_id = sc.session_id
                        AND b.game_id = sc.game_id
                    )
              """
        with connection_pool.get_conn() as db_connection:
            rows = db_connection.execute_dict_select_cur(sql)
            return rows

    @staticmethod
    def get_gameurls_sectors():
        sql = """
                    SELECT DISTINCT sc.game_url, sc.login_url, sc.session_id, sc.game_id
                    FROM session_config sc JOIN sectors s ON
                    (
                        s.session_id = sc.session_id
                        AND s.game_id = sc.game_id
                    )
              """
        with connection_pool.get_conn() as db_connection:
            rows = db_connection.execute_dict_select_cur(sql)
            return rows

    @staticmethod
    def get_gameurls_helps():
        sql = """
                        SELECT DISTINCT sc.game_url, sc.login_url, sc.session_id, sc.game_id
                        FROM session_config sc JOIN helps h ON
                        (
                        h.session_id = sc.session_id
                        AND h.game_id = sc.game_id
                        )
                        """
        with connection_pool.get_conn() as db_connection:
            rows = db_connection.execute_dict_select_cur(sql)
            return rows

    @staticmethod
    def get_gameurls_messages():
        sql = """
                    SELECT DISTINCT sc.game_url, sc.login_url, sc.session_id, sc.game_id
                    FROM session_config sc JOIN messages m ON
                    (
                        m.session_id = sc.session_id
                        AND m.game_id = sc.game_id
                    )
              """
        with connection_pool.get_conn() as db_connection:
            rows = db_connection.execute_dict_select_cur(sql)
            return rows

    # @staticmethod
    # def get_gameids_for_builder_list():
    #     sql = "SELECT DISTINCT * FROM gamesforbuilder"
    #     with connection_pool.get_conn() as db_connection:
    #         rows = db_connection.execute_select_cur(sql)
    #         return [row[0] for row in rows]
    #
    # @staticmethod
    # def insert_gameids_for_builder(gameid):
    #     sql = """
    #             INSERT INTO gamesforbuilder (gameid)
    #             VALUES ('%s')""" % gameid
    #     with connection_pool.get_conn() as db_connection:
    #         return db_connection.execute_insert_cur(sql)
    #
    # @staticmethod
    # def insert_game_transfer_row(gameid, header, data):
    #     sql = """INSERT INTO gametransferids (gameid, %s)
    #             VALUES (%s, '%s')""" % (header, gameid, data)
    #     with connection_pool.get_conn() as db_connection:
    #         db_connection.execute_insert_cur(sql)
    #
    # @staticmethod
    # def get_game_transfer_ids(gameid, header):
    #     sql = "SELECT %s FROM gametransferids WHERE gameid = %s" % (header, gameid)
    #     with connection_pool.get_conn() as db_connection:
    #         rows = db_connection.execute_select_cur(sql)
    #         return [row[0] for row in rows] if rows else list()
    #
    # @staticmethod
    # def clean_game_transfer_ids(gameid):
    #     sql = "DELETE FROM gametransferids WHERE gameid = %s" % gameid
    #     with connection_pool.get_conn() as db_connection:
    #         return db_connection.execute_insert_cur(sql)
