# -*- coding: utf-8 -*-
import time
from contextlib import contextmanager


_connection_pool = []
_busy_connections = []
max_conns = 10


def init_pool():
    for _ in xrange(max_conns):
        _connection_pool.append(create_connection())


@contextmanager
def get_conn():
    tries = 10
    while tries:
        try:
            conn = _connection_pool.pop()
            break
        except IndexError:
            time.sleep(1)
        tries -= 1
    else:
        raise Exception("Всё пропало, шеф")

    yield conn
    _connection_pool.append(conn)


#use with the following
with get_conn() as db_connection:
    db_connection.select_dict()  # или как там


# Добавить проверку на падение и переподъем