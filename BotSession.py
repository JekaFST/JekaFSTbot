# -*- coding: utf-8 -*-
class BotSession(object):
    def __init__(self):
        self.stop_updater = None  # cfg
        self.use_channel = False  # cfg
        self.channel_name = None  # cfg
        self.active = False  # cfg
        self.config = {
                        'game_url_ending': '/gameengines/encounter/play/',
                        'login_url_ending': '/Login.aspx',
                        'json': '?json=1',
                        'Login': '',
                        'Password': '',
                        'en_domain': '',
                        'game_id': '',
                        'cookie': ''
                    }                 # cfg
        self.current_level = None
        self.storm_levels = None
        self.urls = {
            'game_url': '',
            'game_url_js': '',
            'login_url': ''
        }                             # cfg
        self.game_answered_bonus_ids = list()  # per game
        self.help_statuses = dict()  # per level
        self.bonus_statuses = dict()  # per level
        self.sector_statuses = dict()  # per level
        self.message_statuses = dict()  # per level
        self.sent_messages = list()  # per game
        self.time_to_up_sent = None  # per level
        self.sectors_to_close = None  # per level for channel
        self.sectors_message_id = None  # per level for channel
        self.game_model_status = None  # cfg
        self.delay = 2  # cfg
        self.put_updater_task = None  # cfg
        self.send_codes = True  # cfg
        self.dismissed_level_ids = list()  # per game
        self.storm_game = False  # cfg
        self.locations = dict()  # per level
        self.live_location_message_ids = dict()  # separate
