# -*- coding: utf-8 -*-
import os
import json
import psycopg2.extras

DATABASE_URL = os.environ['DATABASE_URL']
db_conn = psycopg2.connect(DATABASE_URL, sslmode='require')
# db_conn = psycopg2.connect("dbname='JekaFSTbot_base' user='postgres' host='localhost' password='hjccbz_1412' port='5432'")


def execute_select_cur(sql):
    cur = db_conn.cursor()
    try:
        cur.execute(sql)
        result = cur.fetchall()
        cur.close()
        return result
    except psycopg2.DatabaseError as err:
        cur.close()
        db_conn.rollback()
        print 'DB error in the following query: "' + sql + '": ' + err.message
        return False


def execute_dict_select_cur(sql):
    cur = db_conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    try:
        cur.execute(sql)
        result = cur.fetchall()
        cur.close()
        return result
    except psycopg2.DatabaseError as err:
        cur.close()
        db_conn.rollback()
        print 'DB error in the following query: "' + sql + '": ' + err.message
        return False


def execute_insert_cur(sql):
    cur = db_conn.cursor()
    try:
        cur.execute(sql)
        db_conn.commit()
        cur.close()
        return True
    except psycopg2.DatabaseError as err:
        cur.close()
        db_conn.rollback()
        print 'DB error in the following query: "' + sql + '": ' + err.message
        return False


class DBSession(object):
    @staticmethod
    def get_sessions_ids():
        sql = "SELECT sessionid FROM sessionconfig"
        rows = execute_select_cur(sql)
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
                GameModelStatus, UseChannel, StopUpdater, PutUpdaterTask, Delay, SendCodes, StormGame, CurrLevelId, Locations, llmessageids)
                VALUES (%s, False, %s, %s, %s, '', %s, '', NULL, NULL, NULL, '', %s, NULL, NULL, 2, True, NULL, NULL, '{}', '{}')
              """ % (main_chat_id, login, password, en_domain, channel_name, use_channel)
        return execute_insert_cur(sql)

    @staticmethod
    def get_session(session_id):
        sql = "SELECT * FROM SessionConfig WHERE sessionid = %s" % session_id
        rows = execute_dict_select_cur(sql)
        return rows[0] if rows else None

    @staticmethod
    def update_session_urls(sessionid, urls):
        sql = """UPDATE SessionConfig
                SET gameurl = '%s', gameurljs = '%s', loginurl = '%s'
                WHERE sessionid = %s
              """ % (urls['game_url'], urls['game_url_js'], urls['login_url'], sessionid)
        return execute_insert_cur(sql)

    @staticmethod
    def drop_session_vars(session_id):
        sql = """UPDATE SessionConfig
                SET CurrLevelId = NULL, GameURL = NULL, GameURLjs = NULL, LoginURL = NULL, StormGame = NULL,
                SendCodes = True, GameModelStatus = '', PutUpdaterTask = Null, StopUpdater = NULL
                WHERE sessionid = %s
              """ % session_id
        execute_insert_cur(sql)

    @staticmethod
    def get_locations(session_id):
        sql = "SELECT locations FROM SessionConfig WHERE sessionid = %s" % session_id
        rows = execute_select_cur(sql)
        return json.loads(rows[0][0])

    @staticmethod
    def update_json_field(session_id, header, value):
        sql = """UPDATE SessionConfig
                        SET %s = '%s'
                        WHERE sessionid = %s
                      """ % (header, json.dumps(value), session_id)
        return execute_insert_cur(sql)

    @staticmethod
    def update_text_field(sessionid, header, value):
        sql = """UPDATE SessionConfig
                        SET %s = '%s'
                        WHERE sessionid = %s
                      """ % (header, value, sessionid)
        return execute_insert_cur(sql)

    @staticmethod
    def get_field_value(sessionid, header):
        sql = "SELECT %s FROM SessionConfig WHERE sessionid = %s" % (header, sessionid)
        rows = execute_select_cur(sql)
        return rows[0][0]

    @staticmethod
    def update_bool_flag(sessionid, header, value):
        sql = """UPDATE SessionConfig
                SET %s = %s
                WHERE sessionid = %s
                """ % (header, value, sessionid)
        return execute_insert_cur(sql)

    @staticmethod
    def update_int_field(sessionid, header, value):
        sql = """UPDATE SessionConfig
                SET %s = %s
                WHERE sessionid = %s
                """ % (header, value, sessionid)
        return execute_insert_cur(sql)


class DBLevels(object):
    @staticmethod
    def insert_level(session_id, game_id, level):
        sql = """INSERT INTO levels
                    (SessionId, LevelId, GameId, Number, IsPassed, Dismissed, TimeToUpSent)
                    VALUES (%s, %s, '%s', %s, %s, %s, False)
                """ % (session_id, level['LevelId'], game_id, level['Number'], level['IsPassed'], level['Dismissed'])
        return execute_insert_cur(sql)

    @staticmethod
    def get_dismissed_level_ids(session_id, game_id):
        sql = """SELECT LevelId FROM levels
                    WHERE sessionid = %s AND gameid = '%s' AND dismissed = True
                    """ % (session_id, game_id)
        rows = execute_select_cur(sql)
        return [row[0] for row in rows] if rows else list()

    @staticmethod
    def get_passed_level_ids(session_id, game_id):
        sql = """SELECT LevelId FROM levels
                        WHERE sessionid = %s AND gameid = '%s' AND ispassed = True
                        """ % (session_id, game_id)
        rows = execute_select_cur(sql)
        return [row[0] for row in rows] if rows else list()

    @staticmethod
    def update_bool_field(session_id, game_id, level_id, header, active):
        sql = """UPDATE Levels
                SET %s = %s
                WHERE sessionid = %s AND gameid = '%s' AND levelid = %s
                """ % (header, active, session_id, game_id, level_id)
        execute_insert_cur(sql)

    @staticmethod
    def get_level_ids_per_game(session_id, game_id):
        sql = """SELECT LevelId FROM Levels
                    WHERE sessionid = %s AND gameid = '%s'
                    """ % (session_id, game_id)
        rows = execute_select_cur(sql)
        return [row[0] for row in rows] if rows else list()

    @staticmethod
    def get_time_to_up_sent(session_id, level_id):
        sql = "SELECT timetoupsent FROM Levels WHERE sessionid = %s AND levelid = %s" % (session_id, level_id)
        rows = execute_select_cur(sql)
        return rows[0][0]

    @staticmethod
    def update_time_to_up_sent(session_id, level_id, active):
        sql = """UPDATE Levels
                SET timetoupsent = %s
                WHERE sessionid = %s AND levelid = %s
                """ % (active, session_id, level_id)
        execute_insert_cur(sql)


class DBHelps(object):
    @staticmethod
    def insert_help(session_id, game_id, help_id):
        sql = """INSERT INTO helps
                        (SessionId, HintId, GameId, NotSent, TimeNotSent)
                        VALUES (%s, %s, '%s', True, True)
                    """ % (session_id, help_id, game_id)
        return execute_insert_cur(sql)

    @staticmethod
    def get_help_ids_per_game(session_id, game_id):
        sql = """SELECT HintId FROM helps
                        WHERE sessionid = %s AND gameid = '%s'
                        """ % (session_id, game_id)
        rows = execute_select_cur(sql)
        return [row[0] for row in rows] if rows else list()

    @staticmethod
    def get_not_sent_help_ids_per_game(session_id, game_id):
        sql = """SELECT HintId FROM helps
                            WHERE sessionid = %s AND gameid = '%s' AND notsent = True
                            """ % (session_id, game_id)
        rows = execute_select_cur(sql)
        return [row[0] for row in rows] if rows else list()

    @staticmethod
    def get_time_not_sent_help_ids_per_game(session_id, game_id):
        sql = """SELECT HintId FROM helps
                            WHERE sessionid = %s AND gameid = '%s' AND timenotsent = True
                            """ % (session_id, game_id)
        rows = execute_select_cur(sql)
        return [row[0] for row in rows] if rows else list()

    @staticmethod
    def get_field_value(session_id, game_id, help_id, header):
        sql = "SELECT %s FROM Helps WHERE sessionid = %s AND gameid = '%s' AND hintid = %s" % \
              (header, session_id, game_id, help_id)
        rows = execute_select_cur(sql)
        return rows[0][0]

    @staticmethod
    def update_bool_flag(session_id, game_id, help_id, header, value):
        sql = """UPDATE Helps
                    SET %s = %s
                    WHERE sessionid = %s AND gameid = '%s' AND hintid = %s
                    """ % (header, value, session_id, game_id, help_id)
        execute_insert_cur(sql)


class DBBonuses(object):
    @staticmethod
    def insert_bonus(session_id, game_id, bonus_id):
        sql = """INSERT INTO bonuses
                        (SessionId, BonusId, GameId, InfoNotSent, AwardNotSent)
                        VALUES (%s, %s, '%s', True, True)
                    """ % (session_id, bonus_id, game_id)
        return execute_insert_cur(sql)

    @staticmethod
    def get_bonus_ids_per_game(session_id, game_id):
        sql = """SELECT BonusId FROM bonuses
                        WHERE sessionid = %s AND gameid = '%s'
                        """ % (session_id, game_id)
        rows = execute_select_cur(sql)
        return [row[0] for row in rows] if rows else list()

    @staticmethod
    def get_award_not_sent_bonus_ids_per_game(session_id, game_id):
        sql = """SELECT BonusId FROM bonuses
                        WHERE sessionid = %s AND gameid = '%s' AND awardnotsent = True
                        """ % (session_id, game_id)
        rows = execute_select_cur(sql)
        return [row[0] for row in rows] if rows else list()

    @staticmethod
    def get_info_not_sent_bonus_ids_per_game(session_id, game_id):
        sql = """SELECT BonusId FROM bonuses
                        WHERE sessionid = %s AND gameid = '%s' AND infonotsent = True
                        """ % (session_id, game_id)
        rows = execute_select_cur(sql)
        return [row[0] for row in rows] if rows else list()

    @staticmethod
    def get_field_value(session_id, game_id, bonus_id, header):
        sql = "SELECT %s FROM Bonuses WHERE sessionid = %s AND gameid = '%s' AND bonusid = %s" % \
              (header, session_id, game_id, bonus_id)
        rows = execute_select_cur(sql)
        return rows[0][0]

    @staticmethod
    def update_bool_flag(session_id, game_id, bonus_id, header, value):
        sql = """UPDATE Bonuses
                SET %s = %s
                WHERE sessionid = %s AND gameid = '%s' AND bonusid = %s
                """ % (header, value, session_id, game_id, bonus_id)
        execute_insert_cur(sql)


class DBSectors(object):
    @staticmethod
    def insert_sector(session_id, game_id, sector_id):
        sql = """INSERT INTO sectors
                    (SessionId, SectorId, GameId, AnswerInfoNotSent)
                    VALUES (%s, %s, '%s', True)
                """ % (session_id, sector_id, game_id)
        return execute_insert_cur(sql)

    @staticmethod
    def get_sector_ids_per_game(session_id, game_id):
        sql = """SELECT SectorId FROM sectors
                    WHERE sessionid = %s AND gameid = '%s'
                    """ % (session_id, game_id)
        rows = execute_select_cur(sql)
        return [row[0] for row in rows] if rows else list()

    @staticmethod
    def get_answer_info_not_sent_sector_ids_per_game(session_id, game_id):
        sql = """SELECT SectorId FROM sectors
                    WHERE sessionid = %s AND gameid = '%s' AND answerinfonotsent = True
                    """ % (session_id, game_id)
        rows = execute_select_cur(sql)
        return [row[0] for row in rows] if rows else list()

    @staticmethod
    def get_answer_info_not_sent(session_id, game_id, sector_id):
        sql = "SELECT answerinfonotsent FROM Sectors WHERE sessionid = %s AND gameid = '%s' AND sectorid = %s" % \
              (session_id, game_id, sector_id)
        rows = execute_select_cur(sql)
        return rows[0][0]

    @staticmethod
    def update_answer_info_not_sent(session_id, game_id, sector_id, active):
        sql = """UPDATE Sectors
                SET answerinfonotsent = %s
                WHERE sessionid = %s AND gameid = '%s' AND sectorid = %s
                """ % (active, session_id, game_id, sector_id)
        execute_insert_cur(sql)


class DBMessages(object):
    @staticmethod
    def insert_message(session_id, game_id, message_id):
        sql = """INSERT INTO messages
                    (SessionId, MessageId, GameId, MessageNotSent)
                    VALUES (%s, %s, '%s', True)
                """ % (session_id, message_id, game_id)
        return execute_insert_cur(sql)

    @staticmethod
    def get_message_ids_per_game(session_id, game_id):
        sql = """SELECT MessageId FROM messages
                    WHERE sessionid = %s AND gameid = '%s'
                    """ % (session_id, game_id)
        rows = execute_select_cur(sql)
        return [row[0] for row in rows] if rows else list()

    @staticmethod
    def get_not_sent_message_ids_per_game(session_id, game_id):
        sql = """SELECT MessageId FROM messages
                        WHERE sessionid = %s AND gameid = '%s' AND messagenotsent = True
                        """ % (session_id, game_id)
        rows = execute_select_cur(sql)
        return [row[0] for row in rows] if rows else list()

    @staticmethod
    def get_message_not_sent(session_id, game_id, message_id):
        sql = "SELECT messagenotsent FROM Messages WHERE sessionid = %s AND gameid = '%s' AND messageid = %s" % \
              (session_id, game_id, message_id)
        rows = execute_select_cur(sql)
        return rows[0][0]

    @staticmethod
    def update_message_not_sent(session_id, game_id, message_id, active):
        sql = """UPDATE Messages
                SET messagenotsent = %s
                WHERE sessionid = %s AND gameid = '%s' AND messageid = %s
                """ % (active, session_id, game_id, message_id)
        execute_insert_cur(sql)


class DB(object):
    @staticmethod
    def get_tags_list():
        sql = "SELECT DISTINCT * FROM TagsToCut"
        rows = execute_select_cur(sql)
        return [row[0] for row in rows]

    @staticmethod
    def insert_tag_in_tags_list(tag_to_add):
        sql = """
                INSERT INTO TagsToCut (Tag)
                VALUES ('%s')""" % tag_to_add
        return execute_insert_cur(sql)

    @staticmethod
    def get_main_bot_token():
        sql = "SELECT BotToken FROM BotTokens WHERE type = 'main'"
        rows = execute_select_cur(sql)
        return rows[0][0]

    @staticmethod
    def get_location_bot_token_by_number(number):
        sql = "SELECT BotToken FROM BotTokens WHERE type = 'location' and number = '%s'" % number
        rows = execute_select_cur(sql)
        return rows[0][0]

    @staticmethod
    def get_config_by_chat_id(chat_id):
        sql = "SELECT Login, Password, ENdomain, ChannelName FROM ChatConfigs WHERE ChatId = %s" % (chat_id)
        rows = execute_dict_select_cur(sql)
        return rows[0] if rows else None

    @staticmethod
    def get_allowed_chat_ids():
        sql_main = "SELECT ChatId FROM AllowedChats"
        sql_add = "SELECT AddChatId FROM AllowedChats WHERE AddChatId IS NOT NULL"
        main_rows = execute_select_cur(sql_main)
        add_rows = execute_select_cur(sql_add)
        return [row[0] for row in main_rows] if main_rows else list(), [row[0] for row in add_rows] if add_rows else list()

    @staticmethod
    def insert_main_chat_id(main_chat_id):
        sql = "INSERT INTO AllowedChats (ChatId, AddChatId) VALUES (%s, %s)" % (str(main_chat_id), 'NULL')
        execute_insert_cur(sql)

    @staticmethod
    def insert_add_chat_id(main_chat_id, add_chat_id):
        sql = "INSERT INTO AllowedChats (ChatId, AddChatId) VALUES (%s, %s)" % (str(main_chat_id), str(add_chat_id))
        execute_insert_cur(sql)

    @staticmethod
    def delete_add_chat_id(add_chat_id):
        sql = "DELETE FROM AllowedChats WHERE AddChatId = %s" % str(add_chat_id)
        execute_insert_cur(sql)

    @staticmethod
    def get_main_chat_id_via_add(add_chat_id):
        sql = "SELECT ChatId FROM AllowedChats WHERE AddChatId = %s" % str(add_chat_id)
        rows = execute_select_cur(sql)
        return rows[0][0] if rows else None

    @staticmethod
    def get_add_chat_ids_for_main(main_chat_id):
        sql = "SELECT AddChatId FROM AllowedChats WHERE ChatId = %s AND AddChatId IS NOT NULL" % str(main_chat_id)
        rows = execute_select_cur(sql)
        return [row[0] for row in rows] if rows else list()
