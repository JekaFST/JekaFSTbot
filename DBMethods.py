import json
import os
import psycopg2.extras

# DATABASE_URL = os.environ['DATABASE_URL']
# db_conn = psycopg2.connect(DATABASE_URL, sslmode='require')
DATABASE_URL = 'jdbc:postgresql://localhost:5432/JekaFSTbot_base'
db_conn = psycopg2.connect("dbname='JekaFSTbot_base' user='postgres' host='localhost' password='hjccbz_1412' port='5432'")


def execute_select_cur(sql):
    try:
        cur = db_conn.cursor()
        cur.execute(sql)
        return cur.fetchall()
    except psycopg2.DatabaseError as err:
        print 'DB error in the following query: "' + sql + '": ' + err.message
        return False


def execute_dict_select_cur(sql):
    try:
        cur = db_conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        cur.execute(sql)
        return cur.fetchall()
    except psycopg2.DatabaseError as err:
        print 'DB error in the following query: "' + sql + '": ' + err.message
        return False


def execute_insert_cur(sql):
    try:
        cur = db_conn.cursor()
        cur.execute(sql)
        db_conn.commit()
        return True
    except psycopg2.DatabaseError as err:
        print 'DB error in the following query: "' + sql + '": ' + err.message
        return False


class DB(object):
    @staticmethod
    def get_sessions_ids():
        sql = "SELECT sessionid FROM sessionconfig"
        rows = execute_select_cur(sql)
        return [row[0] for row in rows] if rows else list()


    @staticmethod
    def get_tags_list():
        sql = "SELECT DISTINCT * FROM TagsToCut"
        cur = db_conn.cursor()
        try:
            cur.execute(sql)
            rows = cur.fetchall()
            return [row[0] for row in rows]
        except psycopg2.DatabaseError as err:
            print err
            return 'error'

    @staticmethod
    def insert_tag_in_tags_list(tag_to_add):
        sql = """
                INSERT INTO TagsToCut (Tag)
                VALUES ('%s')""" % tag_to_add
        cur = db_conn.cursor()
        cur.execute(sql)
        db_conn.commit()

    @staticmethod
    def get_main_bot_token():
        sql = "SELECT BotToken FROM BotTokens WHERE type = 'main'"
        cur = db_conn.cursor()
        cur.execute(sql)
        rows = cur.fetchall()
        return rows[0][0]

    @staticmethod
    def get_location_bot_token_by_number(number):
        sql = "SELECT BotToken FROM BotTokens WHERE type = 'location' and number = '%s'" % str(number)
        cur = db_conn.cursor()
        cur.execute(sql)
        rows = cur.fetchall()
        return rows[0][0]

    @staticmethod
    def get_config_by_chat_id(chat_id):
        sql = "SELECT Login, Password, ENdomain, ChannelName FROM ChatConfigs WHERE ChatId = %s" % (chat_id)
        cur = db_conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        cur.execute(sql)
        rows = cur.fetchall()
        return rows[0] if rows else None

    @staticmethod
    def get_allowed_chat_ids():
        sql_main = "SELECT ChatId FROM AllowedChats"
        sql_add = "SELECT AddChatId FROM AllowedChats WHERE AddChatId IS NOT NULL"
        cur = db_conn.cursor()
        cur.execute(sql_main)
        main_rows = cur.fetchall()
        cur.execute(sql_add)
        add_rows = cur.fetchall()
        return [row[0] for row in main_rows] if main_rows else list(), [row[0] for row in add_rows] if add_rows else list()

    @staticmethod
    def insert_main_chat_id(main_chat_id):
        sql = "INSERT INTO AllowedChats (ChatId, AddChatId) VALUES (%s, %s)" % (str(main_chat_id), 'NULL')
        cur = db_conn.cursor()
        cur.execute(sql)
        db_conn.commit()

    @staticmethod
    def insert_add_chat_id(main_chat_id, add_chat_id):
        sql = "INSERT INTO AllowedChats (ChatId, AddChatId) VALUES (%s, %s)" % (str(main_chat_id), str(add_chat_id))
        cur = db_conn.cursor()
        cur.execute(sql)
        db_conn.commit()

    @staticmethod
    def delete_add_chat_id(add_chat_id):
        sql = "DELETE FROM AllowedChats WHERE AddChatId = %s" % str(add_chat_id)
        cur = db_conn.cursor()
        cur.execute(sql)
        db_conn.commit()

    @staticmethod
    def get_main_chat_id_via_add(add_chat_id):
        sql = "SELECT ChatId FROM AllowedChats WHERE AddChatId = %s" % str(add_chat_id)
        cur = db_conn.cursor()
        cur.execute(sql)
        rows = cur.fetchall()
        return rows[0][0] if rows else None

    @staticmethod
    def get_add_chat_ids_for_main(main_chat_id):
        sql = "SELECT AddChatId FROM AllowedChats WHERE ChatId = %s AND AddChatId IS NOT NULL" % str(main_chat_id)
        cur = db_conn.cursor()
        cur.execute(sql)
        rows = cur.fetchall()
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
                GameModelStatus, UseChannel, StopUpdater, PutUpdaterTask, Delay, SendCodes, StormGame, CurrLevelId, Locations)
                VALUES (%s, False, %s, %s, %s, '', %s, '', NULL, NULL, NULL, '', %s, NULL, NULL, 2, True, NULL, NULL, '{}')
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
    def update_gameid(sessionid, game_id):
        sql = """UPDATE SessionConfig
                    SET gameid = %s
                    WHERE sessionid = %s
                  """ % (game_id, sessionid)
        return execute_insert_cur(sql)

    @staticmethod
    def get_game_id(sessionid):
        sql = "SELECT gameid FROM SessionConfig WHERE sessionid = %s" % sessionid
        rows = execute_select_cur(sql)
        return rows[0][0]

    @staticmethod
    def update_login(sessionid, login):
        sql = """UPDATE SessionConfig
                    SET login = '%s'
                    WHERE sessionid = %s
                  """ % (login, sessionid)
        return execute_insert_cur(sql)

    @staticmethod
    def update_password(sessionid, password):
        sql = """UPDATE SessionConfig
                    SET password = '%s'
                    WHERE sessionid = %s
                  """ % (password, sessionid)
        return execute_insert_cur(sql)

    @staticmethod
    def update_domain(sessionid, domain):
        sql = """UPDATE SessionConfig
                    SET endomain = '%s'
                    WHERE sessionid = %s
                  """ % (domain, sessionid)
        return execute_insert_cur(sql)

    @staticmethod
    def update_cookie(sessionid, cookie):
        sql = """UPDATE SessionConfig
                    SET cookie = '%s'
                    WHERE sessionid = %s
                  """ % (cookie, sessionid)
        return execute_insert_cur(sql)

    @staticmethod
    def get_cookie(sessionid):
        sql = "SELECT cookie FROM SessionConfig WHERE sessionid = %s" % sessionid
        rows = execute_select_cur(sql)
        return rows[0][0]

    @staticmethod
    def update_session_activity(sessionid, active):
        sql = """UPDATE SessionConfig
                SET Active = %s
                WHERE sessionid = %s
                """ % (active, sessionid)
        return execute_insert_cur(sql)

    @staticmethod
    def get_session_activity(sessionid):
        sql = "SELECT active FROM SessionConfig WHERE sessionid = %s" % sessionid
        rows = execute_select_cur(sql)
        return rows[0][0]

    @staticmethod
    def get_en_domain(sessionid):
        sql = "SELECT endomain FROM SessionConfig WHERE sessionid = %s" % sessionid
        rows = execute_select_cur(sql)
        return rows[0][0]

    @staticmethod
    def update_stop_updater(sessionid, active):
        sql = """UPDATE SessionConfig
                SET stopupdater = %s
                WHERE sessionid = %s
                """ % (active, sessionid)
        return execute_insert_cur(sql)

    @staticmethod
    def update_put_updater_task(sessionid, active):
        sql = """UPDATE SessionConfig
                SET putupdatertask = %s
                WHERE sessionid = %s
                """ % (active, sessionid)
        return execute_insert_cur(sql)

    @staticmethod
    def update_use_channel(sessionid, active):
        sql = """UPDATE SessionConfig
                SET usechannel = %s
                WHERE sessionid = %s
                """ % (active, sessionid)
        return execute_insert_cur(sql)

    @staticmethod
    def get_game_model_status(sessionid):
        sql = "SELECT gamemodelstatus FROM SessionConfig WHERE sessionid = %s" % sessionid
        rows = execute_select_cur(sql)
        return rows[0][0]

    @staticmethod
    def update_game_model_status(sessionid, game_model_status):
        sql = """UPDATE SessionConfig
                SET gamemodelstatus = '%s'
                WHERE sessionid = %s
                """ % (game_model_status, sessionid)
        return execute_insert_cur(sql)

    @staticmethod
    def update_storm_game(sessionid, active):
        sql = """UPDATE SessionConfig
                SET StormGame = %s
                WHERE sessionid = %s
                """ % (active, sessionid)
        return execute_insert_cur(sql)

    @staticmethod
    def update_currlevelid(sessionid, currlevelid):
        sql = """UPDATE SessionConfig
                SET currlevelid = %s
                WHERE sessionid = %s
                """ % (currlevelid, sessionid)
        return execute_insert_cur(sql)

    @staticmethod
    def insert_level(sessionid, level):
        game_id = DB.get_game_id(sessionid)
        sql = """INSERT INTO levels
                    (SessionId, LevelId, GameId, Number, IsPassed, Dismissed, TimeToUpSent, SectorsToClose, SectorsMessageId)
                    VALUES (%s, %s, '%s', %s, %s, %s, False, Null, Null)
                """ % (sessionid, level['LevelId'], game_id, level['Number'], level['IsPassed'], level['Dismissed'])
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
    def get_level_ids_per_game(session_id):
        game_id = DB.get_game_id(session_id)
        sql = """SELECT LevelId FROM Levels
                    WHERE sessionid = %s AND gameid = '%s'
                    """ % (session_id, game_id)
        rows = execute_select_cur(sql)
        return [row[0] for row in rows] if rows else list()
