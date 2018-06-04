from MainMethods import *
from UpdaterMethods import updater
from ExceptionHandler import ExceptionHandler

task_method_dict = {
    'start': start,
    'start_session': start_session,
    'stop_session': stop_session,
    'login_to_en': login,
    'start_updater': start_updater,
    'stop_updater': stop_updater,
    'updater': updater,
    'delay': set_updater_delay,
    'login': set_login,
    'password': set_password,
    'domain': set_domain,
    'game_id': set_game_id,
    'config': config,
    'channel_name': set_channel_name,
    'start_channel': start_channel,
    'stop_channel': stop_channel,
    'join': join,
    'reset_join': reset_join,
    'send_code_main': send_code_main,
    'send_code_bonus': send_code_bonus,
    'send_coords': send_coords,
    'send_task': send_task,
    'task_images': send_task_images,
    'send_sectors': send_all_sectors,
    'send_helps': send_all_helps,
    'send_last_help': send_last_help,
    'send_bonuses': send_all_bonuses,
    'unclosed_bonuses': send_unclosed_bonuses,
    'send_messages': send_auth_messages,
    'codes_on': enable_codes,
    'codes_off': disable_codes,
    'live_location': send_live_locations,
    'stop_live_location': stop_live_locations,
    'edit_live_location': edit_live_locations,
    'add_points_ll': add_custom_live_locations,
    'clean_ll': clean_live_locations,
    'get_codes_links': get_codes_links,
}


class TaskMethodMap(object):
    @staticmethod
    @ExceptionHandler.run_task_exception
    def run_task(task, bot):
        task_method_dict[task.type](task, bot)
