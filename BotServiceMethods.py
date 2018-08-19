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
    logging.log(logging.INFO, "DB cleanup is launched")
    try:
        urls_messages = DB.get_gameurls_messages()
        logging.log(logging.INFO, "urls_messages got")
        logging.log(logging.INFO, '%s' % str(urls_messages))
        elements_cleanup(urls_messages, 'messages')
        logging.log(logging.INFO, "After messages cleanup started")

        urls_levels = DB.get_gameurls_levels()
        logging.log(logging.INFO, "urls_levels got")
        logging.log(logging.INFO, '%s' % str(urls_levels))
        elements_cleanup(urls_levels, 'levels')
        logging.log(logging.INFO, "After levels cleanup started")

        urls_helps = DB.get_gameurls_helps()
        logging.log(logging.INFO, "urls_helps got")
        logging.log(logging.INFO, '%s' % str(urls_helps))
        elements_cleanup(urls_helps, 'helps')
        logging.log(logging.INFO, "After helps cleanup started")

        urls_bonuses = DB.get_gameurls_bonuses()
        logging.log(logging.INFO, "urls_bonuses got")
        logging.log(logging.INFO, '%s' % str(urls_bonuses))
        elements_cleanup(urls_bonuses, 'bonuses')
        logging.log(logging.INFO, "After bonuss cleanup started")

        urls_sectors = DB.get_gameurls_sectors()
        logging.log(logging.INFO, "urls_sectors got")
        logging.log(logging.INFO, '%s' % (urls_sectors))
        elements_cleanup(urls_sectors, 'sectors')
        logging.log(logging.INFO, "After sectors cleanup started")

        bot.send_message(45839899, 'db_cleanup выполнен')
    except Exception:
        logging.exception("Exception during DB cleanup")
    logging.log(logging.INFO, "DB cleanup is finished")
    return


def elements_cleanup(urls, elements):
    for line in urls:
        try:
            response = requests.post(line['loginurl'], data={'Login': 'JekaFST', 'Password': 'hjccbz1412'},
                                     headers={'Cookie': 'lang=ru'})
            cookie = response.request.headers['Cookie']
            response = requests.get(line['gameurljs'], headers={'Cookie': cookie})
            game_model = json.loads(response.text)
            print str(game_model['Event'])
            if game_model['Event'] in [6, 17]:
                DBSession.drop_session_vars(line['sessionid'])
                DB.cleanup_for_ended_game(line['sessionid'], line['gameid'])
        except Exception:
            logging.exception("Не удалось выполнить %s clenup" % elements)
