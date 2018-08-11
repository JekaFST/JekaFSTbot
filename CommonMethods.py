# -*- coding: utf-8 -*-
import json
import datetime as datetime
import telebot
from DBMethods import DB, DBSession
from TextConvertingMethods import send_object_text


def time_converter(seconds):
    time = str(datetime.timedelta(seconds=seconds))
    h_m_s = time[2:4] + ':' + time[5:] if seconds < 3600 else time[:1] + ':' + time[2:4] + ':' + time[5:]
    return h_m_s


def send_task(session_id, loaded_level, bot, chat_id, from_updater=False, storm=False):
    tasks = loaded_level['Tasks']
    if tasks:
        task = tasks[0]['TaskText'].encode('utf-8')
        task_header = '<b>ЗАДАНИЕ</b>'
        send_object_text(task, task_header, bot, chat_id, session_id, from_updater, storm)
    else:
        bot.send_message(chat_id, 'Задание не предусмотрено')


def send_help(help, bot, chat_id, session_id, from_updater=False, storm=False, levelmark=None):
    help_number = str(help['Number'])
    help_text = help['HelpText'].encode('utf-8')
    help_header = '<b>Подсказка ' + help_number + '</b>' if not storm else levelmark + '\r\n<b>Подсказка ' + help_number + '</b>'
    send_object_text(help_text, help_header, bot, chat_id, session_id, from_updater, storm)


def send_time_to_help(help, bot, chat_id, levelmark=None, storm=False):
    help_number = str(help['Number'])
    time_to_help = time_converter(help['RemainSeconds'])
    message_text = '<b>Подсказка ' + help_number + '</b>\r\nпридет через %s' % time_to_help if not storm else \
        levelmark + '\r\n<b>Подсказка ' + help_number + '</b>\r\nпридет через %s' % time_to_help
    bot.send_message(chat_id, message_text, parse_mode='HTML')


def send_bonus_info(bonus, bot, chat_id, session_id, from_updater=False, storm=False, levelmark=None):
    bonus_name = "<b>б-с " + str(bonus['Number']) + ': ' + bonus['Name'].encode('utf-8') + '</b>' if bonus['Name'] \
        else "<b>Бонус " + str(bonus['Number']) + '</b>'
    if storm:
        bonus_name = levelmark + '\r\n' + bonus_name
    if bonus['Expired']:
        send_object_text('Время истекло', bonus_name, bot, chat_id)
        return
    bonus_task = 'Задание:\r\n' + bonus['Task'].encode('utf-8') if bonus['Task'] else 'Бонус без задания'
    bonus_left_time = '\r\nОсталось %s' % time_converter(bonus['SecondsLeft']) if bonus['SecondsLeft'] else ''
    send_object_text(bonus_task + bonus_left_time, bonus_name, bot, chat_id, session_id, from_updater, storm)


def send_bonus_award_answer(bonus, bot, chat_id, session_id, from_updater=False, storm=False, levelmark=None):
    bonus_name = "<b>б-с " + str(bonus['Number']) + ': ' + bonus['Name'].encode('utf-8') if bonus['Name'] \
        else "<b>Бонус " + str(bonus['Number'])
    code = bonus['Answer']['Answer'].encode('utf-8')
    player = bonus['Answer']['Login'].encode('utf-8')
    bonus_award_header = bonus_name + ' - </b>' + '\xE2\x9C\x85' + '<b> (' + player + ': ' + code + ')</b>'
    if storm:
        bonus_award_header = levelmark + '\r\n' + bonus_award_header
    bonus_help = 'Подсказка:\r\n' + bonus['Help'].encode('utf-8') if bonus['Help'] else 'Без подсказки'
    bonus_award = '\r\n<b>Награда: ' + time_converter(bonus['AwardTime']) + '</b>' if bonus['AwardTime'] != 0 \
        else '\n<b>Без награды</b>'
    bonus_award_text = bonus_help + bonus_award
    send_object_text(bonus_award_text, bonus_award_header, bot, chat_id, session_id, from_updater, storm)


def send_adm_message(message, bot, chat_id, session_id, from_updater=False, storm=False, levelmark=None):
    message_header = '<b>Сообщение от авторов</b>' if not storm else levelmark + '\r\n<b>Сообщение от авторов</b>'
    message_text = message['MessageText'].encode('utf-8')
    send_object_text(message_text, message_header, bot, chat_id, session_id, from_updater, storm)


def close_live_locations(chat_id, bot, session, ll_message_ids, point=None):
    if not point:
        for k, v in ll_message_ids.items():
            if int(k) == 0:
                try:
                    bot.stop_message_live_location(chat_id, int(v))
                except Exception as e:
                    response_text = json.loads(e.result.text)['description'].encode('utf-8')
                    if "message can't be edited" in response_text:
                        del ll_message_ids[k]
                bot.send_message(chat_id, 'Live location основного бота остановлена')
            elif int(k) > 20:
                continue
            else:
                try:
                    telebot.TeleBot(DB.get_location_bot_token_by_number(k)).stop_message_live_location(chat_id, int(v))
                except Exception as e:
                    response_text = json.loads(e.result.text)['description'].encode('utf-8')
                    if "message can't be edited" in response_text:
                        del ll_message_ids[k]
                bot.send_message(chat_id, 'Live location %s остановлена' % k)
        DBSession.update_json_field(session['sessionid'], 'llmessageids', {})
    else:
        if point in ll_message_ids.keys():
            try:
                telebot.TeleBot(DB.get_location_bot_token_by_number(point)).stop_message_live_location(chat_id, int(ll_message_ids[point]))
                del ll_message_ids[point]
            except Exception as e:
                response_text = json.loads(e.result.text)['description'].encode('utf-8')
                if "message can't be edited" in response_text:
                    del ll_message_ids[point]
            DBSession.update_json_field(session['sessionid'], 'llmessageids', ll_message_ids)
            bot.send_message(chat_id, 'Live location %s остановлена' % point)
        else:
            bot.send_message(chat_id, 'Live location %s не поставлен' % point)
