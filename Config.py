# -*- coding: utf-8 -*-
game_url_ending = '/gameengines/encounter/play/'
login_url_ending = '/Login.aspx'
json = '?json=1'
config_url = 'http://localhost:443/config'
urls_url = 'http://localhost:443/urls'
current_game_model_url = 'http://localhost:443/game_model_current'
code_request = {
                'LevelId': '',
                'LevelNumber': '',
                'LevelAction.Answer': ''
                }

# init_config_dict = {
#                     'bot_token': '370362982:AAH5ojKT0LSw8jS-vLfDF1bDE8rWWDyTeso',
#                     'en_domain': '',
#                     'game_url_ending': '/gameengines/encounter/play/',
#                     'login_url_ending': '/Login.aspx',
#                     'json': '?json=1',
#                     'Login': 'jekafst_bot',
#                     'Password': 'jekabot_1412',
#                     'game_id': '',
#                     'cookie': '',
#                     'code_request': {
#                                         'LevelId': '',
#                                         'LevelNumber': '',
#                                         'LevelAction.Answer': ''
#                                     }
#                    }

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

# game_repeat_statuses = [16, 18, 19, 20, 21, 22]
