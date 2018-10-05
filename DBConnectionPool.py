# -*- coding: utf-8 -*-
import os
import time
import logging
import psycopg2.extras
from contextlib import contextmanager
import telebot
from Const import prod, num_worker_threads


class DBConnection(object):
    def __init__(self):
        self.db_conn = None

    def open_db_conn(self):
        self.db_conn = psycopg2.connect(os.environ['DATABASE_URL'], sslmode='require') if prod \
            else psycopg2.connect("dbname='JekaFSTbot_base' user='postgres' host='localhost' password='hjccbz_1412' port='5432'")

    def execute_select_cur(self, sql):
        if self.db_conn.closed != 0:
            self.open_db_conn()
        cur = self.db_conn.cursor()
        try:
            cur.execute(sql)
            result = cur.fetchall()
            cur.close()
            return result
        except psycopg2.DatabaseError:
            cur.close()
            self.db_conn.rollback()
            self.db_conn.close()
            logging.exception(sql)
            return False

    def execute_dict_select_cur(self, sql):
        if self.db_conn.closed != 0:
            self.open_db_conn()
        cur = self.db_conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        try:
            cur.execute(sql)
            result = cur.fetchall()
            cur.close()
            return result
        except psycopg2.DatabaseError:
            cur.close()
            self.db_conn.rollback()
            self.db_conn.close()
            logging.exception(sql)
            return False

    def execute_insert_cur(self, sql):
        if self.db_conn.closed != 0:
            self.open_db_conn()
        cur = self.db_conn.cursor()
        try:
            cur.execute(sql)
            self.db_conn.commit()
            cur.close()
            return True
        except psycopg2.DatabaseError:
            cur.close()
            self.db_conn.rollback()
            self.db_conn.close()
            logging.exception(sql)
            return False


class ConnectionPool(object):
    def __init__(self):
        self.connection_pool = list()
        self.max_conns = 15

    def init_pool(self):
        for _ in xrange(self.max_conns):
            db_connection = DBConnection()
            db_connection.open_db_conn()
            self.connection_pool.append(db_connection)

    @contextmanager
    def get_conn(self):
        tries = num_worker_threads
        while tries:
            try:
                conn = self.connection_pool.pop()
                break
            except IndexError:
                time.sleep(1)
            tries -= 1
        else:
            telebot.TeleBot("583637976:AAEFrQFiAaGuKwmoRV0N1MwU-ujRzmCxCAo").send_message(45839899, 'Нет доступного коннекшена к базе')
            raise Exception('Нет доступного коннекшена к базе')

        yield conn
        self.connection_pool.append(conn)
