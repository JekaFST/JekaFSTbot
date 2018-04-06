# -*- coding: utf-8 -*-
import threading
import json
from DBMethods import DBSession, DBLevels, DBHelps, DBBonuses, DBSectors, DBMessages
from SessionMethods import get_current_level, get_storm_level, get_storm_levels, get_current_game_model
from CommonMethods import send_help, send_time_to_help, send_task, time_converter, send_bonus_info,\
    send_bonus_award_answer, send_adm_message, close_live_locations


def updater(task, bot):
    session = DBSession.get_session(task.session_id)
    if not session['stormgame']:
        name = 'upd_thread_%s' % task.chat_id
        task.updaters_dict[task.chat_id] = threading.Thread(name=name, target=linear_updater,
                                                            args=(task.chat_id, bot, session))
        task.updaters_dict[task.chat_id].start()
        return
    else:
        name = 'upd_thread_%s' % task.chat_id
        task.updaters_dict[task.chat_id] = threading.Thread(name=name, target=storm_updater,
                                                            args=(task.chat_id, bot, session))
        task.updaters_dict[task.chat_id].start()
        return


def linear_updater(chat_id, bot, session):
    for i in xrange(2):
        try:
            loaded_level, levels = get_current_level(session, bot, chat_id, from_updater=True)
            break
        except Exception:
            if i == 0:
                continue
            bot.send_message(chat_id, 'Exception - updater не смог загрузить уровень(-вни)')
            DBSession.update_bool_flag(session['sessionid'], 'putupdatertask', 'True')
            return

    if not loaded_level:
        DBSession.update_bool_flag(session['sessionid'], 'putupdatertask', 'True')
        return

    try:
        loaded_helps = loaded_level['Helps']
        loaded_bonuses = loaded_level['Bonuses']
        loaded_sectors = loaded_level['Sectors']
        loaded_messages = loaded_level['Messages']
    except Exception:
        bot.send_message(chat_id, 'Exception - updater не смог вытащить элементы '
                                  '(сектора|бонусы|подсказки) загруженного уровня')
        DBSession.update_bool_flag(session['sessionid'], 'putupdatertask', 'True')
        return

    if not DBSession.get_field_value(session['sessionid'], 'currlevelid') or loaded_level['LevelId'] != session['currlevelid']:
        DBSession.update_int_field(session['sessionid'], 'currlevelid', loaded_level['LevelId'])
        try:
            reset_live_locations(chat_id, bot, session)
        except Exception:
            bot.send_message(chat_id, 'Exception - updater не смог сбросить информацию о live location')
        try:
            sectors_to_close = send_up_info(session['sessionid'], loaded_level, len(levels), loaded_helps,
                                            loaded_bonuses, bot, chat_id, session['channelname'], session['usechannel'])
            if session['channelname'] and session['usechannel']:
                send_unclosed_sectors_to_channel(loaded_level, sectors_to_close, bot, session['channelname'], session['sessionid'])
        except Exception:
            bot.send_message(chat_id, 'Exception - updater не смог прислать информацию об АПе')

        DBSession.update_bool_flag(session['sessionid'], 'putupdatertask', 'True')
        return

    DBSession.update_int_field(session['sessionid'], 'currlevelid', loaded_level['LevelId'])
    try:
        if not loaded_level['Timeout'] == 0 and loaded_level['TimeoutSecondsRemain'] <= 300 \
                and not DBLevels.get_time_to_up_sent(session['sessionid'], loaded_level['LevelId']):
            message = 'До автоперехода < 5 мин'
            bot.send_message(chat_id, message)
            DBLevels.update_time_to_up_sent(session['sessionid'], loaded_level['LevelId'], 'True')
    except Exception:
        bot.send_message(chat_id, 'Exception - updater не смог проанализировать время до автоперехода')

    try:
        if loaded_messages:
            message_parcer(session['sessionid'], session['gameid'], loaded_messages, bot, chat_id,
                           session['channelname'], session['usechannel'])
    except Exception as err:
        bot.send_message(chat_id, 'Exception - не удалось выполнить слежение за сообщениями авторов')
    try:
        if loaded_sectors:
            codes_to_find = loaded_level['SectorsLeftToClose']
            sectors_parcer(session['sessionid'], session['gameid'], loaded_sectors, codes_to_find, bot, chat_id)
    except Exception as err:
        bot.send_message(chat_id, 'Exception - не удалось выполнить слежение за секторами')
    try:
        if loaded_helps:
            help_parcer(session['sessionid'], session['gameid'], loaded_helps, bot, chat_id, session['channelname'],
                        session['usechannel'])
    except Exception as err:
        bot.send_message(chat_id, 'Exception - не удалось выполнить слежение за подсказками')
    try:
        if loaded_bonuses:
            bonus_parcer(session['sessionid'], session['gameid'], loaded_bonuses, bot, chat_id)
    except Exception as err:
        bot.send_message(chat_id, 'Exception - не удалось выполнить слежение за бонусами')
    try:
        if session['channelname'] and session['usechannel'] and session['sectorstoclose'] \
                and session['sectorstoclose'] != '1' and session['sectorsmessageid']:
            channel_sectors_editor(session['sessionid'], loaded_level, session['sectorstoclose'], bot,
                                   session['channelname'], session['sectorsmessageid'])
    except Exception as err:
        bot.send_message(chat_id, 'Exception - не удалось обновить не закрытые сектора в канале')
    try:
        dismissed_level_ids = DBLevels.get_dismissed_level_ids(session['sessionid'], session['gameid'])
        levels_parcer(session['sessionid'], session['gameid'], dismissed_level_ids, levels, bot, chat_id)
    except Exception as err:
        bot.send_message(chat_id, 'Exception - не удалось выполнить слежение за уровнями')

    DBSession.update_bool_flag(session['sessionid'], 'putupdatertask', 'True')


def storm_updater(chat_id, bot, session):
    existing_levels = DBLevels.get_level_ids_per_game(session['sessionid'], session['gameid'])
    game_model = get_current_game_model(session, bot, chat_id, from_updater=True)
    if not game_model:
        DBSession.update_bool_flag(session['sessionid'], 'putupdatertask', 'True')
        return

    if not existing_levels:
        for i in xrange(2):
            try:
                storm_levels = get_storm_levels(len(game_model['Levels']), session, bot, chat_id, from_updater=True)
                for level in storm_levels:
                    if level['LevelId'] not in existing_levels:
                        DBLevels.insert_level(session['sessionid'], session['gameid'], level)
                break
            except Exception:
                if i == 0:
                    continue
                bot.send_message(chat_id, 'Exception - updater не смог загрузить уровень(-вни)')
        DBSession.update_bool_flag(session['sessionid'], 'putupdatertask', 'True')
        return

    storm_levels = get_storm_levels(len(game_model['Levels']), session, bot, chat_id, from_updater=True)
    dismissed_level_ids = DBLevels.get_dismissed_level_ids(session['sessionid'], session['gameid'])
    passed_level_ids = DBLevels.get_passed_level_ids(session['sessionid'], session['gameid'])
    for level in storm_levels:
        if level['LevelId'] not in existing_levels:
            level = get_storm_level(level['Number'], session, bot, chat_id, from_updater=True)
            DBLevels.insert_level(session['sessionid'], session['gameid'], level)
            DBSession.update_bool_flag(session['sessionid'], 'putupdatertask', 'True')
            return

        try:
            if session['stopupdater']:
                DBSession.update_bool_flag(session['sessionid'], 'putupdatertask', 'False')
                return
            if level['LevelId'] in dismissed_level_ids or level['LevelId'] in passed_level_ids:
                continue

            loaded_helps = level['Helps']
            loaded_bonuses = level['Bonuses']
            loaded_sectors = level['Sectors']
            loaded_messages = level['Messages']

            levelmark = '<b>Уровень %s: %s</b>' % (str(level['Number']), level['Name'].encode('utf-8')) if level['Name'] \
                else '<b>Уровень %s</b>' % str(level['Number'])

            if loaded_messages:
                message_parcer(session['sessionid'], session['gameid'], loaded_messages, bot, chat_id,
                               session['channelname'], session['usechannel'], levelmark=levelmark, storm=True)
            if loaded_sectors:
                codes_to_find = level['SectorsLeftToClose']
                sectors_parcer(session['sessionid'], session['gameid'], loaded_sectors, codes_to_find, bot, chat_id,
                               levelmark=levelmark, storm=True)
            if loaded_helps:
                help_parcer(session['sessionid'], session['gameid'], loaded_helps, bot, chat_id, session['channelname'],
                            session['usechannel'], levelmark=levelmark, storm=True)
            if loaded_bonuses:
                bonus_parcer(session['sessionid'], session['gameid'], loaded_bonuses, bot, chat_id,
                             levelmark=levelmark, storm=True)
        except Exception:
            bot.send_message(chat_id, 'Exception - не удалось выполнить команду updater до конца')
    try:
        levels_parcer(session['sessionid'], session['gameid'], dismissed_level_ids, storm_levels, bot, chat_id, storm=True)
    except Exception:
        bot.send_message(chat_id, 'Exception - не удалось обновить информацию об уровнях')

    DBSession.update_bool_flag(session['sessionid'], 'putupdatertask', 'True')


def reset_live_locations(chat_id, bot, session):
    ll_message_ids = json.loads(session['llmessageids'])
    if ll_message_ids:
        close_live_locations(chat_id, bot, session, ll_message_ids)


def send_up_info(session_id, loaded_level, number_of_levels, loaded_helps, loaded_bonuses, bot, chat_id, channel_name, use_channel, block=''):
    try:
        up = '\xE2\x9D\x97#АП'
        name = loaded_level['Name'].encode('utf-8') if loaded_level['Name'] else 'без названия'
        level = '\r\n<b>Уровень %s из %s: %s</b>' % (str(loaded_level['Number']), str(number_of_levels),
                                                     name)
        time_to_up = '\r\nБез автоперехода' if loaded_level['Timeout'] == 0 else '\r\nАвтопереход: %s' %\
                                                                                 time_converter(loaded_level['Timeout'])
        codes_all = 1 if not loaded_level['Sectors'] else len(loaded_level['Sectors'])
        codes_to_find = 1 if not loaded_level['Sectors'] else loaded_level['RequiredSectorsCount']
        codes = '\r\nЗакрыть секторов: %s из %s' % (str(codes_to_find), str(codes_all))

        if loaded_level['HasAnswerBlockRule']:
            att_number = loaded_level['AttemtsNumber']
            att_period = time_converter(loaded_level['AttemtsPeriod'])
            att_object = 'команда' if loaded_level['BlockTargetId'] == 2 else 'игрок'
            block = '\r\n<b>БЛОКИРОВКА: %s / %s|%s</b>' % (str(att_number), att_period, att_object)

        helps = '\r\nПодсказок: %s, первая через %s' % (str(len(loaded_helps)),
                                                        time_converter(loaded_helps[0]['RemainSeconds'])) if loaded_helps\
            else '\r\nБез подсказок'
        bonuses = '\r\nБонусов: %s' % len(loaded_bonuses) if loaded_bonuses else '\r\nБез бонусов'

        up_message = up + level + time_to_up + codes + block + helps + bonuses

        bot.send_message(chat_id, up_message, parse_mode='HTML')
    except Exception:
        bot.send_message(chat_id, up + '\r\nException - updater не смог собрать и отправить информацию об уровне')

    send_task(session_id, loaded_level, bot, chat_id, from_updater=True)

    try:
        if channel_name and use_channel:
            bot.send_message(channel_name, up_message, parse_mode='HTML')
            send_task(session_id, loaded_level, bot, channel_name)
    except Exception:
        bot.send_message(chat_id, 'Exception - updater не смог отправить информацию по новому уровню в канал')

    try:
        sectors_to_close = get_sectors_to_close(loaded_level['Sectors'], get_sector_names=True)
    except Exception:
        bot.send_message(chat_id, 'Exception - updater не смог составить список секторов')
        sectors_to_close = 'Exception - updater не смог составить список секторов'

    DBSession.update_text_field(session_id, 'sectorstoclose', sectors_to_close)
    return sectors_to_close


def send_unclosed_sectors_to_channel(loaded_level, sectors_to_close, bot, channel_name, session_id):
    try:
        codes_all = 1 if not loaded_level['Sectors'] else len(loaded_level['Sectors'])
        codes_to_find = 1 if not loaded_level['Sectors'] else loaded_level['SectorsLeftToClose']
        message = '<b>Осталось закрыть: %s из %s:</b>\r\n%s' % (str(codes_to_find), str(codes_all), sectors_to_close)
        response = bot.send_message(channel_name, message, parse_mode='HTML')
    except Exception:
        response = bot.send_message(channel_name, 'Exception - updater не смог прислать не закрытые сектора')
    DBSession.update_int_field(session_id, 'sectorsmessageid', response.message_id)


def sectors_parcer(session_id, game_id, loaded_sectors, codes_to_find, bot, chat_id, levelmark=None, storm=False):
    existing_sectors = DBSectors.get_sector_ids_per_game(session_id, game_id)
    for sector in loaded_sectors:
        if sector['SectorId'] not in existing_sectors:
            DBSectors.insert_sector(session_id, game_id, sector['SectorId'])

        if sector['IsAnswered'] and DBSectors.get_answer_info_not_sent(session_id, game_id, sector['SectorId']):

            code = sector['Answer']['Answer'].encode('utf-8')
            player = sector['Answer']['Login'].encode('utf-8')
            name = sector['Name'].encode('utf-8')
            codes_all = len(loaded_sectors)
            sectors_to_close = get_sectors_to_close(loaded_sectors)
            message = '<b>с-р: ' + name + ' - </b>' + '\xE2\x9C\x85' + '<b> (' + player + ': ' + code + ')</b>' \
                      '\r\nОсталось закрыть: %s из %s:\r\n%s' % (str(codes_to_find), str(codes_all), sectors_to_close)
            if storm:
                message = levelmark + '\r\n' + message
            bot.send_message(chat_id, message, parse_mode='HTML')
            DBSectors.update_answer_info_not_sent(session_id, game_id, sector['SectorId'], 'False')


# def sectors_parcer(session_id, game_id, loaded_sectors, codes_to_find, bot, chat_id, levelmark=None, storm=False):
#     existing_sectors = DBSectors.get_sector_ids_per_game(session_id, game_id)
#     for sector in loaded_sectors:
#         if sector['SectorId'] not in existing_sectors:
#             DBSectors.insert_sector(session_id, game_id, sector['SectorId'])
#     answer_info_not_sent_sectors = DBSectors.get_answer_info_not_sent_sector_ids_per_game(session_id, game_id)
#     for sector in loaded_sectors:
#         if sector['IsAnswered'] and sector['SectorId'] in answer_info_not_sent_sectors:
#
#             code = sector['Answer']['Answer'].encode('utf-8')
#             player = sector['Answer']['Login'].encode('utf-8')
#             name = sector['Name'].encode('utf-8')
#             codes_all = len(loaded_sectors)
#             sectors_to_close = get_sectors_to_close(loaded_sectors)
#             message = '<b>с-р: ' + name + ' - </b>' + '\xE2\x9C\x85' + '<b> (' + player + ': ' + code + ')</b>' \
#                       '\r\nОсталось закрыть: %s из %s:\r\n%s' % (str(codes_to_find), str(codes_all), sectors_to_close)
#             if storm:
#                 message = levelmark + '\r\n' + message
#             bot.send_message(chat_id, message, parse_mode='HTML')
#             DBSectors.update_answer_info_not_sent(session_id, game_id, sector['SectorId'], 'False')


def help_parcer(session_id, game_id, loaded_helps, bot, chat_id, channel_name, use_channel, levelmark=None, storm=False):
    existing_helps = DBHelps.get_help_ids_per_game(session_id, game_id)
    for help in loaded_helps:
        if help['HelpId'] not in existing_helps:
            DBHelps.insert_help(session_id, game_id, help['HelpId'])

        if help['HelpText'] is not None and DBHelps.get_field_value(session_id, game_id, help['HelpId'], 'notsent'):
            DBHelps.update_bool_flag(session_id, game_id, help['HelpId'], 'notsent', 'False')
            DBHelps.update_bool_flag(session_id, game_id, help['HelpId'], 'timenotsent', 'False')
            send_help(help, bot, chat_id, session_id, from_updater=True, storm=storm, levelmark=levelmark)
            if channel_name and use_channel:
                send_help(help, bot, channel_name, session_id, storm=storm, levelmark=levelmark)
            continue
        if help['RemainSeconds'] <= 180 and DBHelps.get_field_value(session_id, game_id, help['HelpId'], 'timenotsent'):
            DBHelps.update_bool_flag(session_id, game_id, help['HelpId'], 'timenotsent', 'False')
            send_time_to_help(help, bot, chat_id, levelmark, storm)


# def help_parcer(session_id, game_id, loaded_helps, bot, chat_id, channel_name, use_channel, levelmark=None, storm=False):
#     existing_helps = DBHelps.get_help_ids_per_game(session_id, game_id)
#     for help in loaded_helps:
#         if help['HelpId'] not in existing_helps:
#             DBHelps.insert_help(session_id, game_id, help['HelpId'])
#     helps_not_sent = DBHelps.get_not_sent_help_ids_per_game(session_id, game_id)
#     helps_time_not_sent = DBHelps.get_time_not_sent_help_ids_per_game(session_id, game_id)
#     for help in loaded_helps:
#         if help['HelpText'] is not None and help['HelpId'] in helps_not_sent:
#             DBHelps.update_bool_flag(session_id, game_id, help['HelpId'], 'notsent', 'False')
#             DBHelps.update_bool_flag(session_id, game_id, help['HelpId'], 'timenotsent', 'False')
#             send_help(help, bot, chat_id, session_id, from_updater=True, storm=storm, levelmark=levelmark)
#             if channel_name and use_channel:
#                 send_help(help, bot, channel_name, session_id, storm=storm, levelmark=levelmark)
#             continue
#         if help['RemainSeconds'] <= 180 and help['HelpId'] in helps_time_not_sent:
#             DBHelps.update_bool_flag(session_id, game_id, help['HelpId'], 'timenotsent', 'False')
#             send_time_to_help(help, bot, chat_id, levelmark, storm)


def bonus_parcer(session_id, game_id, loaded_bonuses, bot, chat_id, levelmark=None, storm=False):
    existing_bonuses = DBBonuses.get_bonus_ids_per_game(session_id, game_id)
    for bonus in loaded_bonuses:
        if bonus['BonusId'] not in existing_bonuses:
            DBBonuses.insert_bonus(session_id, game_id, bonus['BonusId'])

        if bonus['IsAnswered'] and DBBonuses.get_field_value(session_id, game_id, bonus['BonusId'], 'awardnotsent'):
            DBBonuses.update_bool_flag(session_id, game_id, bonus['BonusId'], 'awardnotsent', 'False')
            DBBonuses.update_bool_flag(session_id, game_id, bonus['BonusId'], 'infonotsent', 'False')
            send_bonus_award_answer(bonus, bot, chat_id, session_id, from_updater=True, storm=storm, levelmark=levelmark)
            continue
        if bonus['Task'] and not bonus['Expired'] and DBBonuses.get_field_value(session_id, game_id, bonus['BonusId'], 'infonotsent'):
            DBBonuses.update_bool_flag(session_id, game_id, bonus['BonusId'], 'infonotsent', 'False')
            if not storm:
                send_bonus_info(bonus, bot, chat_id, session_id, from_updater=True, storm=storm, levelmark=levelmark)


# def bonus_parcer(session_id, game_id, loaded_bonuses, bot, chat_id, levelmark=None, storm=False):
#     existing_bonuses = DBBonuses.get_bonus_ids_per_game(session_id, game_id)
#     for bonus in loaded_bonuses:
#         if bonus['BonusId'] not in existing_bonuses:
#             DBBonuses.insert_bonus(session_id, game_id, bonus['BonusId'])
#     bonuses_award_not_sent = DBBonuses.get_award_not_sent_bonus_ids_per_game(session_id, game_id)
#     bonuses_info_not_sent = DBBonuses.get_info_not_sent_bonus_ids_per_game(session_id, game_id)
#     for bonus in loaded_bonuses:
#
#         if bonus['IsAnswered'] and bonus['BonusId'] in bonuses_award_not_sent:
#             DBBonuses.update_bool_flag(session_id, game_id, bonus['BonusId'], 'awardnotsent', 'False')
#             DBBonuses.update_bool_flag(session_id, game_id, bonus['BonusId'], 'infonotsent', 'False')
#             send_bonus_award_answer(bonus, bot, chat_id, session_id, from_updater=True, storm=storm, levelmark=levelmark)
#             continue
#         if bonus['Task'] and not bonus['Expired'] and bonus['BonusId'] in bonuses_info_not_sent:
#             DBBonuses.update_bool_flag(session_id, game_id, bonus['BonusId'], 'infonotsent', 'False')
#             if not storm:
#                 send_bonus_info(bonus, bot, chat_id, session_id, from_updater=True, storm=storm, levelmark=levelmark)


def message_parcer(session_id, game_id, loaded_messages, bot, chat_id, channel_name, use_channel, levelmark=None, storm=False):
    existing_messages = DBMessages.get_message_ids_per_game(session_id, game_id)
    for message in loaded_messages:
        if message['MessageId'] not in existing_messages:
            DBMessages.insert_message(session_id, game_id, message['MessageId'])

        if DBMessages.get_message_not_sent(session_id, game_id, message['MessageId']):
            DBMessages.update_message_not_sent(session_id, game_id, message['MessageId'], 'False')
            send_adm_message(message, bot, chat_id, session_id, from_updater=True, storm=storm, levelmark=levelmark)
            if channel_name and use_channel:
                send_adm_message(message, bot, channel_name, session_id, storm=storm, levelmark=levelmark)


# def message_parcer(session_id, game_id, loaded_messages, bot, chat_id, channel_name, use_channel, levelmark=None, storm=False):
#     existing_messages = DBMessages.get_message_ids_per_game(session_id, game_id)
#     for message in loaded_messages:
#         if message['MessageId'] not in existing_messages:
#             DBMessages.insert_message(session_id, game_id, message['MessageId'])
#     not_sent_messages = DBMessages.get_not_sent_message_ids_per_game(session_id, game_id)
#     for message in loaded_messages:
#         if message['MessageId'] in not_sent_messages:
#             DBMessages.update_message_not_sent(session_id, game_id, message['MessageId'], 'False')
#             send_adm_message(message, bot, chat_id, session_id, from_updater=True, storm=storm, levelmark=levelmark)
#             if channel_name and use_channel:
#                 send_adm_message(message, bot, channel_name, session_id, storm=storm, levelmark=levelmark)


def levels_parcer(session_id, game_id, dismissed_level_ids, levels, bot, chat_id, storm=False):
    for level in levels:
        if level['Dismissed'] and level['LevelId'] not in dismissed_level_ids:
            text = '\xE2\x9D\x97 <b>Уровень %s, "%s" - снят</b> \xE2\x9D\x97' % (str(level['LevelNumber']),
                                                                                 level['LevelName'].encode('utf-8')) \
                if level['LevelName'] else '\xE2\x9D\x97 <b>Уровень %s - снят</b> \xE2\x9D\x97' % str(level['LevelNumber'])
            bot.send_message(chat_id, text, parse_mode='HTML')
            DBLevels.update_bool_field(session_id, game_id, level['LevelId'], 'dismissed', 'True')
        if not level['Dismissed'] and level['LevelId'] in dismissed_level_ids:
            text = '\xE2\x9D\x97 <b>Уровень %s, "%s" - возвращен</b> \xE2\x9D\x97' % (str(level['LevelNumber']), level['LevelName'].encode('utf-8')) \
                if level['LevelName'] else '\xE2\x9D\x97 <b>Уровень %s - возвращен</b> \xE2\x9D\x97' % str(level['LevelNumber'])
            bot.send_message(chat_id, text, parse_mode='HTML')
            DBLevels.update_bool_field(session_id, game_id, level['LevelId'], 'dismissed', 'False')

        if storm and level['IsPassed']:
            DBLevels.update_bool_field(session_id, game_id, level['LevelId'], 'ispassed', 'True')


def channel_sectors_editor(session_id, loaded_level, old_sectors_to_close, bot, channel_name, message_id):
    new_sectors_to_close = get_sectors_to_close(loaded_level['Sectors'], get_sector_names=True)
    if new_sectors_to_close != old_sectors_to_close:
        codes_all = 1 if not loaded_level['Sectors'] else len(loaded_level['Sectors'])
        codes_to_find = 1 if not loaded_level['Sectors'] else loaded_level['SectorsLeftToClose']
        message = '<b>Осталось закрыть: %s из %s:</b>\r\n%s' % \
                  (str(codes_to_find), str(codes_all), new_sectors_to_close)
        bot.edit_message_text(message, channel_name, message_id, parse_mode='HTML')
        DBSession.update_text_field(session_id, 'sectorstoclose', new_sectors_to_close)


def get_sectors_to_close(sectors, get_sector_names=False):
    sectors_to_close = ''

    if not sectors:
        sectors_to_close = '1'
    elif get_sector_names:
        for i, sector in enumerate(get_unclosed_sectors(sectors)):
            sectors_to_close += sector['Name'].encode('utf-8') if i == 0 else '\r\n' + sector['Name'].encode('utf-8')
    else:
        for i, sector in enumerate(get_unclosed_sectors(sectors)):
            sectors_to_close += str(sector['Order']) if i == 0 else ', ' + str(sector['Order'])
    return sectors_to_close


def get_unclosed_sectors(sectors):
    return [sector for sector in sectors if not sector['IsAnswered']]
