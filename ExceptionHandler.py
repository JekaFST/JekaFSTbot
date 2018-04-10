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
    def text_exception_1_result(function):
        def wrapped(text, **kwargs):
            result = text
            try:
                result = function(text, **kwargs)
            except Exception:
                kwargs['bot'].send_message(kwargs['chat_id'], kwargs['message'], parse_mode='HTML')
                kwargs['bot'].send_message(45839899, kwargs['message'] + '\r\n\r\nRAW TEXT\r\n' + kwargs['raw_text'],
                                           disable_web_page_preview=True)
                logging.exception(kwargs['message'])
            return result

        return wrapped

    @staticmethod
    def text_exception_2_results(function):
        def wrapped(text, **kwargs):
            res_1 = text
            res_2 = list()
            try:
                res_1, res_2 = function(text, **kwargs)
            except Exception:
                kwargs['bot'].send_message(kwargs['chat_id'], kwargs['message'], parse_mode='HTML')
                kwargs['bot'].send_message(45839899, kwargs['message'] + '\r\n\r\nRAW TEXT\r\n' + kwargs['raw_text'],
                                           disable_web_page_preview=True)
                logging.exception(kwargs['message'])
            return res_1, res_2

        return wrapped

    @staticmethod
    def text_exception_3_results(function):
        def wrapped(text, *args, **kwargs):
            res_1 = text
            res_2 = list()
            res_3 = list()
            try:
                res_1, res_2, res_3 = function(text, *args, **kwargs)
            except Exception:
                kwargs['bot'].send_message(kwargs['chat_id'], kwargs['message'], parse_mode='HTML')
                kwargs['bot'].send_message(45839899, kwargs['message'] + '\r\n\r\nRAW TEXT\r\n' + kwargs['raw_text'],
                                           disable_web_page_preview=True)
                logging.exception(kwargs['message'])
            return res_1, res_2, res_3

        return wrapped

    @staticmethod
    def send_text_exception(function):
        def wrapped(text, **kwargs):
            result = False
            try:
                result = function(text, **kwargs)
            except Exception:
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
