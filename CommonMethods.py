# -*- coding: utf-8 -*-
import datetime as datetime
from TextConvertingMethods import send_object_text


def time_converter(seconds):
    time = str(datetime.timedelta(seconds=seconds))
    h_m_s = time[2:4] + ':' + time[5:] if seconds < 3600 else time[:1] + ':' + time[2:4] + ':' + time[5:]
    return h_m_s


def send_task(loaded_level, bot, chat_id):
    tasks = loaded_level['Tasks']
    if tasks:
        task = tasks[0]['TaskText'].encode('utf-8')
        task_header = '<b>ЗАДАНИЕ</b>'
        send_object_text(task, task_header, bot, chat_id)
    else:
        bot.send_message(chat_id, 'Задание не предусмотрено')


def send_help(help, bot, chat_id):
    help_number = str(help['Number'])
    help_text = help['HelpText'].encode('utf-8')
    help_header = '<b>Подсказка ' + help_number + '</b>'
    send_object_text(help_text, help_header, bot, chat_id)


def send_time_to_help(help, bot, chat_id):
    help_number = str(help['Number'])
    time_to_help = time_converter(help['RemainSeconds'])
    message_text = '<b>Подсказка ' + help_number + '</b>\r\nпридет через %s' % time_to_help
    bot.send_message(chat_id, message_text, parse_mode='HTML')


def send_bonus_info(bonus, bot, chat_id):
    bonus_name = "<b>б-с " + str(bonus['Number']) + ': ' + bonus['Name'].encode('utf-8') + '</b>' if bonus['Name'] \
        else "<b>Бонус " + str(bonus['Number']) + '</b>'
    if bonus['Expired']:
        send_object_text('Время истекло', bonus_name, bot, chat_id)
        return
    bonus_task = 'Задание:\r\n' + bonus['Task'].encode('utf-8') if bonus['Task'] else 'Бонус без задания'
    bonus_left_time = '\r\nОсталось %s' % time_converter(bonus['SecondsLeft']) if bonus['SecondsLeft'] else ''
    send_object_text(bonus_task + bonus_left_time, bonus_name, bot, chat_id)


def send_bonus_award_answer(bonus, bot, chat_id):
    bonus_name = "<b>б-с " + str(bonus['Number']) + ': ' + bonus['Name'].encode('utf-8') if bonus['Name'] \
        else "<b>Бонус " + str(bonus['Number'])
    code = bonus['Answer']['Answer'].encode('utf-8')
    player = bonus['Answer']['Login'].encode('utf-8')
    bonus_award_header = bonus_name + ' - </b>' + '\xE2\x9C\x85' + '<b> (' + player + ': ' + code + ')</b>'
    bonus_help = 'Подсказка:\r\n' + bonus['Help'].encode('utf-8') if bonus['Help'] else 'Без подсказки'
    bonus_award = '\r\n<b>Награда: ' + time_converter(bonus['AwardTime']) + '</b>' if bonus['AwardTime'] != 0 \
        else '\n<b>Без награды</b>'
    bonus_award_text = bonus_help + bonus_award
    send_object_text(bonus_award_text, bonus_award_header, bot, chat_id)
