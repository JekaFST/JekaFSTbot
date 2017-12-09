# -*- coding: utf-8 -*-
import telebot

tags_list = ['font', 'p', 'div', 'span', 'td', 'tr', 'table', 'hr', 'object', 'param', 'audio', 'source', 'embed']

game_wrong_statuses = {
                2: 'Игра с указанным ID не существует',
                3: 'Запрошенная игра не соответствует запрошенному Engine',
                4: 'Логин не удался',
                5: 'Игра еще не началась',
                6: 'Игра закончилась',
                7: 'Не подана заявка (игроком)',
                8: 'Не подана заявка (командой)',
                9: 'Игрок еще не принят в игру',
                10: 'У игрока нет команды (в командной игре)',
                11: 'Игрок не активен в команде (в командной игре)',
                12: 'В игре нет уровней',
                13: 'Превышено количество участников в команде (в командной игре)',
                16: 'Уровень снят',
                17: 'Игра закончена',
                18: 'Уровень снят',
                19: 'Уровень пройден автопереходом',
                20: 'Все сектора отгаданы',
                21: 'Уровень снят',
                22: 'Таймаут уровня'
                }

coord_bots = {
    1: telebot.TeleBot('460875098:AAELtUs4hS3E9k1ZsOMHUJ9-9SFeNAzcSSM'),
    2: telebot.TeleBot('476666700:AAHa2938k_9H_nrwDnJ9F0PqLIOmwxAnMsM'),
    3: telebot.TeleBot('502067022:AAF5X_7yhoeDRWz2_g6WEhZx7sns9XoLQbc'),
    4: telebot.TeleBot('455710359:AAFb30ylsISV_zzV3UYtZuuOxUjCMILRojY'),
    5: telebot.TeleBot('433979521:AAG5lyqy5jFBiOH4xAS0WPIGe3Q-wydFeEY'),
    6: telebot.TeleBot('474004206:AAGuTE_mRxkowxxe0kV-cPOo9qErm6Nejt4'),
    7: telebot.TeleBot('398767427:AAFc6rjiv6ONgF__xX1uwzxsF36JScFER_c'),
    8: telebot.TeleBot('407075101:AAGHKuzITtLG8d6oAIYLmFXqPun0r93knAk'),
    9: telebot.TeleBot('445012402:AAH5hFl4LqcPcO-lgJf7qAoIanovj4Maxvg'),
    10: telebot.TeleBot('492949542:AAFytmZDVOFtl79mqUlKrQAVePUfzI_if5U'),
    11: telebot.TeleBot(''),
    12: telebot.TeleBot(''),
    13: telebot.TeleBot(''),
    14: telebot.TeleBot(''),
    15: telebot.TeleBot(''),
    16: telebot.TeleBot(''),
    17: telebot.TeleBot(''),
    18: telebot.TeleBot(''),
    19: telebot.TeleBot(''),
    20: telebot.TeleBot('')
}

# game_repeat_statuses = [16, 18, 19, 20, 21, 22]
