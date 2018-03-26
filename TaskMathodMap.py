from MainMethods import *
from UpdaterMethods import updater

task_method_dict = {
    'start': start,  # refactored
    'start_session': start_session,  # refactored
    'stop_session': stop_session,  # refactored
    'login_to_en': login,  # refactored
    'start_updater': start_updater,
    'stop_updater': stop_updater,
    'updater': updater,
    'delay': set_updater_delay,
    'login': set_login,  # refactored
    'password': set_password,  # refactored
    'domain': set_domain,  # refactored
    'game_id': set_game_id,  # refactored
    'config': config,  # refactored
    'channel_name': set_channel_name,
    'start_channel': start_channel,
    'stop_channel': stop_channel,
    'join': join,
    'reset_join': reset_join,
    'send_code_main': send_code_main,
    'send_code_bonus': send_code_bonus,
    'send_coords': send_coords,
    'send_task': send_task,  # refactored
    'task_images': send_task_images,  # refactored
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
    'add_points_ll': add_custom_live_locations
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
            'points_dict': task.points_dict
        }
        task_method_dict[task.type](**kwargs)

# start(task.chat_id, bot, main_vars.sessions_dict)
# start_session(task.chat_id, bot, main_vars.sessions_dict[task['chat_id']])
# updater(task['chat_id'], bot, main_vars.sessions_dict[task['chat_id']], main_vars.updaters_dict)
# send_code_main(chat_id, bot, session, task['message_id'], task['code'])
# send_code_bonus(chat_id, bot, session, task['message_id'], task['code'])
# send_coords(task['chat_id'], bot, task['coords'])
# send_live_locations(chat_id, bot, session, task['coords'], task['duration'])
# stop_live_locations(chat_id, bot, session, task['point'])
# edit_live_locations(chat_id, bot, session, task['point'], task['coords'])
# add_custom_live_locations(chat_id, bot, session, task['points_dict'], task['duration'])
# send_task(chat_id, bot, session, task['storm_level'])
# send_task_images(task['chat_id'], bot, main_vars.sessions_dict[task['chat_id']])
# send_all_sectors(chat_id, bot, session, task['storm_level'])
# send_all_helps(chat_id, bot, session, task['storm_level'])
# send_last_help(chat_id, bot, session, task['storm_level'])
# send_all_bonuses(chat_id, bot, session, task['storm_level'])
# send_unclosed_bonuses(chat_id, bot, session, task['storm_level'])
# send_auth_messages(chat_id, bot, session, task['storm_level'])
# stop_session(task['chat_id'], bot, main_vars.sessions_dict[task['chat_id']], main_vars.additional_ids)
# config(task['chat_id'], bot, main_vars.sessions_dict[task['chat_id']])
# set_login(task['chat_id'], bot, main_vars.sessions_dict[task['chat_id']], task['new_login'])
# set_password(task['chat_id'], bot, main_vars.sessions_dict[task['chat_id']], task['new_password'])
# set_domain(task['chat_id'], bot, main_vars.sessions_dict[task['chat_id']], task['new_domain'])
# set_game_id(task['chat_id'], bot, main_vars.sessions_dict[task['chat_id']], task['new_game_id'])
# login(task['chat_id'], bot, main_vars.sessions_dict[task['chat_id']])
# start_updater(task['chat_id'], bot, main_vars)
# set_updater_delay(task['chat_id'], bot, main_vars.sessions_dict[task['chat_id']], task['new_delay'])
# stop_updater(main_vars.sessions_dict[task['chat_id']])
# set_channel_name(task['chat_id'], bot, main_vars.sessions_dict[task['chat_id']], task['new_channel_name'])
# start_channel(task['chat_id'], bot, main_vars.sessions_dict[task['chat_id']])
# stop_channel(task['chat_id'], bot, main_vars.sessions_dict[task['chat_id']])
# enable_codes(task['chat_id'], bot, main_vars.sessions_dict[task['chat_id']])
# disable_codes(task['chat_id'], bot, main_vars.sessions_dict[task['chat_id']])