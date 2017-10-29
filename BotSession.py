# -*- coding: utf-8 -*-
class BotSession(object):
    def __init__(self):
        self.stop_updater = None
        self.use_channel = False
        # self.channel_name = '@fst_channel'
        self.channel_name = '@nnm_channel'
        self.active = False
        self.config = {
                    'game_url_ending': '/gameengines/encounter/play/',
                    'login_url_ending': '/Login.aspx',
                    'json': '?json=1',
                    # 'Login': 'prinncessa',
                    # 'Password': 'h323232z',
                    'Login': 'jekafst_bot',
                    'Password': 'jekabot_1412',
                    'code_request': {},
                    'en_domain': 'http://demo.en.cx',
                    'game_id': '26991'
                   }
        self.current_level = None
        self.urls = dict()
        self.number_of_levels = None
        self.game_answered_bonus_ids = list()
        self.help_statuses = dict()
        self.bonus_statuses = dict()
        self.sector_statuses = dict()
        self.message_statuses = dict()
        self.sent_messages = list()
        self.time_to_up_sent = None
        self.sectors_to_close = None
        self.sectors_message_id = None
        self.game_model_status = None
        self.delay = 2
        self.send_coords_active = True
        self.current_game_model = None
        self.put_updater_task = None
        self.send_codes = True
