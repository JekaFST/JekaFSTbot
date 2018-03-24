import os
import psycopg2.extras

# DATABASE_URL = os.environ['DATABASE_URL']
# db_conn = psycopg2.connect(DATABASE_URL, sslmode='require')
DATABASE_URL = 'jdbc:postgresql://localhost:5432/JekaFSTbot_base'
db_conn = psycopg2.connect("dbname='JekaFSTbot_base' user='postgres' host='localhost' password='hjccbz_1412' port='5432'")


class DB(object):
    @staticmethod
    def get_tags_list():
        sql = "SELECT DISTINCT * FROM TagsToCut"
        cur = db_conn.cursor()
        cur.execute(sql)
        rows = cur.fetchall()
        return [row[0] for row in rows]

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
    def insert_add_chat_id(main_chat_id, add_chat_id):
        sql = "INSERT INTO AllowedChats (ChatId, AddChatId) VALUES (%s, %s)" % (str(main_chat_id), str(add_chat_id))
        cur = db_conn.cursor()
        cur.execute(sql)
        db_conn.commit()

    @staticmethod
    def delete_add_chat_id(main_chat_id, add_chat_id):
        sql = "DELETE FROM AllowedChats WHERE ChatId = %s AND AddChatId = %s" % (str(main_chat_id), str(add_chat_id))
        cur = db_conn.cursor()
        cur.execute(sql)
        db_conn.commit()

    @staticmethod
    def get_main_chat_id_via_add(add_chat_id):
        sql = "SELECT ChatId FROM AllowedChats WHERE AddChatId = %s" % str(add_chat_id)
        cur = db_conn.cursor()
        cur.execute(sql)
        rows = cur.fetchall()
        return rows[0][0]
