# -*- coding: utf-8 -*-
import logging


class ExceptionHandler(object):
    @staticmethod
    def run_task_exception(function):
        def wrapped(*args, **kwargs):
            result = None
            try:
                result = function(*args, **kwargs)
            except Exception:
                args[1].send_message(args[0].chat_id, 'Exception в main - не удалось обработать команду %s' % args[0].type)
                logging.exception("Exception в main - не удалось обработать команду %s" % args[0].type)
            return result
        return wrapped
