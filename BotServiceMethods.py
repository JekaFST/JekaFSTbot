# -*- coding: utf-8 -*-
import json
import logging
import requests
from DBMethods import DBSession, DB


def add_level_sectors(levels_dict, sectors_lines):
    for line in sectors_lines:
        level_number = line['number']
        level_name = line['levelname'].decode('utf-8')
        if not level_number in levels_dict.keys():
            levels_dict[level_number] = {
                'number': level_number,
                'name': level_name,
                'sectors': list(),
                'bonuses': list()
            }
        levels_dict[level_number]['sectors'].append({
            'order': line['sectororder'],
            'name': line['sectorname'].decode('utf-8'),
            'code': line['code'].decode('utf-8') if line['code'] else '???',
            'player': line['player'].decode('utf-8') if line['player'] else ''
        })
    return levels_dict


def add_level_bonuses(levels_dict, bonus_lines):
    for line in bonus_lines:
        level_number = line['number']
        level_name = line['levelname'].decode('utf-8')
        if not level_number in levels_dict.keys():
            levels_dict[level_number] = {
                'number': level_number,
                'name': level_name,
                'sectors': list(),
                'bonuses': list()
            }
        levels_dict[level_number]['bonuses'].append({
            'number': line['bonusnumber'],
            'name': line['bonusname'].decode('utf-8'),
            'code': line['code'].decode('utf-8') if line['code'] else '???',
            'player': line['player'].decode('utf-8') if line['player'] else ''
        })
    return levels_dict


def run_db_cleanup(bot):
    urls_levels = DB.get_gameurls_levels()
    elements_cleanup(urls_levels, 'levels')
    urls_bonuses = DB.get_gameurls_bonuses()
    elements_cleanup(urls_bonuses, 'bonuses')
    urls_sectors = DB.get_gameurls_sectors()
    elements_cleanup(urls_sectors, 'sectors')
    urls_helps = DB.get_gameurls_helps()
    elements_cleanup(urls_helps, 'helps')
    urls_messages = DB.get_gameurls_messages()
    elements_cleanup(urls_messages, 'messages')
    bot.send_message(45839899, 'db_cleanup выполнен')
    return


def elements_cleanup(urls, elements):
    for line in urls:
        try:
            response = requests.post(line['loginurl'], data={'Login': 'JekaFST', 'Password': 'hjccbz1412'},
                                     headers={'Cookie': 'lang=ru'})
            cookie = response.request.headers['Cookie']
            response = requests.get(line['gameurljs'], headers={'Cookie': cookie})
            game_model = json.loads(response.text)
            if game_model['Event'] == 17:
                DBSession.drop_session_vars(line['sessionid'])
                DB.cleanup_for_ended_game(line['sessionid'], line['gameid'])
        except Exception:
            logging.exception("Не удалось выполнить %s clenup" % elements)
