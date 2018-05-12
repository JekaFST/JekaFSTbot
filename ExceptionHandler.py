# -*- coding: utf-8 -*-
import logging
from DBMethods import DBSession
from MainClasses import Task


class ExceptionHandler(object):
    @staticmethod
    def run_task_exception(function):
        def wrapped(task, bot):
            try:
                function(task, bot)
            except Exception:
                bot.send_message(task.chat_id, 'Exception в main - не удалось обработать команду %s' % task.type)
                logging.exception("Exception в main - не удалось обработать команду %s" % task.type)
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
    def common_updater_exception(function):
        def wrapped(bot, chat_id, session, **kwargs):
            try:
                function(bot, chat_id, session, **kwargs)
            except Exception:
                bot.send_message(chat_id, kwargs['message'])
                logging.exception(kwargs['message'])
        return wrapped

    @staticmethod
    def updater_exception(function):
        def wrapped(bot, chat_id, session):
            try:
                function(bot, chat_id, session)
            except Exception:
                # bot.send_message(chat_id, 'Exception в функции слежения')
                logging.exception('Exception в updater')
                DBSession.update_bool_flag(session['sessionid'], 'putupdatertask', 'True')
        return wrapped

    @staticmethod
    def get_levels_updater_exception(function):
        def wrapped(bot, chat_id, session):
            r1 = None
            r2 = None
            for i in xrange(2):
                try:
                    r1, r2 = function(bot, chat_id, session)
                    break
                except Exception:
                    if i == 0:
                        continue
                    bot.send_message(chat_id, 'Exception - updater не смог загрузить уровень(-вни)')
                    logging.exception('Exception - updater не смог загрузить уровень(-вни)')
            return r1, r2
        return wrapped

    @staticmethod
    def up_message_exception(function):
        def wrapped(bot, chat_id, **kwargs):
            try:
                function(bot, chat_id, **kwargs)
            except Exception:
                bot.send_message(chat_id, kwargs['message'])
                logging.exception(kwargs['message'])
        return wrapped

    @staticmethod
    def updater_scheduler_exception(function):
        def wrapped(chat_id, bot, main_vars, session_id):
            try:
                function(chat_id, bot, main_vars, session_id)
            except Exception:
                logging.exception('Exception - упал updater_scheduler')
                del main_vars.updater_schedulers_dict[chat_id]
                start_updater_task = Task(chat_id, 'start_updater', main_vars=main_vars, session_id=chat_id)
                main_vars.task_queue.append(start_updater_task)
                # bot.send_message(chat_id, 'Критическая ошибка при слежении. Перезапустите /start_updater')
        return wrapped
