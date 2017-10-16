# -*- coding: utf-8 -*-
from SessionMethods import get_current_level
from UpdaterMethods import *


def updater(chat_id, bot, session):
    loaded_level = get_current_level(session, bot, chat_id, from_updater=True)

    if not loaded_level:
        return

    loaded_helps = loaded_level['Helps']
    loaded_bonuses = loaded_level['Bonuses']
    loaded_sectors = loaded_level['Sectors']

    if not session.current_level:
        session.current_level = loaded_level
        session.help_statuses, session.bonus_statuses, session.time_to_up_sent, session.sector_statuses = reset_level_vars()
        session.sectors_to_close = send_up_info(loaded_level, loaded_helps, loaded_bonuses, bot, chat_id,
                                                session.channel_name, session.use_channel)
        if session.channel_name and session.use_channel:
            session.sectors_message_id = send_unclosed_sectors_to_channel(loaded_level, session.sectors_to_close, bot,
                                                                          session.channel_name)
        session.help_statuses = fill_help_statuses(loaded_helps, session.help_statuses)
        session.bonus_statuses = fill_bonus_statuses(loaded_bonuses, session.game_answered_bonus_ids,
                                                     session.bonus_statuses)
        session.sector_statuses = fill_sector_statuses(loaded_sectors, session.sector_statuses)
        return

    if loaded_level['LevelId'] != session.current_level['LevelId']:
        session.current_level = loaded_level
        session.help_statuses, session.bonus_statuses, session.time_to_up_sent, session.sector_statuses = reset_level_vars()
        session.sectors_to_close = send_up_info(loaded_level, loaded_helps, loaded_bonuses, bot, chat_id,
                                                session.channel_name, session.use_channel)
        if session.channel_name and session.use_channel:
            session.sectors_message_id = send_unclosed_sectors_to_channel(loaded_level, session.sectors_to_close, bot,
                                                                          session.channel_name)
        session.help_statuses = fill_help_statuses(loaded_helps, session.help_statuses)
        session.bonus_statuses = fill_bonus_statuses(loaded_bonuses, session.game_answered_bonus_ids,
                                                     session.bonus_statuses)
        session.sector_statuses = fill_sector_statuses(loaded_sectors, session.sector_statuses)
        return

    session.current_level = loaded_level

    if not loaded_level['Timeout'] == 0 and not session.time_to_up_sent\
            and loaded_level['TimeoutSecondsRemain'] <= 300:
        message = 'До автоперехода < 5 мин'
        bot.send_message(chat_id, message)
        session.time_to_up_sent = True

    if loaded_sectors:
        codes_to_find = loaded_level['SectorsLeftToClose']
        sectors_parcer(loaded_sectors, codes_to_find, session.sector_statuses, bot, chat_id)

    if loaded_helps:
        help_parcer(loaded_helps, session.help_statuses, bot, chat_id, session.channel_name, session.use_channel)

    if loaded_bonuses:
        bonus_parcer(loaded_bonuses, session.bonus_statuses, session.game_answered_bonus_ids, bot, chat_id)

    if session.channel_name and session.use_channel and session.sectors_to_close and session.sectors_to_close != '1'\
            and session.sectors_message_id:
        session.sectors_to_close = channel_sectors_editor(loaded_level, session.sectors_to_close,
                                                          bot, session.channel_name, session.sectors_message_id)
