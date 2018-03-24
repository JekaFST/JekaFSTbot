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
        sql = "SELECT Login, Password, ENdomain, ChannelName FROM ChatConfigs WHERE ChatId = %s" % chat_id
        cur = db_conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        cur.execute(sql)
        rows = cur.fetchall()
        return rows[0]
