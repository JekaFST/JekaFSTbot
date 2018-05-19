# -*- coding: utf-8 -*-
import os
import json
import logging
import psycopg2.extras
from Const import prod


class DBConnection(object):
    def __init__(self):
        self.db_conn = None

    def connect(self):
        self.db_conn = psycopg2.connect(os.environ['DATABASE_URL'], sslmode='require') if prod \
            else psycopg2.connect("dbname='JekaFSTbot_base' user='postgres' host='localhost' password='hjccbz_1412' port='5432'")

    def execute_select_cur(self, sql):
        if self.db_conn.closed != 0:
            self.connect()
        cur = self.db_conn.cursor()
        try:
            cur.execute(sql)
            result = cur.fetchall()
            cur.close()
            return result
        except psycopg2.DatabaseError:
            cur.close()
            self.db_conn.rollback()
            logging.exception(sql)
            return False

    def execute_dict_select_cur(self, sql):
        if self.db_conn.closed != 0:
            self.connect()
        cur = self.db_conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        try:
            cur.execute(sql)
            result = cur.fetchall()
            cur.close()
            return result
        except psycopg2.DatabaseError:
            cur.close()
            self.db_conn.rollback()
            logging.exception(sql)
            return False

    def execute_insert_cur(self, sql):
        if self.db_conn.closed != 0:
            self.connect()
        cur = self.db_conn.cursor()
        try:
            cur.execute(sql)
            db_connection.db_conn.commit()
            cur.close()
            return True
        except psycopg2.DatabaseError:
            cur.close()
            self.db_conn.rollback()
            logging.exception(sql)
            return False


db_connection = DBConnection()
db_connection.connect()


class DBSession(object):
    @staticmethod
    def get_sessions_ids():
        sql = "SELECT sessionid FROM sessionconfig"
        rows = db_connection.execute_select_cur(sql)
        return [row[0] for row in rows] if rows else list()

    @staticmethod
    def insert_session(main_chat_id, login=None, password=None, en_domain=None, channel_name=None):
        use_channel = True if channel_name else False
        login = "'" + login + "'" if login else "''"
        password = "'" + password + "'" if password else "''"
        en_domain = "'" + en_domain + "'" if en_domain else "''"
        channel_name = "'" + channel_name + "'" if channel_name else 'NULL'
        sql = """INSERT INTO SessionConfig
                (SessionId, Active, Login, Password, ENDomain, GameId, ChannelName, Cookie, GameURL, GameURLjs, LoginURL,
                GameModelStatus, UseChannel, StopUpdater, PutUpdaterTask, Delay, SendCodes, StormGame, CurrLevelId,
                sectorstoclose, sectorsmessageid, Locations, llmessageids)
                VALUES (%s, False, %s, %s, %s, '', %s, '', NULL, NULL, NULL, '', %s, True, NULL, 2, True, NULL, NULL,
                '', NULL, '{}', '{}')
              """ % (main_chat_id, login, password, en_domain, channel_name, use_channel)
        return db_connection.execute_insert_cur(sql)

    @staticmethod
    def get_session(session_id):
        sql = "SELECT * FROM SessionConfig WHERE sessionid = %s" % session_id
        rows = db_connection.execute_dict_select_cur(sql)
        return rows[0] if rows else None

    @staticmethod
    def delete_session(session_id):
        sql = "DELETE FROM SessionConfig WHERE sessionid = %s" % session_id
        db_connection.execute_insert_cur(sql)

    @staticmethod
    def get_all_sessions():
        sql = "SELECT * FROM SessionConfig"
        rows = db_connection.execute_dict_select_cur(sql)
        return rows if rows else list()

    @staticmethod
    def update_session_urls(sessionid, urls):
        sql = """UPDATE SessionConfig
                SET gameurl = '%s', gameurljs = '%s', loginurl = '%s'
                WHERE sessionid = %s
              """ % (urls['game_url'], urls['game_url_js'], urls['login_url'], sessionid)
        return db_connection.execute_insert_cur(sql)

    @staticmethod
    def drop_session_vars(session_id):
        sql = """UPDATE SessionConfig
                SET CurrLevelId = NULL, GameURL = NULL, GameURLjs = NULL, LoginURL = NULL, StormGame = NULL,
                SendCodes = True, GameModelStatus = '', PutUpdaterTask = Null, StopUpdater = True, Locations = '{}', llmessageids = '{}'
                WHERE sessionid = %s
              """ % session_id
        db_connection.execute_insert_cur(sql)

    @staticmethod
    def get_locations(session_id):
        sql = "SELECT locations FROM SessionConfig WHERE sessionid = %s" % session_id
        rows = db_connection.execute_select_cur(sql)
        return json.loads(rows[0][0])

    @staticmethod
    def update_json_field(session_id, header, value):
        sql = """UPDATE SessionConfig
                        SET %s = '%s'
                        WHERE sessionid = %s
                      """ % (header, json.dumps(value), session_id)
        return db_connection.execute_insert_cur(sql)

    @staticmethod
    def update_text_field(sessionid, header, value):
        sql = """UPDATE SessionConfig
                        SET %s = '%s'
                        WHERE sessionid = %s
                      """ % (header, value, sessionid)
        return db_connection.execute_insert_cur(sql)

    @staticmethod
    def get_field_value(sessionid, header):
        sql = "SELECT %s FROM SessionConfig WHERE sessionid = %s" % (header, sessionid)
        rows = db_connection.execute_select_cur(sql)
        return rows[0][0]

    @staticmethod
    def update_bool_flag(sessionid, header, value):
        sql = """UPDATE SessionConfig
                SET %s = %s
                WHERE sessionid = %s
                """ % (header, value, sessionid)
        return db_connection.execute_insert_cur(sql)

    @staticmethod
    def update_int_field(sessionid, header, value):
        sql = """UPDATE SessionConfig
                SET %s = %s
                WHERE sessionid = %s
                """ % (header, value, sessionid)
        return db_connection.execute_insert_cur(sql)


class DBLevels(object):
    @staticmethod
    def insert_level(session_id, game_id, level):
        name = level['LevelName'].encode('utf-8') if level['LevelName'] else ''
        sql = """INSERT INTO levels
                    (SessionId, LevelId, GameId, Number, IsPassed, Dismissed, TimeToUpSent, levelname)
                    VALUES (%s, %s, '%s', %s, %s, %s, False, '%s')
                """ % (session_id, level['LevelId'], game_id, level['LevelNumber'], level['IsPassed'], level['Dismissed'], name)
        return db_connection.execute_insert_cur(sql)

    @staticmethod
    def get_dismissed_level_ids(session_id, game_id):
        sql = """SELECT LevelId FROM levels
                    WHERE sessionid = %s AND gameid = '%s' AND dismissed = True
                    """ % (session_id, game_id)
        rows = db_connection.execute_select_cur(sql)
        return [row[0] for row in rows] if rows else list()

    @staticmethod
    def get_passed_level_ids(session_id, game_id):
        sql = """SELECT LevelId FROM levels
                        WHERE sessionid = %s AND gameid = '%s' AND ispassed = True
                        """ % (session_id, game_id)
        rows = db_connection.execute_select_cur(sql)
        return [row[0] for row in rows] if rows else list()

    @staticmethod
    def update_bool_field(session_id, game_id, level_id, header, active):
        sql = """UPDATE Levels
                SET %s = %s
                WHERE sessionid = %s AND gameid = '%s' AND levelid = %s
                """ % (header, active, session_id, game_id, level_id)
        db_connection.execute_insert_cur(sql)

    @staticmethod
    def get_level_ids_per_game(session_id, game_id):
        sql = """SELECT LevelId FROM Levels
                    WHERE sessionid = %s AND gameid = '%s'
                    """ % (session_id, game_id)
        rows = db_connection.execute_select_cur(sql)
        return [row[0] for row in rows] if rows else list()

    @staticmethod
    def get_time_to_up_sent(session_id, level_id):
        sql = "SELECT timetoupsent FROM Levels WHERE sessionid = %s AND levelid = %s" % (session_id, level_id)
        rows = db_connection.execute_select_cur(sql)
        return rows[0][0]

    @staticmethod
    def update_time_to_up_sent(session_id, level_id, active):
        sql = """UPDATE Levels
                SET timetoupsent = %s
                WHERE sessionid = %s AND levelid = %s
                """ % (active, session_id, level_id)
        db_connection.execute_insert_cur(sql)


class DBHelps(object):
    @staticmethod
    def insert_help(session_id, game_id, help_id):
        sql = """INSERT INTO helps
                        (SessionId, HintId, GameId, NotSent, TimeNotSent)
                        VALUES (%s, %s, '%s', True, True)
                    """ % (session_id, help_id, game_id)
        return db_connection.execute_insert_cur(sql)

    @staticmethod
    def get_help_ids_per_game(session_id, game_id):
        sql = """SELECT HintId FROM helps
                        WHERE sessionid = %s AND gameid = '%s'
                        """ % (session_id, game_id)
        rows = db_connection.execute_select_cur(sql)
        return [row[0] for row in rows] if rows else list()

    @staticmethod
    def get_not_sent_help_ids_per_game(session_id, game_id):
        sql = """SELECT HintId FROM helps
                            WHERE sessionid = %s AND gameid = '%s' AND notsent = True
                            """ % (session_id, game_id)
        rows = db_connection.execute_select_cur(sql)
        return [row[0] for row in rows] if rows else list()

    @staticmethod
    def get_time_not_sent_help_ids_per_game(session_id, game_id):
        sql = """SELECT HintId FROM helps
                            WHERE sessionid = %s AND gameid = '%s' AND timenotsent = True
                            """ % (session_id, game_id)
        rows = db_connection.execute_select_cur(sql)
        return [row[0] for row in rows] if rows else list()

    @staticmethod
    def get_field_value(session_id, game_id, help_id, header):
        sql = "SELECT %s FROM Helps WHERE sessionid = %s AND gameid = '%s' AND hintid = %s" % \
              (header, session_id, game_id, help_id)
        rows = db_connection.execute_select_cur(sql)
        return rows[0][0]

    @staticmethod
    def update_bool_flag(session_id, game_id, help_id, header, value):
        sql = """UPDATE Helps
                    SET %s = %s
                    WHERE sessionid = %s AND gameid = '%s' AND hintid = %s
                    """ % (header, value, session_id, game_id, help_id)
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
                        VALUES (%s, %s, '%s', %s, %s, %s, %s, '%s', %s, '%s')
                    """ % (session_id, bonus_id, game_id, info_not_sent, award_not_sent, level_id, code, bonus_name, bonus_number, player)
        return db_connection.execute_insert_cur(sql)

    @staticmethod
    def get_bonus_ids_per_level(session_id, game_id, level_id):
        sql = """SELECT BonusId FROM bonuses
                            WHERE sessionid = %s AND gameid = '%s' AND levelid = %s
                            """ % (session_id, game_id, level_id)
        rows = db_connection.execute_select_cur(sql)
        return [row[0] for row in rows] if rows else list()

    @staticmethod
    def get_award_not_sent_bonus_ids_per_game(session_id, game_id):
        sql = """SELECT DISTINCT BonusId FROM bonuses
                        WHERE sessionid = %s AND gameid = '%s' AND awardnotsent = True
                        """ % (session_id, game_id)
        rows = db_connection.execute_select_cur(sql)
        return [row[0] for row in rows] if rows else list()

    @staticmethod
    def get_award_sent_bonus_ids_per_game(session_id, game_id):
        sql = """SELECT DISTINCT BonusId FROM bonuses
                            WHERE sessionid = %s AND gameid = '%s' AND awardnotsent = False
                            """ % (session_id, game_id)
        rows = db_connection.execute_select_cur(sql)
        return [row[0] for row in rows] if rows else list()

    @staticmethod
    def get_info_not_sent_bonus_ids_per_game(session_id, game_id):
        sql = """SELECT DISTINCT BonusId FROM bonuses
                        WHERE sessionid = %s AND gameid = '%s' AND infonotsent = True
                        """ % (session_id, game_id)
        rows = db_connection.execute_select_cur(sql)
        return [row[0] for row in rows] if rows else list()

    @staticmethod
    def get_info_sent_bonus_ids_per_game(session_id, game_id):
        sql = """SELECT DISTINCT BonusId FROM bonuses
                            WHERE sessionid = %s AND gameid = '%s' AND infonotsent = False
                            """ % (session_id, game_id)
        rows = db_connection.execute_select_cur(sql)
        return [row[0] for row in rows] if rows else list()

    @staticmethod
    def get_field_value(session_id, game_id, bonus_id, header):
        sql = "SELECT %s FROM Bonuses WHERE sessionid = %s AND gameid = '%s' AND bonusid = %s" % \
              (header, session_id, game_id, bonus_id)
        rows = db_connection.execute_select_cur(sql)
        return rows[0][0]

    @staticmethod
    def update_bool_flag(session_id, game_id, bonus_id, header, value):
        sql = """UPDATE Bonuses
                SET %s = %s
                WHERE sessionid = %s AND gameid = '%s' AND bonusid = %s
                """ % (header, value, session_id, game_id, bonus_id)
        db_connection.execute_insert_cur(sql)

    @staticmethod
    def update_answer_info_not_sent(session_id, game_id, bonus, header, value):
        player = bonus['Answer']['Login'].encode('utf-8')
        code = bonus['Answer']['Answer'].encode('utf-8')
        bonus_id = bonus['BonusId']
        sql = """UPDATE Bonuses
                        SET %s = %s, code = '%s', player = '%s'
                        WHERE sessionid = %s AND gameid = '%s' AND bonusid = %s
                        """ % (header, value, code, player, session_id, game_id, bonus_id)
        db_connection.execute_insert_cur(sql)


class DBSectors(object):
    @staticmethod
    def insert_sector(session_id, game_id, sector, level_id, code='NULL', player=''):
        sector_id = sector['SectorId']
        sector_name = sector['Name'].encode('utf-8')
        sector_order = sector['Order']
        sql = """INSERT INTO sectors
                    (SessionId, SectorId, GameId, AnswerInfoNotSent, code, levelid, sectorname, sectororder, player)
                    VALUES (%s, %s, '%s', True, %s, %s, '%s', %s, '%s')
                """ % (session_id, sector_id, game_id, code, level_id, sector_name, sector_order, player)
        return db_connection.execute_insert_cur(sql)

    @staticmethod
    def get_sector_ids_per_game(session_id, game_id):
        sql = """SELECT SectorId FROM sectors
                    WHERE sessionid = %s AND gameid = '%s'
                    """ % (session_id, game_id)
        rows = db_connection.execute_select_cur(sql)
        return [row[0] for row in rows] if rows else list()

    @staticmethod
    def get_answer_info_not_sent_sector_ids_per_game(session_id, game_id):
        sql = """SELECT SectorId FROM sectors
                    WHERE sessionid = %s AND gameid = '%s' AND answerinfonotsent = True
                    """ % (session_id, game_id)
        rows = db_connection.execute_select_cur(sql)
        return [row[0] for row in rows] if rows else list()

    @staticmethod
    def get_answer_info_not_sent(session_id, game_id, sector_id):
        sql = "SELECT answerinfonotsent FROM Sectors WHERE sessionid = %s AND gameid = '%s' AND sectorid = %s" % \
              (session_id, game_id, sector_id)
        rows = db_connection.execute_select_cur(sql)
        return rows[0][0]

    @staticmethod
    def update_answer_info_not_sent(session_id, game_id, sector_id, active, code, player):
        sql = """UPDATE Sectors
                    SET answerinfonotsent = %s, code = '%s', player = '%s'
                    WHERE sessionid = %s AND gameid = '%s' AND sectorid = %s
                    """ % (active, code, player, session_id, game_id, sector_id)
        db_connection.execute_insert_cur(sql)

    @staticmethod
    def update_level_last_code(session_id, game_id, sector_id, code, player):
        sql = """UPDATE Sectors
                        SET code = '%s', player = '%s'
                        WHERE sessionid = %s AND gameid = '%s' AND sectorid = %s
                        """ % (code, player, session_id, game_id, sector_id)
        db_connection.execute_insert_cur(sql)


class DBMessages(object):
    @staticmethod
    def insert_message(session_id, game_id, message_id):
        sql = """INSERT INTO messages
                    (SessionId, MessageId, GameId, MessageNotSent)
                    VALUES (%s, %s, '%s', True)
                """ % (session_id, message_id, game_id)
        return db_connection.execute_insert_cur(sql)

    @staticmethod
    def get_message_ids_per_game(session_id, game_id):
        sql = """SELECT MessageId FROM messages
                    WHERE sessionid = %s AND gameid = '%s'
                    """ % (session_id, game_id)
        rows = db_connection.execute_select_cur(sql)
        return [row[0] for row in rows] if rows else list()

    @staticmethod
    def get_not_sent_message_ids_per_game(session_id, game_id):
        sql = """SELECT MessageId FROM messages
                        WHERE sessionid = %s AND gameid = '%s' AND messagenotsent = True
                        """ % (session_id, game_id)
        rows = db_connection.execute_select_cur(sql)
        return [row[0] for row in rows] if rows else list()

    @staticmethod
    def get_message_not_sent(session_id, game_id, message_id):
        sql = "SELECT messagenotsent FROM Messages WHERE sessionid = %s AND gameid = '%s' AND messageid = %s" % \
              (session_id, game_id, message_id)
        rows = db_connection.execute_select_cur(sql)
        return rows[0][0]

    @staticmethod
    def update_message_not_sent(session_id, game_id, message_id, active):
        sql = """UPDATE Messages
                SET messagenotsent = %s
                WHERE sessionid = %s AND gameid = '%s' AND messageid = %s
                """ % (active, session_id, game_id, message_id)
        db_connection.execute_insert_cur(sql)


class DB(object):
    @staticmethod
    def get_tags_list():
        sql = "SELECT DISTINCT * FROM TagsToCut"
        rows = db_connection.execute_select_cur(sql)
        return [row[0] for row in rows]

    @staticmethod
    def insert_tag_in_tags_list(tag_to_add):
        sql = """
                INSERT INTO TagsToCut (Tag)
                VALUES ('%s')""" % tag_to_add
        return db_connection.execute_insert_cur(sql)

    @staticmethod
    def get_main_bot_token():
        sql = "SELECT BotToken FROM BotTokens WHERE type = 'main'"
        rows = db_connection.execute_select_cur(sql)
        return rows[0][0]

    @staticmethod
    def get_location_bot_token_by_number(number):
        sql = "SELECT BotToken FROM BotTokens WHERE type = 'location' and number = '%s'" % number
        rows = db_connection.execute_select_cur(sql)
        return rows[0][0]

    @staticmethod
    def get_config_by_chat_id(chat_id):
        sql = "SELECT Login, Password, ENdomain, ChannelName FROM ChatConfigs WHERE ChatId = %s" % (chat_id)
        rows = db_connection.execute_dict_select_cur(sql)
        return rows[0] if rows else None

    @staticmethod
    def get_allowed_chat_ids():
        sql_main = "SELECT ChatId FROM AllowedChats"
        sql_add = "SELECT AddChatId FROM AllowedChats WHERE AddChatId IS NOT NULL"
        main_rows = db_connection.execute_select_cur(sql_main)
        add_rows = db_connection.execute_select_cur(sql_add)
        return [row[0] for row in main_rows] if main_rows else list(), [row[0] for row in add_rows] if add_rows else list()

    @staticmethod
    def insert_main_chat_id(main_chat_id):
        sql = "INSERT INTO AllowedChats (ChatId, AddChatId, AllowedGameIds) VALUES (%s, %s, '')" % (str(main_chat_id), 'NULL')
        return db_connection.execute_insert_cur(sql)

    @staticmethod
    def insert_add_chat_id(main_chat_id, add_chat_id):
        sql = "INSERT INTO AllowedChats (ChatId, AddChatId, AllowedGameIds) VALUES (%s, %s, '')" % (str(main_chat_id), str(add_chat_id))
        return db_connection.execute_insert_cur(sql)

    @staticmethod
    def delete_add_chat_id(add_chat_id):
        sql = "DELETE FROM AllowedChats WHERE AddChatId = %s" % str(add_chat_id)
        db_connection.execute_insert_cur(sql)

    @staticmethod
    def delete_add_chat_ids(session_id):
        sql = "DELETE FROM AllowedChats WHERE chatid = %s AND AddChatId IS NOT NULL" % str(session_id)
        db_connection.execute_insert_cur(sql)

    @staticmethod
    def get_main_chat_id_via_add(add_chat_id):
        sql = "SELECT ChatId FROM AllowedChats WHERE AddChatId = %s" % str(add_chat_id)
        rows = db_connection.execute_select_cur(sql)
        return rows[0][0] if rows else None

    @staticmethod
    def get_add_chat_ids_for_main(main_chat_id):
        sql = "SELECT AddChatId FROM AllowedChats WHERE ChatId = %s AND AddChatId IS NOT NULL" % str(main_chat_id)
        rows = db_connection.execute_select_cur(sql)
        return [row[0] for row in rows] if rows else list()

    @staticmethod
    def get_allowed_game_ids(main_chat_id):
        sql = "SELECT AllowedGameIds FROM AllowedChats WHERE ChatId = %s AND AddChatId IS NULL" % str(main_chat_id)
        rows = db_connection.execute_select_cur(sql)
        return rows[0][0] if rows else list()

    @staticmethod
    def update_allowed_game_ids(main_chat_id, allowed_game_ids):
        sql = "UPDATE AllowedChats SET AllowedGameIds = '%s' WHERE ChatId = %s AND AddChatId IS NULL" \
              % (allowed_game_ids, str(main_chat_id))
        return db_connection.execute_insert_cur(sql)

    @staticmethod
    def cleanup_for_ended_game(session_id, game_id):
        sql = """
                DELETE FROM levels WHERE sessionid = %s AND gameid = '%s';
                DELETE FROM sectors WHERE sessionid = %s AND gameid = '%s';
                DELETE FROM bonuses WHERE sessionid = %s AND gameid = '%s';
                DELETE FROM helps WHERE sessionid = %s AND gameid = '%s';
                DELETE FROM messages WHERE sessionid = %s AND gameid = '%s';
                """ % (session_id, game_id, session_id, game_id, session_id, game_id, session_id, game_id, session_id, game_id)
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
        rows = db_connection.execute_dict_select_cur(sql)
        return rows
