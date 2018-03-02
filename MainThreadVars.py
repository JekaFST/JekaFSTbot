import telebot


test_config_dict = {
                    'channel_name': '',
                    'en_domain': 'http://demo.en.cx',
                    'Login': 'jekafst_bot',
                    'Password': 'jekabot_1412'
                  }


fst_config_dict = {
                    'channel_name': '@fst_channel',
                    'en_domain': 'http://deadline.en.cx',
                    'Login': 'jekafst_bot',
                    'Password': 'jekabot_1412'
                  }

nnm_config_dict = {
                    'channel_name': '@nnm_channel',
                    'en_domain': 'http://deadline.en.cx',
                    'Login': 'oneanotherbot',
                    'Password': 'ljcneg12'
                  }

rch_config_dict = {
                    'channel_name': '@r4channel',
                    'en_domain': 'http://deadline.en.cx',
                    'Login': 'oneanotherbot',
                    'Password': 'ljcneg12'
                  }

keks_config_dict = {
                    'channel_name': '',
                    'en_domain': 'http://felix.en.cx',
                    'Login': 'jekafst_bot',
                    'Password': 'jekabot_1412'
                  }


class MainVars(object):
    def __init__(self):
        self.allowed_chats = {
            45839899: fst_config_dict,
            -1001145974445: fst_config_dict,
            -1001062839624: nnm_config_dict,
            -1001126631174: rch_config_dict, #P4
            -1001076545820: fst_config_dict,
            -1001116652124: fst_config_dict,
            -169229164: None,
            -1001135150893: test_config_dict,
            -1001184863414: keks_config_dict
        }
        self.bot = telebot.TeleBot('370362982:AAH5ojKT0LSw8jS-vLfDF1bDE8rWWDyTeso')
        self.task_queue = list()
        self.sessions_dict = dict()
        self.additional_ids = dict()
        self.updater_schedulers_dict = dict()
        self.updaters_dict = dict()
