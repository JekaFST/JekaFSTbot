# -*- coding: utf-8 -*-
import json
import threading

from Config import coord_bots
from SessionMethods import get_current_level, get_storm_level, get_storm_levels, get_current_game_model
from CommonMethods import send_help, send_time_to_help, send_task, time_converter, send_bonus_info,\
    send_bonus_award_answer, send_adm_message


def updater(chat_id, bot, session, updaters_dict):
    if not session.storm_game:
        name = 'upd_thread_%s' % chat_id
        updaters_dict[chat_id] = threading.Thread(name=name, target=linear_updater, args=(chat_id, bot, session))
        updaters_dict[chat_id].start()
        # linear_updater(chat_id, bot, session)
        return
    else:
        name = 'upd_thread_%s' % chat_id
        updaters_dict[chat_id] = threading.Thread(name=name, target=storm_updater, args=(chat_id, bot, session))
        updaters_dict[chat_id].start()
        # storm_updater(chat_id, bot, session)
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
            session.put_updater_task = True
            return

    if not loaded_level:
        session.put_updater_task = True
        return

    try:
        loaded_helps = loaded_level['Helps']
        loaded_bonuses = loaded_level['Bonuses']
        loaded_sectors = loaded_level['Sectors']
        loaded_messages = loaded_level['Messages']
    except Exception:
        bot.send_message(chat_id, 'Exception - updater не смог вытащить элементы '
                                  '(сектора|бонусы|подсказки) загруженного уровня')
        session.put_updater_task = True
        return

    if not session.current_level:
        session.current_level = loaded_level
        session.help_statuses, session.bonus_statuses, session.time_to_up_sent, session.sector_statuses, \
                                                                        session.message_statuses = reset_level_vars()
        try:
            reset_live_locations(chat_id, bot, session)
        except Exception:
            bot.send_message(chat_id, 'Exception - updater не смог сбросить информацию о live location')
        try:
            session.sectors_to_close = send_up_info(loaded_level, len(levels), loaded_helps, loaded_bonuses, bot, chat_id,
                                                session.channel_name, session.use_channel, session.locations,
                                                session.add_live_locations)
        except Exception:
            bot.send_message(chat_id, 'Exception - updater не смог прислать информацию об АПе')
        if session.channel_name and session.use_channel:
            session.sectors_message_id = send_unclosed_sectors_to_channel(loaded_level, session.sectors_to_close, bot,
                                                                          session.channel_name)
        try:
            session.help_statuses = fill_help_statuses(loaded_helps, session.help_statuses)
            session.bonus_statuses = fill_bonus_statuses(loaded_bonuses, session.game_answered_bonus_ids,
                                                         session.bonus_statuses)
            session.sector_statuses = fill_sector_statuses(loaded_sectors, session.sector_statuses)
            session.message_statuses = fill_message_statuses(loaded_messages, session.message_statuses, session.sent_messages)
        except Exception:
            bot.send_message(chat_id, 'Exception - updater не смог заполнить статусы элементов')
        session.put_updater_task = True
        return

    if loaded_level['LevelId'] != session.current_level['LevelId']:
        session.current_level = loaded_level
        session.help_statuses, session.bonus_statuses, session.time_to_up_sent, session.sector_statuses, \
                                                                        session.message_statuses = reset_level_vars()
        try:
            reset_live_locations(chat_id, bot, session)
        except Exception:
            bot.send_message(chat_id, 'Exception - updater не смог сбросить информацию о live location')
        try:
            session.sectors_to_close = send_up_info(loaded_level, len(levels), loaded_helps, loaded_bonuses, bot, chat_id,
                                                    session.channel_name, session.use_channel, session.locations,
                                                    session.add_live_locations)
        except Exception:
            bot.send_message(chat_id, 'Exception - updater не смог прислать информацию об АПе')
        if session.channel_name and session.use_channel:
            session.sectors_message_id = send_unclosed_sectors_to_channel(loaded_level, session.sectors_to_close, bot,
                                                                          session.channel_name)
        try:
            session.help_statuses = fill_help_statuses(loaded_helps, session.help_statuses)
            session.bonus_statuses = fill_bonus_statuses(loaded_bonuses, session.game_answered_bonus_ids,
                                                         session.bonus_statuses)
            session.sector_statuses = fill_sector_statuses(loaded_sectors, session.sector_statuses)
            session.message_statuses = fill_message_statuses(loaded_messages, session.message_statuses, session.sent_messages)
        except Exception:
            bot.send_message(chat_id, 'Exception - updater не смог заполнить статусы элементов')
        session.put_updater_task = True
        return

    session.current_level = loaded_level

    try:
        if not loaded_level['Timeout'] == 0 and not session.time_to_up_sent\
                and loaded_level['TimeoutSecondsRemain'] <= 300:
            message = 'До автоперехода < 5 мин'
            bot.send_message(chat_id, message)
            session.time_to_up_sent = True
    except Exception:
        bot.send_message(chat_id, 'Exception - updater не смог проанализировать время до автоперехода')

    try:
        if loaded_messages:
            message_parcer(loaded_messages, session.message_statuses, session.sent_messages, bot, chat_id,
                           session.channel_name, session.use_channel, locations=session.locations, add_live_locations=session.add_live_locations)

        if loaded_sectors:
            codes_to_find = loaded_level['SectorsLeftToClose']
            sectors_parcer(loaded_sectors, codes_to_find, session.sector_statuses, bot, chat_id)

        if loaded_helps:
            help_parcer(loaded_helps, session.help_statuses, bot, chat_id, session.channel_name, session.use_channel,
                        locations=session.locations, add_live_locations=session.add_live_locations)

        if loaded_bonuses:
            bonus_parcer(loaded_bonuses, session.bonus_statuses, session.game_answered_bonus_ids, bot, chat_id,
                         locations=session.locations, add_live_locations=session.add_live_locations)

        if session.channel_name and session.use_channel and session.sectors_to_close and session.sectors_to_close != '1'\
                and session.sectors_message_id:
            session.sectors_to_close = channel_sectors_editor(loaded_level, session.sectors_to_close,
                                                              bot, session.channel_name, session.sectors_message_id)
        levels_parcer(levels, session, bot, chat_id)
    except Exception:
        bot.send_message(chat_id, 'Exception - не удалось выполнить слежение')

    session.put_updater_task = True


def storm_updater(chat_id, bot, session):
    if not session.storm_levels:
        for i in xrange(2):
            try:
                game_model = get_current_game_model(session, bot, chat_id, from_updater=True)
                levels = game_model['Levels']
                session.storm_levels = get_storm_levels(len(levels), session, bot, chat_id, from_updater=True)
                break
            except Exception:
                if i == 0:
                    continue
                bot.send_message(chat_id, 'Exception - updater не смог загрузить уровень(-вни)')
        session.put_updater_task = True
        return

    try:
        if not session.help_statuses or not session.bonus_statuses or not session.sector_statuses or not session.message_statuses:
            fill_all_statuses_storm(session, bot, chat_id)

        for level in session.storm_levels:
            if session.stop_updater:
                session.put_updater_task = True
                return
            if level['IsPassed'] or level['Dismissed']:
                continue
            loaded_storm_level = get_storm_level(level['Number'], session, bot, chat_id, from_updater=True)
            if not loaded_storm_level:
                continue

            loaded_helps = loaded_storm_level['Helps']
            loaded_bonuses = loaded_storm_level['Bonuses']
            loaded_sectors = loaded_storm_level['Sectors']
            loaded_messages = loaded_storm_level['Messages']

            session.storm_levels[level['Number']-1] = loaded_storm_level
            levelmark = '<b>Уровень %s: %s</b>' % (str(loaded_storm_level['Number']), loaded_storm_level['Name'].encode('utf-8')) \
                if loaded_storm_level['Name'] else '<b>Уровень %s</b>' % str(loaded_storm_level['Number'])

            if loaded_messages:
                message_parcer(loaded_messages, session.message_statuses, session.sent_messages, bot, chat_id,
                               session.channel_name, session.use_channel, levelmark=levelmark, storm=True)

            if loaded_sectors:
                codes_to_find = loaded_storm_level['SectorsLeftToClose']
                sectors_parcer(loaded_sectors, codes_to_find,
                               session.sector_statuses[loaded_storm_level['LevelId']], bot, chat_id,
                               levelmark=levelmark, storm=True)

            if loaded_helps:
                help_parcer(loaded_helps, session.help_statuses[loaded_storm_level['LevelId']],
                            bot, chat_id, session.channel_name, session.use_channel, levelmark=levelmark, storm=True)

            if loaded_bonuses:
                bonus_parcer(loaded_bonuses, session.bonus_statuses[loaded_storm_level['LevelId']],
                             session.game_answered_bonus_ids, bot, chat_id, levelmark=levelmark, storm=True)
    except Exception:
        bot.send_message(chat_id, 'Exception - не удалось выполнить команду updater до конца')

    session.put_updater_task = True


def reset_level_vars():
    help_statuses = dict()
    bonus_statuses = dict()
    answer_statuses = dict()
    message_statuses = dict()
    time_to_up_sent = False
    return help_statuses, bonus_statuses, time_to_up_sent, answer_statuses, message_statuses


def reset_live_locations(chat_id, bot, session):
    session.locations = dict()
    if session.live_location_message_ids:
        for k, v in session.live_location_message_ids.items():
            if k == 0:
                try:
                    bot.stop_message_live_location(chat_id, v)
                except Exception as e:
                    response_text = json.loads(e.result.text)['description'].encode('utf-8')
                    if "message can\\'t be edited" in response_text:
                        del session.session.live_location_message_ids[k]
            elif k > 10:
                continue
            else:
                try:
                    coord_bots[k].stop_message_live_location(chat_id, v)
                except Exception as e:
                    response_text = json.loads(e.result.text)['description'].encode('utf-8')
                    if "message can\\'t be edited" in response_text:
                        del session.session.live_location_message_ids[k]
        session.live_location_message_ids = dict()


def send_up_info(loaded_level, number_of_levels, loaded_helps, loaded_bonuses, bot, chat_id, channel_name, use_channel,
                 locations, add_live_locations, block=''):
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

    send_task(loaded_level, bot, chat_id, locations=locations, add_live_locations=add_live_locations)

    try:
        if channel_name and use_channel:
            bot.send_message(channel_name, up_message, parse_mode='HTML')
            send_task(loaded_level, bot, channel_name)
    except Exception:
        bot.send_message(chat_id, 'Exception - updater не смог отправить информацию по новому уровню в канал')

    try:
        sectors_to_close = get_sectors_to_close(loaded_level['Sectors'], get_sector_names=True)
    except Exception:
        bot.send_message(chat_id, 'Exception - updater не смог составить список секторов')
        sectors_to_close = 'Exception - updater не смог составить список секторов'

    return sectors_to_close


def send_unclosed_sectors_to_channel(loaded_level, sectors_to_close, bot, channel_name):
    try:
        codes_all = 1 if not loaded_level['Sectors'] else len(loaded_level['Sectors'])
        codes_to_find = 1 if not loaded_level['Sectors'] else loaded_level['SectorsLeftToClose']
        message = '<b>Осталось закрыть: %s из %s:</b>\r\n%s' % (str(codes_to_find), str(codes_all), sectors_to_close)
        response = bot.send_message(channel_name, message, parse_mode='HTML')
    except Exception:
        response = bot.send_message(channel_name, 'Exception - updater не смог прислать не закрытые сектора')
    return response.message_id


def fill_help_statuses(loaded_helps, help_statuses):
    if loaded_helps:
        for help in loaded_helps:
            help_statuses[help['HelpId']] = {'not_sent': True, 'time_not_sent': True}
        return help_statuses


def fill_bonus_statuses(loaded_bonuses, game_answered_bonus_ids, bonus_statuses):
    if loaded_bonuses:
        for bonus in loaded_bonuses:
            bonus_statuses[bonus['BonusId']] = {'info_not_sent': True, 'award_not_sent': True}\
                if not bonus['BonusId'] in game_answered_bonus_ids else {'info_not_sent': False, 'award_not_sent': False}
        return bonus_statuses


def fill_sector_statuses(loaded_sectors, sector_statuses):
    if loaded_sectors:
        for sector in loaded_sectors:
            sector_statuses[sector['SectorId']] = {'answer_info_not_sent': True}
    return sector_statuses


def fill_message_statuses(loaded_messages, message_statuses, sent_messages):
    if loaded_messages:
        for message in loaded_messages:
            message_statuses[message['MessageId']] = {'message_not_sent': True} \
                if not message['MessageId'] in sent_messages else {'message_not_sent': False}
    return message_statuses


def sectors_parcer(loaded_sectors, codes_to_find, sector_statuses, bot, chat_id, levelmark=None, storm=False):
    if loaded_sectors:
        for sector in loaded_sectors:
            if not sector['SectorId'] in sector_statuses.keys():
                sector_statuses[sector['SectorId']] = {'answer_info_not_sent': True}

            if sector['IsAnswered'] and sector_statuses[sector['SectorId']]['answer_info_not_sent']:

                code = sector['Answer']['Answer'].encode('utf-8')
                player = sector['Answer']['Login'].encode('utf-8')
                name = sector['Name'].encode('utf-8')
                codes_all = len(loaded_sectors)
                sectors_to_close = get_sectors_to_close(loaded_sectors)
                message = '<b>с-р: ' + name + ' - </b>' + '\xE2\x9C\x85' + '<b> (' + player + ': ' + code + ')</b>' \
                          '\r\nОсталось закрыть: %s из %s:\r\n%s' % (str(codes_to_find), str(codes_all),
                                                                     sectors_to_close)
                if storm:
                    message = levelmark + '\r\n' + message
                bot.send_message(chat_id, message, parse_mode='HTML')
                sector_statuses[sector['SectorId']]['answer_info_not_sent'] = False


def help_parcer(loaded_helps, help_statuses, bot, chat_id, channel_name, use_channel, levelmark=None, storm=False,
                locations=None, add_live_locations=False):
    if loaded_helps:
        for help in loaded_helps:
            if not help['HelpId'] in help_statuses.keys():
                help_statuses[help['HelpId']] = {'not_sent': True, 'time_not_sent': True}

            if help_statuses[help['HelpId']]['not_sent'] and help['HelpText'] is not None:
                help_statuses[help['HelpId']]['not_sent'] = False
                help_statuses[help['HelpId']]['time_not_sent'] = False
                send_help(help, bot, chat_id, levelmark, storm, locations=locations, add_live_locations=add_live_locations)
                if channel_name and use_channel:
                    send_help(help, bot, channel_name, levelmark, storm)
                continue
            if help_statuses[help['HelpId']]['time_not_sent'] and help['RemainSeconds'] <= 180:
                help_statuses[help['HelpId']]['time_not_sent'] = False
                send_time_to_help(help, bot, chat_id, levelmark, storm)


def bonus_parcer(loaded_bonuses, bonus_statuses, game_answered_bonus_ids, bot, chat_id, levelmark=None, storm=False,
                 locations=None, add_live_locations=False):
    if loaded_bonuses:

        for bonus in loaded_bonuses:
            if not bonus['BonusId'] in bonus_statuses.keys():
                bonus_statuses[bonus['BonusId']] = {'info_not_sent': True, 'award_not_sent': True}

            if bonus['IsAnswered'] and bonus_statuses[bonus['BonusId']]['award_not_sent']:
                bonus_statuses[bonus['BonusId']]['award_not_sent'] = False
                bonus_statuses[bonus['BonusId']]['info_not_sent'] = False
                game_answered_bonus_ids.append(bonus['BonusId'])
                send_bonus_award_answer(bonus, bot, chat_id, levelmark, storm, locations=locations, add_live_locations=add_live_locations)
                continue
            if bonus_statuses[bonus['BonusId']]['info_not_sent'] and bonus['Task'] and not bonus['Expired']:
                bonus_statuses[bonus['BonusId']]['info_not_sent'] = False
                send_bonus_info(bonus, bot, chat_id, levelmark, storm, locations=locations, add_live_locations=add_live_locations)


def message_parcer(loaded_messages, message_statuses, sent_messages, bot, chat_id, channel_name, use_channel,
                   levelmark=None, storm=False, locations=None, add_live_locations=False):
    if loaded_messages:
        for message in loaded_messages:
            if not message['MessageId'] in message_statuses.keys():
                message_statuses[message['MessageId']] = {'message_not_sent': True}

            if message_statuses[message['MessageId']]['message_not_sent']:
                message_statuses[message['MessageId']]['message_not_sent'] = False
                sent_messages.append(message['MessageId'])
                send_adm_message(message, bot, chat_id, levelmark, storm, locations=locations, add_live_locations=add_live_locations)
                if channel_name and use_channel:
                    send_adm_message(message, bot, channel_name, levelmark, storm)


def levels_parcer(levels, session, bot, chat_id):
    for level in levels:
        if level['Dismissed'] and level['LevelId'] not in session.dismissed_level_ids:
            text = '\xE2\x9D\x97 <b>Уровень %s, "%s" - снят</b> \xE2\x9D\x97' % (str(level['LevelNumber']),
                                                                                 level['LevelName'].encode('utf-8')) \
                if level['LevelName'] else '\xE2\x9D\x97 <b>Уровень %s - снят</b> \xE2\x9D\x97' % str(level['LevelNumber'])
            bot.send_message(chat_id, text, parse_mode='HTML')
            session.dismissed_level_ids.append(level['LevelId'])
        if not level['Dismissed'] and level['LevelId'] in session.dismissed_level_ids:
            text = '\xE2\x9D\x97 <b>Уровень %s, "%s" - возвращен</b> \xE2\x9D\x97' % (str(level['LevelNumber']), level['LevelName'].encode('utf-8')) \
                if level['LevelName'] else '\xE2\x9D\x97 <b>Уровень %s - возвращен</b> \xE2\x9D\x97' % str(level['LevelNumber'])
            bot.send_message(chat_id, text, parse_mode='HTML')
            session.dismissed_level_ids.remove(level['LevelId'])


def channel_sectors_editor(loaded_level, old_sectors_to_close, bot, channel_name, message_id):
    new_sectors_to_close = get_sectors_to_close(loaded_level['Sectors'], get_sector_names=True)
    if new_sectors_to_close != old_sectors_to_close:
        codes_all = 1 if not loaded_level['Sectors'] else len(loaded_level['Sectors'])
        codes_to_find = 1 if not loaded_level['Sectors'] else loaded_level['SectorsLeftToClose']
        message = '<b>Осталось закрыть: %s из %s:</b>\r\n%s' % \
                  (str(codes_to_find), str(codes_all), new_sectors_to_close)
        bot.edit_message_text(message, channel_name, message_id, parse_mode='HTML')

    return new_sectors_to_close


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


def fill_all_statuses_storm(session, bot, chat_id):
    if not session.help_statuses:
        for level in session.storm_levels:
            if session.stop_updater:
                return
            loaded_storm_level = get_storm_level(level['Number'], session, bot, chat_id, from_updater=True)
            if not loaded_storm_level:
                continue
            session.help_statuses[loaded_storm_level['LevelId']] = loaded_storm_level['help_statuses'] = dict()
            session.help_statuses[loaded_storm_level['LevelId']] = \
                fill_help_statuses(loaded_storm_level['Helps'], session.help_statuses[loaded_storm_level['LevelId']]) \
                    if loaded_storm_level['Helps'] else dict()

    if not session.bonus_statuses:
        for level in session.storm_levels:
            if session.stop_updater:
                return
            loaded_storm_level = get_storm_level(level['Number'], session, bot, chat_id, from_updater=True)
            if not loaded_storm_level:
                continue
            session.bonus_statuses[loaded_storm_level['LevelId']] = loaded_storm_level['bonus_statuses'] = dict()
            session.bonus_statuses[loaded_storm_level['LevelId']] = \
                fill_bonus_statuses(loaded_storm_level['Bonuses'], session.game_answered_bonus_ids,
                                    session.bonus_statuses[loaded_storm_level['LevelId']]) if loaded_storm_level['Bonuses'] else dict()

    if not session.sector_statuses:
        for level in session.storm_levels:
            if session.stop_updater:
                return
            loaded_storm_level = get_storm_level(level['Number'], session, bot, chat_id, from_updater=True)
            if not loaded_storm_level:
                continue
            session.sector_statuses[loaded_storm_level['LevelId']] = loaded_storm_level['sector_statuses'] = dict()
            session.sector_statuses[loaded_storm_level['LevelId']] = \
                fill_sector_statuses(loaded_storm_level['Sectors'],
                                     session.sector_statuses[loaded_storm_level['LevelId']]) if loaded_storm_level['Sectors'] else dict()

    if not session.message_statuses:
        for level in session.storm_levels:
            if session.stop_updater:
                return
            loaded_storm_level = get_storm_level(level['Number'], session, bot, chat_id, from_updater=True)
            if not loaded_storm_level:
                continue
            session.message_statuses[loaded_storm_level['LevelId']] = loaded_storm_level['message_statuses'] = dict()
            session.message_statuses[loaded_storm_level['LevelId']] = \
                fill_message_statuses(loaded_storm_level['Messages'],
                                      session.message_statuses[loaded_storm_level['LevelId']], session.sent_messages)
