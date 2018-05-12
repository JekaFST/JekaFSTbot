# -*- coding: utf-8 -*-
import threading
import json
import logging
from DBMethods import DBSession, DBLevels, DBHelps, DBBonuses, DBSectors, DBMessages
from ExceptionHandler import ExceptionHandler
from SessionMethods import get_current_level, get_storm_level, get_storm_levels, get_current_game_model
from CommonMethods import send_help, send_time_to_help, send_task, time_converter, send_bonus_info,\
    send_bonus_award_answer, send_adm_message, close_live_locations


def updater(task, bot):
    session = DBSession.get_session(task.session_id)
    if not session['stormgame']:
        name = 'upd_thread_%s' % task.chat_id
        task.updaters_dict[task.chat_id] = threading.Thread(name=name, target=linear_updater,
                                                            args=(bot, task.chat_id, session))
        task.updaters_dict[task.chat_id].start()
        return
    else:
        name = 'upd_thread_%s' % task.chat_id
        task.updaters_dict[task.chat_id] = threading.Thread(name=name, target=storm_updater,
                                                            args=(bot, task.chat_id, session))
        task.updaters_dict[task.chat_id].start()
        return


@ExceptionHandler.updater_exception
def linear_updater(bot, chat_id, session):
    loaded_level, levels = get_levels_for_updater(bot, chat_id, session)
    if not loaded_level:
        DBSession.update_bool_flag(session['sessionid'], 'putupdatertask', 'True')
        return

    if not DBSession.get_field_value(session['sessionid'], 'currlevelid') or loaded_level['LevelId'] != session['currlevelid']:
        DBSession.update_int_field(session['sessionid'], 'currlevelid', loaded_level['LevelId'])
        reset_live_locations(bot, chat_id, session, message='Exception - updater не смог сбросить информацию о live location')
        send_up_message(bot, chat_id, loaded_level=loaded_level, number_of_levels=len(levels),
                        channel_name=session['channelname'], use_channel=session['usechannel'],
                        message='\xE2\x9D\x97#АП\r\nException - updater не смог собрать и отправить информацию о новом уровне')
        send_task_after_up(bot, chat_id, session, loaded_level=loaded_level,
                           message='Exception - updater не смог отправить задание нового уровня в канал')
        send_unclosed_sectors_to_channel(bot, chat_id, session, loaded_level=loaded_level,
                                         message='Exception - updater не смог отправить или сохранить сообщение с секторами из канала')

        DBSession.update_bool_flag(session['sessionid'], 'putupdatertask', 'True')
        return

    DBSession.update_int_field(session['sessionid'], 'currlevelid', loaded_level['LevelId'])

    timeout_parcer(bot, chat_id, session, loaded_level=loaded_level,
                   message='Exception - updater не смог проанализировать время до автоперехода')

    if loaded_level['Messages']:
        message_parcer(bot, chat_id, session, loaded_messages=loaded_level['Messages'], levelmark=None, storm=False,
                       message='Exception - не удалось выполнить слежение за сообщениями авторов')
    if loaded_level['Sectors']:
        codes_to_find = loaded_level['SectorsLeftToClose']
        sectors_parcer(bot, chat_id, session, loaded_sectors=loaded_level['Sectors'], codes_to_find=codes_to_find,
                       level_id=loaded_level['LevelId'], levelmark=None, storm=False,
                       message='Exception - не удалось выполнить слежение за секторами')
    if loaded_level['Helps']:
        help_parcer(bot, chat_id, session, loaded_helps=loaded_level['Helps'], levelmark=None, storm=False,
                    message='Exception - не удалось выполнить слежение за подсказками')
    if loaded_level['Bonuses']:
        bonus_parcer(bot, chat_id, session, loaded_bonuses=loaded_level['Bonuses'], level_id=loaded_level['LevelId'],
                     levelmark=None, storm=False, message='Exception - не удалось выполнить слежение за бонусами')

    channel_sectors_editor(bot, chat_id, session, loaded_level=loaded_level,
                           message='Exception - не удалось обновить не закрытые сектора в канале')

    dismissed_level_ids = DBLevels.get_dismissed_level_ids(session['sessionid'], session['gameid'])
    levels_parcer(bot, chat_id, session, levels=levels, dismissed_level_ids=dismissed_level_ids, storm=False,
                  message='Exception - не удалось выполнить слежение за уровнями')

    DBSession.update_bool_flag(session['sessionid'], 'putupdatertask', 'True')


@ExceptionHandler.updater_exception
def storm_updater(bot, chat_id, session):
    existing_levels = DBLevels.get_level_ids_per_game(session['sessionid'], session['gameid'])
    game_model = get_current_game_model(session, bot, chat_id, from_updater=True)
    if not game_model:
        DBSession.update_bool_flag(session['sessionid'], 'putupdatertask', 'True')
        return

    if not existing_levels:
        for i in xrange(2):
            try:
                for level in game_model['Levels']:
                    if level['LevelId'] not in existing_levels:
                        DBLevels.insert_level(session['sessionid'], session['gameid'], level, breif=True)
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
        if session['stopupdater']:
            DBSession.update_bool_flag(session['sessionid'], 'putupdatertask', 'False')
            return
        if level['LevelId'] not in existing_levels:
            level = get_storm_level(level['Number'], session, bot, chat_id, from_updater=True)
            DBLevels.insert_level(session['sessionid'], session['gameid'], level)
            DBSession.update_bool_flag(session['sessionid'], 'putupdatertask', 'True')
            return

        if level['LevelId'] in dismissed_level_ids or level['LevelId'] in passed_level_ids:
            continue

        levelmark = '<b>Уровень %s: %s</b>' % (str(level['Number']), level['Name'].encode('utf-8')) if level['Name'] \
            else '<b>Уровень %s</b>' % str(level['Number'])

        if level['Messages']:
            message_parcer(bot, chat_id, session, loaded_messages=level['Messages'], levelmark=levelmark, storm=True,
                           message='Exception - не удалось выполнить слежение за сообщениями авторов')
        if level['Sectors']:
            codes_to_find = level['SectorsLeftToClose']
            sectors_parcer(bot, chat_id, session, loaded_sectors=level['Sectors'], codes_to_find=codes_to_find,
                           level_id=level['LevelId'], levelmark=levelmark, storm=True,
                           message='Exception - не удалось выполнить слежение за секторами')
        if level['Helps']:
            help_parcer(bot, chat_id, session, loaded_helps=level['Helps'], levelmark=levelmark, storm=True,
                        message='Exception - не удалось выполнить слежение за подсказками')
        if level['Bonuses']:
            bonus_parcer(bot, chat_id, session, loaded_bonuses=level['Bonuses'], level_id=level['LevelId'],
                         levelmark=levelmark, storm=True, message='Exception - не удалось выполнить слежение за бонусами')

    levels_parcer(bot, chat_id, session, levels=storm_levels, dismissed_level_ids=dismissed_level_ids, storm=True,
                  passed_level_ids=passed_level_ids, message='Exception - не удалось выполнить слежение за уровнями')

    DBSession.update_bool_flag(session['sessionid'], 'putupdatertask', 'True')


@ExceptionHandler.get_levels_updater_exception
def get_levels_for_updater(bot, chat_id, session):
    loaded_level, levels = get_current_level(session, bot, chat_id, from_updater=True)
    return loaded_level, levels


@ExceptionHandler.common_updater_exception
def reset_live_locations(bot, chat_id, session, **kwargs):
    DBSession.update_json_field(session['sessionid'], 'locations', {})
    ll_message_ids = json.loads(session['llmessageids'])
    if ll_message_ids:
        close_live_locations(chat_id, bot, session, ll_message_ids)


@ExceptionHandler.up_message_exception
def send_up_message(bot, chat_id, **kwargs):
    block = ''
    loaded_level = kwargs['loaded_level']
    up = '\xE2\x9D\x97#АП'
    name = loaded_level['Name'].encode('utf-8') if loaded_level['Name'] else 'без названия'
    level = '\r\n<b>Уровень %s из %s: %s</b>' % (str(loaded_level['Number']), str(kwargs['number_of_levels']),
                                                 name)
    time_to_up = '\r\nБез автоперехода' if loaded_level['Timeout'] == 0 else '\r\nАвтопереход: %s' % \
                                                                             time_converter(loaded_level['Timeout'])
    codes_all = 1 if not loaded_level['Sectors'] else len(loaded_level['Sectors'])
    codes_to_find = 1 if not loaded_level['Sectors'] else loaded_level['RequiredSectorsCount']
    codes = '\r\nЗакрыть секторов: %s из %s' % (str(codes_to_find), str(codes_all))

    if loaded_level['HasAnswerBlockRule']:
        att_number = loaded_level['AttemtsNumber']
        att_period = time_converter(loaded_level['AttemtsPeriod'])
        att_object = 'команда' if loaded_level['BlockTargetId'] == 2 else 'игрок'
        block = '\r\n<b>БЛОКИРОВКА: %s / %s|%s</b>' % (str(att_number), att_period, att_object)

    helps = '\r\nПодсказок: %s, первая через %s' % (str(len(loaded_level['Helps'])),
                                                    time_converter(loaded_level['Helps'][0]['RemainSeconds'])) if loaded_level['Helps'] \
        else '\r\nБез подсказок'
    bonuses = '\r\nБонусов: %s' % len(loaded_level['Bonuses']) if loaded_level['Bonuses'] else '\r\nБез бонусов'

    up_message = up + level + time_to_up + codes + block + helps + bonuses

    bot.send_message(chat_id, up_message, parse_mode='HTML')
    if kwargs['channel_name'] and kwargs['use_channel']:
        bot.send_message(kwargs['channel_name'], up_message, parse_mode='HTML')


@ExceptionHandler.common_updater_exception
def send_task_after_up(bot, chat_id, session, **kwargs):
    send_task(session['sessionid'], kwargs['loaded_level'], bot, chat_id, from_updater=True)
    if session['channelname'] and session['usechannel']:
        send_task(session['sessionid'], kwargs['loaded_level'], bot, session['channelname'])


@ExceptionHandler.common_updater_exception
def send_unclosed_sectors_to_channel(bot, chat_id, session, **kwargs):
    if session['channelname'] and session['usechannel']:
        loaded_level = kwargs['loaded_level']
        try:
            sectors_to_close = get_sectors_to_close(loaded_level['Sectors'], get_sector_names=True)
        except Exception:
            sectors_to_close = 'Список секторов не составлен'
            logging.exception('Exception - cписок секторов не составлен')
        DBSession.update_text_field(session['sessionid'], 'sectorstoclose', sectors_to_close)
        codes_all = 1 if not loaded_level['Sectors'] else len(loaded_level['Sectors'])
        codes_to_find = 1 if not loaded_level['Sectors'] else loaded_level['SectorsLeftToClose']
        message = '<b>Осталось закрыть: %s из %s:</b>\r\n%s' % (str(codes_to_find), str(codes_all), sectors_to_close)
        try:
            response = bot.send_message(session['channelname'], message, parse_mode='HTML')
        except Exception:
            response = bot.send_message(session['channelname'], 'Exception - updater не смог прислать не закрытые сектора')
            logging.exception('Exception - updater не смог прислать не закрытые сектора')
        DBSession.update_int_field(session['sessionid'], 'sectorsmessageid', response.message_id)


@ExceptionHandler.common_updater_exception
def timeout_parcer(bot, chat_id, session, **kwargs):
    loaded_level = kwargs['loaded_level']
    if not loaded_level['Timeout'] == 0 and loaded_level['TimeoutSecondsRemain'] <= 300 \
            and not DBLevels.get_time_to_up_sent(session['sessionid'], loaded_level['LevelId']):
        message = 'До автоперехода 5 мин'
        bot.send_message(chat_id, message)
        DBLevels.update_time_to_up_sent(session['sessionid'], loaded_level['LevelId'], 'True')


@ExceptionHandler.common_updater_exception
def sectors_parcer(bot, chat_id, session, **kwargs):
    existing_sectors = DBSectors.get_sector_ids_per_game(session['sessionid'], session['gameid'])
    for sector in kwargs['loaded_sectors']:
        if sector['SectorId'] not in existing_sectors:
            DBSectors.insert_sector(session['sessionid'], session['gameid'], sector, kwargs['level_id'])
    answer_info_not_sent_sectors = DBSectors.get_answer_info_not_sent_sector_ids_per_game(session['sessionid'], session['gameid'])
    for sector in kwargs['loaded_sectors']:
        if sector['IsAnswered'] and sector['SectorId'] in answer_info_not_sent_sectors:

            code = sector['Answer']['Answer'].encode('utf-8')
            player = sector['Answer']['Login'].encode('utf-8')
            name = sector['Name'].encode('utf-8')
            codes_all = len(kwargs['loaded_sectors'])
            sectors_to_close = get_sectors_to_close(kwargs['loaded_sectors'])
            message = '<b>с-р: ' + name + ' - </b>' + '\xE2\x9C\x85' + '<b> (' + player + ': ' + code + ')</b>' \
                      '\r\nОсталось закрыть: %s из %s:\r\n%s' % (str(kwargs['codes_to_find']), str(codes_all), sectors_to_close)
            if kwargs['storm']:
                message = kwargs['levelmark'] + '\r\n' + message
            bot.send_message(chat_id, message, parse_mode='HTML')
            DBSectors.update_answer_info_not_sent(session['sessionid'], session['gameid'], sector['SectorId'], 'False', code, player)


@ExceptionHandler.common_updater_exception
def help_parcer(bot, chat_id, session, **kwargs):
    existing_helps = DBHelps.get_help_ids_per_game(session['sessionid'], session['gameid'])
    for help in kwargs['loaded_helps']:
        if help['HelpId'] not in existing_helps:
            DBHelps.insert_help(session['sessionid'], session['gameid'], help['HelpId'])
    helps_not_sent = DBHelps.get_not_sent_help_ids_per_game(session['sessionid'], session['gameid'])
    helps_time_not_sent = DBHelps.get_time_not_sent_help_ids_per_game(session['sessionid'], session['gameid'])
    for help in kwargs['loaded_helps']:
        if help['HelpText'] is not None and help['HelpId'] in helps_not_sent:
            DBHelps.update_bool_flag(session['sessionid'], session['gameid'], help['HelpId'], 'notsent', 'False')
            DBHelps.update_bool_flag(session['sessionid'], session['gameid'], help['HelpId'], 'timenotsent', 'False')
            send_help(help, bot, chat_id, session['sessionid'], from_updater=True, storm=kwargs['storm'], levelmark=kwargs['levelmark'])
            if session['channelname'] and session['usechannel']:
                send_help(help, bot, session['channelname'], session['sessionid'], storm=kwargs['storm'], levelmark=kwargs['levelmark'])
            continue
        if help['RemainSeconds'] <= 180 and help['HelpId'] in helps_time_not_sent:
            DBHelps.update_bool_flag(session['sessionid'], session['gameid'], help['HelpId'], 'timenotsent', 'False')
            send_time_to_help(help, bot, chat_id, kwargs['levelmark'], kwargs['storm'])


@ExceptionHandler.common_updater_exception
def bonus_parcer(bot, chat_id, session, **kwargs):
    existing_bonuses = DBBonuses.get_bonus_ids_per_level(session['sessionid'], session['gameid'], kwargs['level_id'])
    for bonus in kwargs['loaded_bonuses']:
        if bonus['BonusId'] not in existing_bonuses:
            bonuses_award_sent = DBBonuses.get_award_sent_bonus_ids_per_game(session['sessionid'], session['gameid'])
            award_not_sent = False if bonus['BonusId'] in bonuses_award_sent else True
            if award_not_sent:
                bonuses_info_sent = DBBonuses.get_info_sent_bonus_ids_per_game(session['sessionid'], session['gameid'])
                info_not_sent = False if bonus['BonusId'] in bonuses_info_sent else True
            else:
                info_not_sent = False
            DBBonuses.insert_bonus(session['sessionid'], session['gameid'], bonus, kwargs['level_id'], info_not_sent, award_not_sent)
    bonuses_award_not_sent = DBBonuses.get_award_not_sent_bonus_ids_per_game(session['sessionid'], session['gameid'])
    bonuses_info_not_sent = DBBonuses.get_info_not_sent_bonus_ids_per_game(session['sessionid'], session['gameid'])
    for bonus in kwargs['loaded_bonuses']:

        if bonus['IsAnswered'] and bonus['BonusId'] in bonuses_award_not_sent:
            DBBonuses.update_answer_info_not_sent(session['sessionid'], session['gameid'], bonus, 'awardnotsent', 'False')
            DBBonuses.update_bool_flag(session['sessionid'], session['gameid'], bonus['BonusId'], 'infonotsent', 'False')
            send_bonus_award_answer(bonus, bot, chat_id, session['sessionid'], from_updater=True, storm=kwargs['storm'],
                                    levelmark=kwargs['levelmark'])
            continue
        if not kwargs['storm']:
            if bonus['Task'] and not bonus['Expired'] and bonus['BonusId'] in bonuses_info_not_sent:
                DBBonuses.update_bool_flag(session['sessionid'], session['gameid'], bonus['BonusId'], 'infonotsent', 'False')
                send_bonus_info(bonus, bot, chat_id, session['sessionid'], from_updater=True, storm=kwargs['storm'],
                                levelmark=kwargs['levelmark'])


@ExceptionHandler.common_updater_exception
def message_parcer(bot, chat_id, session, **kwargs):
    existing_messages = DBMessages.get_message_ids_per_game(session['sessionid'], session['gameid'])
    for message in kwargs['loaded_messages']:
        if message['MessageId'] not in existing_messages:
            DBMessages.insert_message(session['sessionid'], session['gameid'], message['MessageId'])
    not_sent_messages = DBMessages.get_not_sent_message_ids_per_game(session['sessionid'], session['gameid'])
    for message in kwargs['loaded_messages']:
        if message['MessageId'] in not_sent_messages:
            DBMessages.update_message_not_sent(session['sessionid'], session['gameid'], message['MessageId'], 'False')
            send_adm_message(message, bot, chat_id, session['sessionid'], from_updater=True, storm=kwargs['storm'],
                             levelmark=kwargs['levelmark'])
            if session['channelname'] and session['usechannel']:
                send_adm_message(message, bot, session['channelname'], session['sessionid'], storm=kwargs['storm'],
                                 levelmark=kwargs['levelmark'])


@ExceptionHandler.common_updater_exception
def levels_parcer(bot, chat_id, session, **kwargs):
    existing_levels = DBLevels.get_level_ids_per_game(session['sessionid'], session['gameid'])
    for level in kwargs['levels']:
        if level['LevelId'] not in existing_levels:
            DBLevels.insert_level(session['sessionid'], session['gameid'], level) if kwargs['storm'] \
                else DBLevels.insert_level(session['sessionid'], session['gameid'], level, breif=True)
    for level in kwargs['levels']:
        if level['Dismissed'] and level['LevelId'] not in kwargs['dismissed_level_ids']:
            text = '\xE2\x9D\x97 <b>Уровень %s, "%s" - снят</b> \xE2\x9D\x97' % \
                   (str(level['LevelNumber']), level['LevelName'].encode('utf-8')) if level['LevelName'] \
                else '\xE2\x9D\x97 <b>Уровень %s - снят</b> \xE2\x9D\x97' % str(level['LevelNumber'])
            bot.send_message(chat_id, text, parse_mode='HTML')
            DBLevels.update_bool_field(session['sessionid'], session['gameid'], level['LevelId'], 'dismissed', 'True')
        if not level['Dismissed'] and level['LevelId'] in kwargs['dismissed_level_ids']:
            text = '\xE2\x9D\x97 <b>Уровень %s, "%s" - возвращен</b> \xE2\x9D\x97' % \
                   (str(level['LevelNumber']), level['LevelName'].encode('utf-8')) if level['LevelName'] \
                else '\xE2\x9D\x97 <b>Уровень %s - возвращен</b> \xE2\x9D\x97' % str(level['LevelNumber'])
            bot.send_message(chat_id, text, parse_mode='HTML')
            DBLevels.update_bool_field(session['sessionid'], session['gameid'], level['LevelId'], 'dismissed', 'False')

        if kwargs['storm'] and level['IsPassed'] and level['LevelId'] not in kwargs['passed_level_ids']:
            DBLevels.update_bool_field(session['sessionid'], session['gameid'], level['LevelId'], 'ispassed', 'True')


@ExceptionHandler.common_updater_exception
def channel_sectors_editor(bot, chat_id, session, **kwargs):
    if session['channelname'] and session['usechannel'] and session['sectorstoclose'] and session['sectorstoclose'] != '1' \
            and session['sectorsmessageid']:
        loaded_level = kwargs['loaded_level']
        new_sectors_to_close = get_sectors_to_close(loaded_level['Sectors'], get_sector_names=True)
        if new_sectors_to_close != session['sectorstoclose']:
            codes_all = 1 if not loaded_level['Sectors'] else len(loaded_level['Sectors'])
            codes_to_find = 1 if not loaded_level['Sectors'] else loaded_level['SectorsLeftToClose']
            message = '<b>Осталось закрыть: %s из %s:</b>\r\n%s' % \
                      (str(codes_to_find), str(codes_all), new_sectors_to_close)
            bot.edit_message_text(message, session['channelname'], session['sectorsmessageid'], parse_mode='HTML')
            DBSession.update_text_field(session['sessionid'], 'sectorstoclose', new_sectors_to_close)


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
