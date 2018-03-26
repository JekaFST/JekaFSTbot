from MainMethods import *
from UpdaterMethods import updater

task_method_dict = {
    'start': start,  # refactored
    'start_session': start_session,  # refactored
    'stop_session': stop_session,  # refactored
    'login_to_en': login,  # refactored
    'start_updater': start_updater,  # refactored
    'stop_updater': stop_updater,  # refactored
    'updater': updater,  # refactored
    'delay': set_updater_delay,  # refactored
    'login': set_login,  # refactored
    'password': set_password,  # refactored
    'domain': set_domain,  # refactored
    'game_id': set_game_id,  # refactored
    'config': config,  # refactored
    'channel_name': set_channel_name,  # refactored
    'start_channel': start_channel,  # refactored
    'stop_channel': stop_channel,  # refactored
    'join': join,  # refactored
    'reset_join': reset_join,  # refactored
    'send_code_main': send_code_main,  # refactored
    'send_code_bonus': send_code_bonus,  # refactored
    'send_coords': send_coords,  # refactored
    'send_task': send_task,  # refactored
    'task_images': send_task_images,  # refactored
    'send_sectors': send_all_sectors,  # refactored
    'send_helps': send_all_helps,  # refactored
    'send_last_help': send_last_help,  # refactored
    'send_bonuses': send_all_bonuses,  # refactored
    'unclosed_bonuses': send_unclosed_bonuses,  # refactored
    'send_messages': send_auth_messages,  # refactored
    'codes_on': enable_codes,  # refactored
    'codes_off': disable_codes,  # refactored
    'live_location': send_live_locations,  # refactored
    'stop_live_location': stop_live_locations,  # refactored
    'edit_live_location': edit_live_locations,  # refactored
    'add_points_ll': add_custom_live_locations,  # refactored
}


class TaskMethodMap(object):
    @staticmethod
    def run_task(task, bot):
        kwargs = {
            'chat_id': task.chat_id,
            'bot': bot,
            'message_id': task.message_id,
            'add_chat_id': task.user_id,
            'session': task.session,
            'sessions_dict': task.sessions_dict,
            'add_chat_ids_per_session': task.add_chat_ids_per_session,
            'main_vars': task.main_vars,
            'updaters_dict': task.updaters_dict,
            'new_delay': task.new_delay,
            'new_login': task.new_login,
            'new_password': task.new_password,
            'new_domain': task.new_domain,
            'new_game_id': task.new_game_id,
            'new_channel_name': task.new_channel_name,
            'code': task.code,
            'coords': task.coords,
            'storm_level_number': task.storm_level_number,
            'duration': task.duration,
            'point': task.point,
            'points_dict': task.points_dict,
        }
        task_method_dict[task.type](**kwargs)