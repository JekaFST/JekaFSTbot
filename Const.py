# -*- coding: utf-8 -*-
import os


prod = True if 'DYNO' in os.environ.keys() else False
num_worker_threads = 10

urls = {
    'game_url_ending': '/gameengines/encounter/play/',
    'login_url_ending': '/Login.aspx',
}

obj_type_url_mapping = {
    'help': '/Administration/Games/PromptEdit.aspx',
    'pen_help': '/Administration/Games/PromptEdit.aspx',
    'bonus': '/Administration/Games/BonusEdit.aspx',
    'sector': '/Administration/Games/LevelEditor.aspx',
    'level': '/Administration/Games/LevelEditor.aspx',
    'task': '/Administration/Games/TaskEdit.aspx',
    'level_name': '/Administration/Games/NameCommentEdit.aspx',
    'level_timeout': '/ALoader/LevelInfo.aspx',
}

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

helptext = 'Коды сдавать в виде !код или ! код или .код или . код\n' \
           'Сдавать коды в бонусное окно в виде ?код или ? код\n' \
           '/task - прислать задание\n' \
           '/task_images - прислать все картинки из задания\n' \
           '/sectors - прислать список секторов\n' \
           '/hints - прислать все подсказки\n' \
           '/last_hint - прислать последнюю пришедшую подсказку\n' \
           '/bonuses - прислать бонусы\n' \
           '/unclosed_bonuses - прислать не закрытые бонусы цифрой\n' \
           '/messages - прислать сообщения авторов\n' \
           '/start_updater - запустить слежение за обновлениями\n' \
           '/stop_updater - остановить слежение за обновлениями\n' \
           '/set_channel_name - задать имя канала для репостинга (через пробел)\n' \
           '/start_channel - запустить постинг в канал\n' \
           '/stop_channel - остановить постинг в канал\n' \
           '/start_session - запустить сессию ' \
           '(активировать выполнение команд из чата, сдачу кодов)\n' \
           '/stop_session - остановить сессию ' \
           '(остановить выполнение команд из чата, сдачу кодов, слежение и постинг в канал)\n' \
           '/config - прислать конфигурацию,\n' \
           '/join - включить работу с ботом через личный чат\n' \
           '/reset_join - выключить работу с ботом через личный чат\n' \
           '/ask_for_permission - отправить запрос на разрешение использования бота\n' \
           '/codes_off - выключить отправку кодов в движок\n' \
           '/codes_on - включить отправку кодов в движок\n' \
           '/get_codes_links - получить ссылки для просмотра сданных кодов\n' \
           '/kml - получить kml файл с пронумерованными точками по координатам уровня\n' \
           '/send_ll s3600 - отправить live locations из уровня\n' \
           'где s3600 - длительность в секундах\n' \
           'если длительность не задана - по умолчанию - 3 часа\n' \
           'для отправки одной live location из чата с меткой основного бота:\n' \
           '/send_ll s3600 корды, где s3600 - длительность в секундах\n' \
           'если длительность не задана - по умолчанию - 3 часа\n' \
           '/edit_ll - отредактировать live location (пробел-номер точки-пробел-новые координаты)\n' \
           '/stop_ll - остановить live locations (пробел-номер точки, чтобы остановить конкретный location)\n' \
           '/add_points_ll - отправить live locations из чата. Формат:\n' \
           '/add_points_ll s3600\n' \
           '1 - корды\n2 - корды\n...\nn - корды\n' \
           'где s3600 - длительность в секундах\n' \
           'если длительность не задана - по умолчанию - 3 часа\n' \
           'при штурмовой игре поддерживается сдача кодов:\n' \
           '!номер уровня!код или .номер уровня.код | ?номер уровня?код\n' \
           'и следующие команды:\n' \
           '/task, /sectors, /hints, /last_hint, /bonuses, /unclosed_bonuses, /messages\n' \
           'номер штурмового уровня вводится после команды, через пробел\n' \
           '/instruction - получить ссылку на инструкцию'
