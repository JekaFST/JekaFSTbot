# -*- coding: utf-8 -*-
import json
from DBConnectionPool import ConnectionPool


connection_pool = ConnectionPool()
connection_pool.init_pool()


class DBSession(object):
    @staticmethod
    def get_sessions_ids():
        sql = "SELECT sessionid FROM sessionconfig"
        with connection_pool.get_conn() as db_connection:
            rows = db_connection.execute_select_cur(sql)
            return [row[0] for row in rows] if rows else list()

    @staticmethod
    def insert_session(main_chat_id):
        sql = """INSERT INTO SessionConfig
                (SessionId, Active, Login, Password, ENDomain, GameId, ChannelName, Cookie, GameURL, LoginURL,
                GameModelStatus, UseChannel, StopUpdater, PutUpdaterTask, Delay, SendCodes, StormGame, CurrLevelId,
                sectorstoclose, sectorsmessageid, Locations, llmessageids)
                VALUES (%s, False, '', '', '', '', '', '', NULL, NULL, '', False, True, NULL, 2, True, NULL, NULL,
                '', NULL, '{}', '{}')
              """ % main_chat_id
        with connection_pool.get_conn() as db_connection:
            return db_connection.execute_insert_cur(sql)

    @staticmethod
    def get_session(session_id):
        sql = "SELECT * FROM SessionConfig WHERE sessionid = %s" % session_id
        with connection_pool.get_conn() as db_connection:
            rows = db_connection.execute_dict_select_cur(sql)
            return rows[0] if rows else None

    @staticmethod
    def delete_session(session_id):
        sql = "DELETE FROM SessionConfig WHERE sessionid = %s" % session_id
        with connection_pool.get_conn() as db_connection:
            db_connection.execute_insert_cur(sql)

    @staticmethod
    def get_all_sessions():
        sql = "SELECT * FROM SessionConfig"
        with connection_pool.get_conn() as db_connection:
            rows = db_connection.execute_dict_select_cur(sql)
            return rows if rows else list()

    @staticmethod
    def update_session_urls(sessionid, urls):
        sql = """UPDATE SessionConfig
                SET gameurl = '%s', loginurl = '%s'
                WHERE sessionid = %s
              """ % (urls['game_url'], urls['login_url'], sessionid)
        with connection_pool.get_conn() as db_connection:
            return db_connection.execute_insert_cur(sql)

    @staticmethod
    def drop_session_vars(session_id):
        sql = """UPDATE SessionConfig
                SET CurrLevelId = NULL, GameURL = NULL, LoginURL = NULL, StormGame = NULL,
                SendCodes = True, GameModelStatus = '', PutUpdaterTask = Null, StopUpdater = True, Locations = '{}', llmessageids = '{}'
                WHERE sessionid = %s
              """ % session_id
        with connection_pool.get_conn() as db_connection:
            db_connection.execute_insert_cur(sql)

    @staticmethod
    def get_locations(session_id):
        sql = "SELECT locations FROM SessionConfig WHERE sessionid = %s" % session_id
        with connection_pool.get_conn() as db_connection:
            rows = db_connection.execute_select_cur(sql)
            return json.loads(rows[0][0])

    @staticmethod
    def update_json_field(session_id, header, value):
        sql = """UPDATE SessionConfig
                        SET %s = '%s'
                        WHERE sessionid = %s
                      """ % (header, json.dumps(value), session_id)
        with connection_pool.get_conn() as db_connection:
            return db_connection.execute_insert_cur(sql)

    @staticmethod
    def update_text_field(sessionid, header, value):
        sql = """UPDATE SessionConfig
                        SET %s = $$%s$$
                        WHERE sessionid = %s
                      """ % (header, value, sessionid)
        with connection_pool.get_conn() as db_connection:
            return db_connection.execute_insert_cur(sql)

    @staticmethod
    def get_field_value(sessionid, header):
        sql = "SELECT %s FROM SessionConfig WHERE sessionid = %s" % (header, sessionid)
        with connection_pool.get_conn() as db_connection:
            rows = db_connection.execute_select_cur(sql)
            return rows[0][0]

    @staticmethod
    def update_bool_flag(sessionid, header, value):
        sql = """UPDATE SessionConfig
                SET %s = %s
                WHERE sessionid = %s
                """ % (header, value, sessionid)
        with connection_pool.get_conn() as db_connection:
            return db_connection.execute_insert_cur(sql)

    @staticmethod
    def update_int_field(sessionid, header, value):
        sql = """UPDATE SessionConfig
                SET %s = %s
                WHERE sessionid = %s
                """ % (header, value, sessionid)
        with connection_pool.get_conn() as db_connection:
            return db_connection.execute_insert_cur(sql)


class DBLevels(object):
    @staticmethod
    def insert_level(session_id, game_id, level):
        name = level['LevelName'].encode('utf-8') if level['LevelName'] else ''
        sql = """INSERT INTO levels
                    (SessionId, LevelId, GameId, Number, IsPassed, Dismissed, TimeToUpSent, levelname)
                    VALUES (%s, %s, '%s', %s, %s, %s, False, $$%s$$)
                """ % (session_id, level['LevelId'], game_id, level['LevelNumber'], level['IsPassed'], level['Dismissed'], name)
        with connection_pool.get_conn() as db_connection:
            return db_connection.execute_insert_cur(sql)

    @staticmethod
    def get_dismissed_level_ids(session_id, game_id):
        sql = """SELECT LevelId FROM levels
                    WHERE sessionid = %s AND gameid = '%s' AND dismissed = True
                    """ % (session_id, game_id)
        with connection_pool.get_conn() as db_connection:
            rows = db_connection.execute_select_cur(sql)
            return [row[0] for row in rows] if rows else list()

    @staticmethod
    def get_passed_level_ids(session_id, game_id):
        sql = """SELECT LevelId FROM levels
                        WHERE sessionid = %s AND gameid = '%s' AND ispassed = True
                        """ % (session_id, game_id)
        with connection_pool.get_conn() as db_connection:
            rows = db_connection.execute_select_cur(sql)
            return [row[0] for row in rows] if rows else list()

    @staticmethod
    def update_bool_field(session_id, game_id, level_id, header, active):
        sql = """UPDATE Levels
                SET %s = %s
                WHERE sessionid = %s AND gameid = '%s' AND levelid = %s
                """ % (header, active, session_id, game_id, level_id)
        with connection_pool.get_conn() as db_connection:
            db_connection.execute_insert_cur(sql)

    @staticmethod
    def get_level_ids_per_game(session_id, game_id):
        sql = """SELECT LevelId FROM Levels
                    WHERE sessionid = %s AND gameid = '%s'
                    """ % (session_id, game_id)
        with connection_pool.get_conn() as db_connection:
            rows = db_connection.execute_select_cur(sql)
            return [row[0] for row in rows] if rows else list()

    @staticmethod
    def get_time_to_up_sent(session_id, level_id):
        sql = "SELECT timetoupsent FROM Levels WHERE sessionid = %s AND levelid = %s" % (session_id, level_id)
        with connection_pool.get_conn() as db_connection:
            rows = db_connection.execute_select_cur(sql)
            return rows[0][0]

    @staticmethod
    def get_level_number(session_id, level_id):
        sql = "SELECT number FROM Levels WHERE sessionid = %s AND levelid = %s" % (session_id, level_id)
        with connection_pool.get_conn() as db_connection:
            rows = db_connection.execute_select_cur(sql)
            return rows[0][0]

    @staticmethod
    def update_time_to_up_sent(session_id, level_id, active):
        sql = """UPDATE Levels
                SET timetoupsent = %s
                WHERE sessionid = %s AND levelid = %s
                """ % (active, session_id, level_id)
        with connection_pool.get_conn() as db_connection:
            db_connection.execute_insert_cur(sql)


class DBHelps(object):
    @staticmethod
    def insert_help(session_id, game_id, help_id):
        sql = """INSERT INTO helps
                        (SessionId, HintId, GameId, NotSent, TimeNotSent)
                        VALUES (%s, %s, '%s', True, True)
                    """ % (session_id, help_id, game_id)
        with connection_pool.get_conn() as db_connection:
            return db_connection.execute_insert_cur(sql)

    @staticmethod
    def get_help_ids_per_game(session_id, game_id):
        sql = """SELECT HintId FROM helps
                        WHERE sessionid = %s AND gameid = '%s'
                        """ % (session_id, game_id)
        with connection_pool.get_conn() as db_connection:
            rows = db_connection.execute_select_cur(sql)
            return [row[0] for row in rows] if rows else list()

    @staticmethod
    def get_not_sent_help_ids_per_game(session_id, game_id):
        sql = """SELECT HintId FROM helps
                            WHERE sessionid = %s AND gameid = '%s' AND notsent = True
                            """ % (session_id, game_id)
        with connection_pool.get_conn() as db_connection:
            rows = db_connection.execute_select_cur(sql)
            return [row[0] for row in rows] if rows else list()

    @staticmethod
    def get_time_not_sent_help_ids_per_game(session_id, game_id):
        sql = """SELECT HintId FROM helps
                            WHERE sessionid = %s AND gameid = '%s' AND timenotsent = True
                            """ % (session_id, game_id)
        with connection_pool.get_conn() as db_connection:
            rows = db_connection.execute_select_cur(sql)
            return [row[0] for row in rows] if rows else list()

    @staticmethod
    def update_bool_flag(session_id, game_id, help_id, header, value):
        sql = """UPDATE Helps
                    SET %s = %s
                    WHERE sessionid = %s AND gameid = '%s' AND hintid = %s
                    """ % (header, value, session_id, game_id, help_id)
        with connection_pool.get_conn() as db_connection:
            db_connection.execute_insert_cur(sql)


class DBPenHelps(object):
    @staticmethod
    def insert_pen_help(session_id, game_id, pen_help_id):
        sql = """INSERT INTO penhelps
                        (SessionId, penhintid, GameId, NotSent)
                        VALUES (%s, %s, '%s', True)
                    """ % (session_id, pen_help_id, game_id)
        with connection_pool.get_conn() as db_connection:
            return db_connection.execute_insert_cur(sql)

    @staticmethod
    def get_pen_help_ids_per_game(session_id, game_id):
        sql = """SELECT penhintid FROM penhelps
                        WHERE sessionid = %s AND gameid = '%s'
                        """ % (session_id, game_id)
        with connection_pool.get_conn() as db_connection:
            rows = db_connection.execute_select_cur(sql)
            return [row[0] for row in rows] if rows else list()

    @staticmethod
    def get_not_sent_pen_help_ids_per_game(session_id, game_id):
        sql = """SELECT penhintid FROM penhelps
                            WHERE sessionid = %s AND gameid = '%s' AND notsent = True
                            """ % (session_id, game_id)
        with connection_pool.get_conn() as db_connection:
            rows = db_connection.execute_select_cur(sql)
            return [row[0] for row in rows] if rows else list()

    @staticmethod
    def update_bool_flag(session_id, game_id, pen_help_id, header, value):
        sql = """UPDATE penhelps
                    SET %s = %s
                    WHERE sessionid = %s AND gameid = '%s' AND penhintid = %s
                    """ % (header, value, session_id, game_id, pen_help_id)
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
        sql = """INSERT INTO bonuses
                        (SessionId, BonusId, GameId, InfoNotSent, AwardNotSent, levelid, code, bonusname, bonusnumber, player)
                        VALUES (%s, %s, '%s', %s, %s, %s, $$%s$$, $$%s$$, %s, $$%s$$)
                    """ % (session_id, bonus_id, game_id, info_not_sent, award_not_sent, level_id, code, bonus_name, bonus_number, player)
        with connection_pool.get_conn() as db_connection:
            return db_connection.execute_insert_cur(sql)

    @staticmethod
    def get_bonus_ids_per_level(session_id, game_id, level_id):
        sql = """SELECT BonusId FROM bonuses
                            WHERE sessionid = %s AND gameid = '%s' AND levelid = %s
                            """ % (session_id, game_id, level_id)
        with connection_pool.get_conn() as db_connection:
            rows = db_connection.execute_select_cur(sql)
            return [row[0] for row in rows] if rows else list()

    @staticmethod
    def get_award_not_sent_bonus_ids_per_game(session_id, game_id):
        sql = """SELECT DISTINCT BonusId FROM bonuses
                        WHERE sessionid = %s AND gameid = '%s' AND awardnotsent = True
                        """ % (session_id, game_id)
        with connection_pool.get_conn() as db_connection:
            rows = db_connection.execute_select_cur(sql)
            return [row[0] for row in rows] if rows else list()

    @staticmethod
    def get_award_sent_bonus_ids_per_game(session_id, game_id):
        sql = """SELECT DISTINCT BonusId FROM bonuses
                            WHERE sessionid = %s AND gameid = '%s' AND awardnotsent = False
                            """ % (session_id, game_id)
        with connection_pool.get_conn() as db_connection:
            rows = db_connection.execute_select_cur(sql)
            return [row[0] for row in rows] if rows else list()

    @staticmethod
    def get_info_not_sent_bonus_ids_per_game(session_id, game_id):
        sql = """SELECT DISTINCT BonusId FROM bonuses
                        WHERE sessionid = %s AND gameid = '%s' AND infonotsent = True
                        """ % (session_id, game_id)
        with connection_pool.get_conn() as db_connection:
            rows = db_connection.execute_select_cur(sql)
            return [row[0] for row in rows] if rows else list()

    @staticmethod
    def get_info_sent_bonus_ids_per_game(session_id, game_id):
        sql = """SELECT DISTINCT BonusId FROM bonuses
                            WHERE sessionid = %s AND gameid = '%s' AND infonotsent = False
                            """ % (session_id, game_id)
        with connection_pool.get_conn() as db_connection:
            rows = db_connection.execute_select_cur(sql)
            return [row[0] for row in rows] if rows else list()

    @staticmethod
    def get_field_value(session_id, game_id, bonus_id, header):
        sql = "SELECT %s FROM Bonuses WHERE sessionid = %s AND gameid = '%s' AND bonusid = %s" % \
              (header, session_id, game_id, bonus_id)
        with connection_pool.get_conn() as db_connection:
            rows = db_connection.execute_select_cur(sql)
            return rows[0][0]

    @staticmethod
    def update_bool_flag(session_id, game_id, bonus_id, header, value):
        sql = """UPDATE Bonuses
                SET %s = %s
                WHERE sessionid = %s AND gameid = '%s' AND bonusid = %s
                """ % (header, value, session_id, game_id, bonus_id)
        with connection_pool.get_conn() as db_connection:
            db_connection.execute_insert_cur(sql)

    @staticmethod
    def update_answer_info_not_sent(session_id, game_id, bonus, header, value):
        player = bonus['Answer']['Login'].encode('utf-8')
        code = bonus['Answer']['Answer'].encode('utf-8')
        bonus_id = bonus['BonusId']
        sql = """UPDATE Bonuses
                        SET %s = %s, code = $$%s$$, player = $$%s$$
                        WHERE sessionid = %s AND gameid = '%s' AND bonusid = %s
                        """ % (header, value, code, player, session_id, game_id, bonus_id)
        with connection_pool.get_conn() as db_connection:
            db_connection.execute_insert_cur(sql)


class DBSectors(object):
    @staticmethod
    def insert_sector(session_id, game_id, sector, level_id, code='NULL', player=''):
        sector_id = sector['SectorId']
        sector_name = sector['Name'].encode('utf-8')
        sector_order = sector['Order']
        sql = """INSERT INTO sectors
                    (SessionId, SectorId, GameId, AnswerInfoNotSent, code, levelid, sectorname, sectororder, player)
                    VALUES (%s, %s, '%s', True, %s, %s, $$%s$$, %s, '%s')
                """ % (session_id, sector_id, game_id, code, level_id, sector_name, sector_order, player)
        with connection_pool.get_conn() as db_connection:
            return db_connection.execute_insert_cur(sql)

    @staticmethod
    def get_sector_ids_per_game(session_id, game_id):
        sql = """SELECT SectorId FROM sectors
                    WHERE sessionid = %s AND gameid = '%s'
                    """ % (session_id, game_id)
        with connection_pool.get_conn() as db_connection:
            rows = db_connection.execute_select_cur(sql)
            return [row[0] for row in rows] if rows else list()

    @staticmethod
    def get_answer_info_not_sent_sector_ids_per_game(session_id, game_id):
        sql = """SELECT SectorId FROM sectors
                    WHERE sessionid = %s AND gameid = '%s' AND answerinfonotsent = True
                    """ % (session_id, game_id)
        with connection_pool.get_conn() as db_connection:
            rows = db_connection.execute_select_cur(sql)
            return [row[0] for row in rows] if rows else list()

    @staticmethod
    def get_answer_info_not_sent(session_id, game_id, sector_id):
        sql = "SELECT answerinfonotsent FROM Sectors WHERE sessionid = %s AND gameid = '%s' AND sectorid = %s" % \
              (session_id, game_id, sector_id)
        with connection_pool.get_conn() as db_connection:
            rows = db_connection.execute_select_cur(sql)
            return rows[0][0]

    @staticmethod
    def update_answer_info_not_sent(session_id, game_id, sector_id, active, code, player):
        sql = """UPDATE Sectors
                    SET answerinfonotsent = %s, code = $$%s$$, player = $$%s$$
                    WHERE sessionid = %s AND gameid = '%s' AND sectorid = %s
                    """ % (active, code, player, session_id, game_id, sector_id)
        with connection_pool.get_conn() as db_connection:
            db_connection.execute_insert_cur(sql)

    @staticmethod
    def update_level_last_code(session_id, game_id, sector_id, code, player):
        sql = """UPDATE Sectors
                        SET code = $$%s$$, player = $$%s$$
                        WHERE sessionid = %s AND gameid = '%s' AND sectorid = %s
                        """ % (code, player, session_id, game_id, sector_id)
        with connection_pool.get_conn() as db_connection:
            db_connection.execute_insert_cur(sql)


class DBMessages(object):
    @staticmethod
    def insert_message(session_id, game_id, message_id):
        sql = """INSERT INTO messages
                    (SessionId, MessageId, GameId, MessageNotSent)
                    VALUES (%s, %s, '%s', True)
                """ % (session_id, message_id, game_id)
        with connection_pool.get_conn() as db_connection:
            return db_connection.execute_insert_cur(sql)

    @staticmethod
    def get_message_ids_per_game(session_id, game_id):
        sql = """SELECT MessageId FROM messages
                    WHERE sessionid = %s AND gameid = '%s'
                    """ % (session_id, game_id)
        with connection_pool.get_conn() as db_connection:
            rows = db_connection.execute_select_cur(sql)
            return [row[0] for row in rows] if rows else list()

    @staticmethod
    def get_not_sent_message_ids_per_game(session_id, game_id):
        sql = """SELECT MessageId FROM messages
                        WHERE sessionid = %s AND gameid = '%s' AND messagenotsent = True
                        """ % (session_id, game_id)
        with connection_pool.get_conn() as db_connection:
            rows = db_connection.execute_select_cur(sql)
            return [row[0] for row in rows] if rows else list()

    @staticmethod
    def get_message_not_sent(session_id, game_id, message_id):
        sql = "SELECT messagenotsent FROM Messages WHERE sessionid = %s AND gameid = '%s' AND messageid = %s" % \
              (session_id, game_id, message_id)
        with connection_pool.get_conn() as db_connection:
            rows = db_connection.execute_select_cur(sql)
            return rows[0][0]

    @staticmethod
    def update_message_not_sent(session_id, game_id, message_id, active):
        sql = """UPDATE Messages
                SET messagenotsent = %s
                WHERE sessionid = %s AND gameid = '%s' AND messageid = %s
                """ % (active, session_id, game_id, message_id)
        with connection_pool.get_conn() as db_connection:
            db_connection.execute_insert_cur(sql)


class DB(object):
    @staticmethod
    def get_tags_list():
        sql = "SELECT DISTINCT * FROM TagsToCut"
        with connection_pool.get_conn() as db_connection:
            rows = db_connection.execute_select_cur(sql)
            return [row[0] for row in rows]

    @staticmethod
    def insert_tag_in_tags_list(tag_to_add):
        sql = """
                INSERT INTO TagsToCut (Tag)
                VALUES ('%s')""" % tag_to_add
        with connection_pool.get_conn() as db_connection:
            return db_connection.execute_insert_cur(sql)

    @staticmethod
    def get_main_bot_token():
        sql = "SELECT BotToken FROM BotTokens WHERE type = 'main'"
        with connection_pool.get_conn() as db_connection:
            rows = db_connection.execute_select_cur(sql)
            return rows[0][0]

    @staticmethod
    def get_location_bot_token_by_number(number):
        sql = "SELECT BotToken FROM BotTokens WHERE type = 'location' and number = '%s'" % number
        with connection_pool.get_conn() as db_connection:
            rows = db_connection.execute_select_cur(sql)
            return rows[0][0]

    @staticmethod
    def get_allowed_chat_ids():
        sql_main = "SELECT DISTINCT ChatId FROM AllowedChats"
        sql_add = "SELECT AddChatId FROM AllowedChats WHERE AddChatId IS NOT NULL"
        with connection_pool.get_conn() as db_connection:
            main_rows = db_connection.execute_select_cur(sql_main)
            add_rows = db_connection.execute_select_cur(sql_add)
            return [row[0] for row in main_rows] if main_rows else list(), [row[0] for row in add_rows] if add_rows else list()

    @staticmethod
    def insert_main_chat_id(main_chat_id):
        sql = "INSERT INTO AllowedChats (ChatId, AddChatId, AllowedGameIds) VALUES (%s, %s, '')" % (str(main_chat_id), 'NULL')
        with connection_pool.get_conn() as db_connection:
            return db_connection.execute_insert_cur(sql)

    @staticmethod
    def insert_add_chat_id(main_chat_id, add_chat_id):
        sql = "INSERT INTO AllowedChats (ChatId, AddChatId, AllowedGameIds) VALUES (%s, %s, '')" % (str(main_chat_id), str(add_chat_id))
        with connection_pool.get_conn() as db_connection:
            return db_connection.execute_insert_cur(sql)

    @staticmethod
    def delete_add_chat_id(add_chat_id):
        sql = "DELETE FROM AllowedChats WHERE AddChatId = %s" % str(add_chat_id)
        with connection_pool.get_conn() as db_connection:
            db_connection.execute_insert_cur(sql)

    @staticmethod
    def delete_add_chat_ids(session_id):
        sql = "DELETE FROM AllowedChats WHERE chatid = %s AND AddChatId IS NOT NULL" % str(session_id)
        with connection_pool.get_conn() as db_connection:
            db_connection.execute_insert_cur(sql)

    @staticmethod
    def get_main_chat_id_via_add(add_chat_id):
        sql = "SELECT ChatId FROM AllowedChats WHERE AddChatId = %s" % str(add_chat_id)
        with connection_pool.get_conn() as db_connection:
            rows = db_connection.execute_select_cur(sql)
            return rows[0][0] if rows else None

    @staticmethod
    def get_add_chat_ids_for_main(main_chat_id):
        sql = "SELECT AddChatId FROM AllowedChats WHERE ChatId = %s AND AddChatId IS NOT NULL" % str(main_chat_id)
        with connection_pool.get_conn() as db_connection:
            rows = db_connection.execute_select_cur(sql)
            return [row[0] for row in rows] if rows else list()

    @staticmethod
    def get_allowed_game_ids(main_chat_id):
        sql = "SELECT AllowedGameIds FROM AllowedChats WHERE ChatId = %s AND AddChatId IS NULL" % str(main_chat_id)
        with connection_pool.get_conn() as db_connection:
            rows = db_connection.execute_select_cur(sql)
            return rows[0][0] if rows else list()

    @staticmethod
    def update_allowed_game_ids(main_chat_id, allowed_game_ids):
        sql = "UPDATE AllowedChats SET AllowedGameIds = '%s' WHERE ChatId = %s AND AddChatId IS NULL" \
              % (allowed_game_ids, str(main_chat_id))
        with connection_pool.get_conn() as db_connection:
            return db_connection.execute_insert_cur(sql)

    @staticmethod
    def cleanup_for_ended_game(session_id, game_id):
        sql = """
                DELETE FROM levels WHERE sessionid = %s AND gameid = '%s';
                DELETE FROM sectors WHERE sessionid = %s AND gameid = '%s';
                DELETE FROM bonuses WHERE sessionid = %s AND gameid = '%s';
                DELETE FROM helps WHERE sessionid = %s AND gameid = '%s';
                DELETE FROM penhelps WHERE sessionid = %s AND gameid = '%s';
                DELETE FROM messages WHERE sessionid = %s AND gameid = '%s';
                """ % (session_id, game_id, session_id, game_id, session_id, game_id, session_id, game_id,
                       session_id, game_id, session_id, game_id)
        with connection_pool.get_conn() as db_connection:
            db_connection.execute_insert_cur(sql)

    @staticmethod
    def get_sectors_per_game(session_id, game_id):
        sql = """
                SELECT l.levelname, l.number, s.code, s.sectorname, s.sectororder, s.player
                FROM levels l JOIN sectors s ON
                (
                l.levelid = s.levelid
                AND l.sessionid = s.sessionid
                AND l.gameid = s.gameid
                )
                WHERE
                l.sessionid = %s
                AND l.gameid = '%s'
                ORDER BY l.number, s.sectororder;
                """ % (session_id, game_id)
        with connection_pool.get_conn() as db_connection:
            rows = db_connection.execute_dict_select_cur(sql)
            return rows

    @staticmethod
    def get_bonuses_per_game(session_id, game_id):
        sql = """
                    SELECT l.levelname, l.number, b.code, b.bonusname, b.bonusnumber, b.player
                    FROM levels l JOIN bonuses b ON
                    (
                    l.levelid = b.levelid
                    AND l.sessionid = b.sessionid
                    AND l.gameid = b.gameid
                    )
                    WHERE
                    l.sessionid = %s
                    AND l.gameid = '%s'
                    ORDER BY l.number, b.bonusnumber;
                    """ % (session_id, game_id)
        with connection_pool.get_conn() as db_connection:
            rows = db_connection.execute_dict_select_cur(sql)
            return rows

    @staticmethod
    def get_sectors_per_level(session_id, game_id, level_number):
        sql = """
                SELECT l.levelname, l.number, s.code, s.sectorname, s.sectororder, s.player
                FROM levels l JOIN sectors s ON
                (
                l.levelid = s.levelid
                AND l.sessionid = s.sessionid
                AND l.gameid = s.gameid
                )
                WHERE
                l.sessionid = %s
                AND l.gameid = '%s'
                AND l.number = %s
                ORDER BY l.number, s.sectororder;
                """ % (session_id, game_id, level_number)
        with connection_pool.get_conn() as db_connection:
            rows = db_connection.execute_dict_select_cur(sql)
            return rows

    @staticmethod
    def get_bonuses_per_level(session_id, game_id, level_number):
        sql = """
                    SELECT l.levelname, l.number, b.code, b.bonusname, b.bonusnumber, b.player
                    FROM levels l JOIN bonuses b ON
                    (
                    l.levelid = b.levelid
                    AND l.sessionid = b.sessionid
                    AND l.gameid = b.gameid
                    )
                    WHERE
                    l.sessionid = %s
                    AND l.gameid = '%s'
                    AND l.number = %s
                    ORDER BY l.number, b.bonusnumber;
                    """ % (session_id, game_id, level_number)
        with connection_pool.get_conn() as db_connection:
            rows = db_connection.execute_dict_select_cur(sql)
            return rows

    @staticmethod
    def get_gameurls_levels():
        sql = """
                        SELECT DISTINCT sc.gameurl, sc.loginurl, sc.sessionid, sc.gameid
                        FROM sessionconfig sc JOIN levels l ON
                        (
                        l.sessionid = sc.sessionid
                        AND l.gameid = sc.gameid
                        )
                        """
        with connection_pool.get_conn() as db_connection:
            rows = db_connection.execute_dict_select_cur(sql)
            return rows

    @staticmethod
    def get_gameurls_bonuses():
        sql = """
                        SELECT DISTINCT sc.gameurl, sc.loginurl, sc.sessionid, sc.gameid
                        FROM sessionconfig sc JOIN bonuses b ON
                        (
                        b.sessionid = sc.sessionid
                        AND b.gameid = sc.gameid
                        )
                        """
        with connection_pool.get_conn() as db_connection:
            rows = db_connection.execute_dict_select_cur(sql)
            return rows

    @staticmethod
    def get_gameurls_sectors():
        sql = """
                        SELECT DISTINCT sc.gameurl, sc.loginurl, sc.sessionid, sc.gameid
                        FROM sessionconfig sc JOIN sectors s ON
                        (
                        s.sessionid = sc.sessionid
                        AND s.gameid = sc.gameid
                        )
                        """
        with connection_pool.get_conn() as db_connection:
            rows = db_connection.execute_dict_select_cur(sql)
            return rows

    @staticmethod
    def get_gameurls_helps():
        sql = """
                        SELECT DISTINCT sc.gameurl, sc.loginurl, sc.sessionid, sc.gameid
                        FROM sessionconfig sc JOIN helps h ON
                        (
                        h.sessionid = sc.sessionid
                        AND h.gameid = sc.gameid
                        )
                        """
        with connection_pool.get_conn() as db_connection:
            rows = db_connection.execute_dict_select_cur(sql)
            return rows

    @staticmethod
    def get_gameurls_messages():
        sql = """
                        SELECT DISTINCT sc.gameurl, sc.loginurl, sc.sessionid, sc.gameid
                        FROM sessionconfig sc JOIN messages m ON
                        (
                        m.sessionid = sc.sessionid
                        AND m.gameid = sc.gameid
                        )
                        """
        with connection_pool.get_conn() as db_connection:
            rows = db_connection.execute_dict_select_cur(sql)
            return rows

    @staticmethod
    def get_gameids_for_builder_list():
        sql = "SELECT DISTINCT * FROM gamesforbuilder"
        with connection_pool.get_conn() as db_connection:
            rows = db_connection.execute_select_cur(sql)
            return [row[0] for row in rows]

    @staticmethod
    def insert_gameids_for_builder(gameid):
        sql = """
                INSERT INTO gamesforbuilder (gameid)
                VALUES ('%s')""" % gameid
        with connection_pool.get_conn() as db_connection:
            return db_connection.execute_insert_cur(sql)

    @staticmethod
    def insert_game_transfer_row(gameid, header, data):
        sql = """INSERT INTO gametransferids (gameid, %s)
                VALUES (%s, '%s')""" % (header, gameid, data)
        with connection_pool.get_conn() as db_connection:
            db_connection.execute_insert_cur(sql)

    @staticmethod
    def get_game_transfer_ids(gameid, header):
        sql = "SELECT %s FROM gametransferids WHERE gameid = %s" % (header, gameid)
        with connection_pool.get_conn() as db_connection:
            rows = db_connection.execute_select_cur(sql)
            return [row[0] for row in rows] if rows else list()

    @staticmethod
    def clean_game_transfer_ids(gameid):
        sql = "DELETE FROM gametransferids WHERE gameid = %s" % gameid
        with connection_pool.get_conn() as db_connection:
            return db_connection.execute_insert_cur(sql)
