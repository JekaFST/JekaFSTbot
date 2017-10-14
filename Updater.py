# -*- coding: utf-8 -*-
import time
from UpdaterMethods import *


class Updater(object):
    def __init__(self):
        self.stop_updater = None
        self.help_statuses = dict()
        self.bonus_statuses = dict()
        self.sector_statuses = dict()
        self.time_to_up_sent = None
        self.sectors_to_close = None
        self.sectors_message_id = None
        self.game_model_status = None
        self.delay = 1

    def updater(self, session, bot, chat_id):
        bot.send_message(chat_id, 'Слежение запущено')

        while not self.stop_updater:
            time.sleep(self.delay)
            loaded_level = session.get_current_level(bot, chat_id, from_updater=True)

            if not loaded_level:
                continue

            loaded_helps = loaded_level['Helps']
            loaded_bonuses = loaded_level['Bonuses']
            loaded_sectors = loaded_level['Sectors']

            if not session.current_level:
                session.current_level = loaded_level
                self.help_statuses, self.bonus_statuses, self.time_to_up_sent, self.sector_statuses = reset_level_vars()
                self.sectors_to_close = send_up_info(loaded_level, loaded_helps, loaded_bonuses, bot, chat_id,
                                                     session.channel_name, session.use_channel)
                if session.channel_name and session.use_channel:
                    self.sectors_message_id = send_unclosed_sectors_to_channel(loaded_level, self.sectors_to_close, bot,
                                                                               session.channel_name)
                self.help_statuses = fill_help_statuses(loaded_helps, self.help_statuses)
                self.bonus_statuses = fill_bonus_statuses(loaded_bonuses, session.game_answered_bonus_ids,
                                                          self.bonus_statuses)
                self.sector_statuses = fill_sector_statuses(loaded_sectors, self.sector_statuses)
                continue

            if loaded_level['LevelId'] != session.current_level['LevelId']:
                session.current_level = loaded_level
                self.help_statuses, self.bonus_statuses, self.time_to_up_sent, self.sector_statuses = reset_level_vars()
                self.sectors_to_close = send_up_info(loaded_level, loaded_helps, loaded_bonuses, bot, chat_id,
                                                     session.channel_name, session.use_channel)
                if session.channel_name and session.use_channel:
                    self.sectors_message_id = send_unclosed_sectors_to_channel(loaded_level, self.sectors_to_close, bot,
                                                                               session.channel_name)
                self.help_statuses = fill_help_statuses(loaded_helps, self.help_statuses)
                self.bonus_statuses = fill_bonus_statuses(loaded_bonuses, session.game_answered_bonus_ids,
                                                          self.bonus_statuses)
                self.sector_statuses = fill_sector_statuses(loaded_sectors, self.sector_statuses)
                continue

            session.current_level = loaded_level

            if not loaded_level['Timeout'] == 0 and not self.time_to_up_sent\
                    and loaded_level['TimeoutSecondsRemain'] <= 300:
                message = 'До автоперехода < 5 мин'
                bot.send_message(chat_id, message)
                self.time_to_up_sent = True

            if loaded_sectors:
                codes_to_find = loaded_level['SectorsLeftToClose']
                sectors_parcer(loaded_sectors, codes_to_find, self.sector_statuses, bot, chat_id)

            if loaded_helps:
                help_parcer(loaded_helps, self.help_statuses, bot, chat_id, session.channel_name, session.use_channel)

            if loaded_bonuses:
                bonus_parcer(loaded_bonuses, self.bonus_statuses, session.game_answered_bonus_ids, bot, chat_id)

            if session.channel_name and session.use_channel and self.sectors_to_close and self.sectors_to_close != '1'\
                    and self.sectors_message_id:
                self.sectors_to_close = channel_sectors_editor(loaded_level, self.sectors_to_close,
                                                               bot, session.channel_name, self.sectors_message_id)
        else:
            bot.send_message(chat_id, 'Слежение остановлено')
            return
