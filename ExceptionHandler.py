# -*- coding: utf-8 -*-
import logging


class ExceptionHandler(object):
    @staticmethod
    def run_task_exception(function):
        def wrapped(task, bot):
            result = None
            try:
                result = function(task, bot)
            except Exception:
                bot.send_message(task.chat_id, 'Exception в main - не удалось обработать команду %s' % task.type)
                logging.exception("Exception в main - не удалось обработать команду %s" % task.type)
            return result
        return wrapped

    @staticmethod
    def reload_backup_exception(function):
        def wrapped(bot, main_vars):
            try:
                function(bot, main_vars)
            except Exception:
                logging.exception("Exception в main - не удалось сделать reload backup")
        return wrapped

    @staticmethod
    def convert_text_exception(function):
        def wrapped(text, **kwargs):
            r1 = text
            r2 = kwargs['r2']
            r3 = kwargs['r3']
            try:
                r1, r2, r3 = function(text, **kwargs)
            except Exception:
                kwargs['bot'].send_message(kwargs['chat_id'], kwargs['message'], parse_mode='HTML')
                kwargs['bot'].send_message(45839899, kwargs['message'] + '\r\n\r\nRAW TEXT\r\n' + kwargs['raw_text'],
                                           disable_web_page_preview=True)
                logging.exception(kwargs['message'])
            return r1, r2, r3

        return wrapped

    @staticmethod
    def send_text_exception(function):
        def wrapped(text, **kwargs):
            result = False
            try:
                result = function(text, **kwargs)
            except Exception:
                if kwargs['send_to_chat']:
                    kwargs['bot'].send_message(kwargs['chat_id'], kwargs['message'], parse_mode='HTML')
                    try:
                        kwargs['bot'].send_message(45839899, kwargs['message'] + '\r\n\r\nRAW TEXT\r\n' + kwargs['raw_text'],
                                                   disable_web_page_preview=True)
                    except Exception:
                        kwargs['bot'].send_message(45839899, kwargs['header'] + '\r\nНе получилось отправить raw text',
                                                   parse_mode='HTML')
                        logging.exception(kwargs['message'])
                logging.exception(kwargs['message'])
            return result

        return wrapped

    @staticmethod
    def send_text_objects_exception(function):
        def wrapped(bot, chat_id, **kwargs):
            try:
                function(bot, chat_id, **kwargs)
            except Exception:
                bot.send_message(chat_id, kwargs['message'])
                logging.exception(kwargs['message'])
        return wrapped

    @staticmethod
    def db_exception(function):
        def wrapped(sql):
            result = False
            try:
                result = function(sql)
            except Exception:
                # except psycopg2.DatabaseError as err:
                cur.close()
                self.db_conn.rollback()
                logging.exception(kwargs['message'])
            return result
        return wrapped
