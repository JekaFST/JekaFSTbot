# -*- coding: utf-8 -*-
import re
from bs4 import BeautifulSoup


def get_bonus_data_from_engine(text, level_ids_dict, target_level_number):
    soup = BeautifulSoup(text, 'html.parser')
    bonus_data = {
        "ddlBonusFor": int([option.attrs['value'] for option in soup.find(id='ddlBonusFor').contents if 'selected' in option.attrs][0]),
        "txtBonusName": soup.find(attrs={"name": "txtBonusName"}).attrs['value'] if 'value' in soup.find(attrs={"name": "txtBonusName"}).attrs else '',
        "txtTask": soup.find(attrs={"name": "txtTask"}).text,
        "rbAllLevels-1": 0 if 'checked' in soup.find(id='rbAllLevels').attrs else 1,
        "txtHours": int(soup.find(attrs={"name": "txtHours"}).attrs['value']),
        "txtMinutes": int(soup.find(attrs={"name": "txtMinutes"}).attrs['value']),
        "txtSeconds": int(soup.find(attrs={"name": "txtSeconds"}).attrs['value']),
        "txtHelp": soup.find(attrs={"name": "txtHelp"}).text,
    }
    answers = [answer.attrs['value'] for answer in soup.find_all(attrs={'name': re.compile("answer_")}) if 'value' in answer.attrs]
    for i, answer in enumerate(answers):
        bonus_data['answer_-%s' % str(i + 1)] = answer
    if bonus_data['rbAllLevels-1'] == 1:
        levels = [level for level in soup.find_all(attrs={'name': re.compile("level_"), 'checked': 'checked'})]
        if len(levels) == 1:
            bonus_data['level_%s' % level_ids_dict[target_level_number]] = 'on'
        else:
            for level in levels:
                level_number = level.parent.parent.contents[3].text
                bonus_data['level_%s' % level_ids_dict[level_number]] = 'on'
    if 'checked' in soup.find(id='chkDelay').attrs:
        bonus_data['chkDelay'] = 'on'
        bonus_data['txtDelayHours'] = int(soup.find(attrs={"name": "txtDelayHours"}).attrs['value'])
        bonus_data['txtDelayMinutes'] = int(soup.find(attrs={"name": "txtDelayMinutes"}).attrs['value'])
        bonus_data['txtDelaySeconds'] = int(soup.find(attrs={"name": "txtDelaySeconds"}).attrs['value'])
    if 'checked' in soup.find(id='chkRelativeLimit').attrs:
        bonus_data['chkRelativeLimit'] = 'on'
        bonus_data['txtValidHours'] = int(soup.find(attrs={"name": "txtValidHours"}).attrs['value'])
        bonus_data['txtValidMinutes'] = int(soup.find(attrs={"name": "txtValidMinutes"}).attrs['value'])
        bonus_data['txtValidSeconds'] = int(soup.find(attrs={"name": "txtValidSeconds"}).attrs['value'])
    if 'checked' in soup.find(id='chkAbsoluteLimit').attrs:
        bonus_data['chkAbsoluteLimit'] = 'on'
        bonus_data['txtValidFrom'] = soup.find(attrs={"name": "txtValidFrom"}).attrs['value']
        bonus_data['txtValidTo'] = soup.find(attrs={"name": "txtValidTo"}).attrs['value']
    return bonus_data


def get_task_data_from_engine(text):
    soup = BeautifulSoup(text, 'html.parser')
    task_data = {
        'forMemberID': int([option.attrs['value'] for option in soup.find(id='forMemberID').contents if 'selected' in option.attrs][0]),
        'inputTask': soup.find(attrs={"name": "inputTask"}).text
    }
    if 'checked' in soup.find(attrs={"name": "chkReplaceNlToBr"}).attrs:
        task_data['chkReplaceNlToBr'] = 'on'
    return task_data


def get_help_data_from_engine(text):
    soup = BeautifulSoup(text, 'html.parser')
    help_data = {
        'ForMemberID': int([option.attrs['value'] for option in soup.find(id='ForMemberID').contents if 'selected' in option.attrs][0]),
        'NewPromptTimeoutDays': int(soup.find(attrs={"name": "NewPromptTimeoutDays"}).attrs['value']),
        'NewPromptTimeoutHours': int(soup.find(attrs={"name": "NewPromptTimeoutHours"}).attrs['value']),
        'NewPromptTimeoutMinutes': int(soup.find(attrs={"name": "NewPromptTimeoutMinutes"}).attrs['value']),
        'NewPromptTimeoutSeconds': int(soup.find(attrs={"name": "NewPromptTimeoutSeconds"}).attrs['value']),
        'NewPrompt': soup.find(attrs={"name": "NewPrompt"}).text
    }
    return help_data


def get_penalty_help_data_from_engine(text):
    soup = BeautifulSoup(text, 'html.parser')
    pen_help_data = {
        'ForMemberID': int([option.attrs['value'] for option in soup.find(id='ForMemberID').contents if 'selected' in option.attrs][0]),
        'txtPenaltyComment': soup.find(attrs={"name": "txtPenaltyComment"}).text,
        'NewPrompt': soup.find(attrs={"name": "NewPrompt"}).text,
        'NewPromptTimeoutDays': int(soup.find(attrs={"name": "NewPromptTimeoutDays"}).attrs['value']),
        'NewPromptTimeoutHours': int(soup.find(attrs={"name": "NewPromptTimeoutHours"}).attrs['value']),
        'NewPromptTimeoutMinutes': int(soup.find(attrs={"name": "NewPromptTimeoutMinutes"}).attrs['value']),
        'NewPromptTimeoutSeconds': int(soup.find(attrs={"name": "NewPromptTimeoutSeconds"}).attrs['value']),
        'PenaltyPromptHours': int(soup.find(attrs={"name": "PenaltyPromptHours"}).attrs['value']),
        'PenaltyPromptMinutes': int(soup.find(attrs={"name": "PenaltyPromptMinutes"}).attrs['value']),
        'PenaltyPromptSeconds': int(soup.find(attrs={"name": "PenaltyPromptSeconds"}).attrs['value']),
    }
    if 'checked' in soup.find(id='chkRequestPenaltyConfirm').attrs:
        pen_help_data['chkRequestPenaltyConfirm'] = 'on'
    return pen_help_data


def get_lvl_name_comment_data_from_engine(text):
    soup = BeautifulSoup(text, 'html.parser')
    level_name_comment_data = {
        'txtLevelName': soup.find(attrs={"name": "txtLevelName"}).attrs['value'] if 'value' in soup.find(attrs={"name": "txtLevelName"}).attrs else '',
        'txtLevelComment': soup.find(attrs={"name": "txtLevelComment"}).text,
    }
    return level_name_comment_data


def get_lvl_timeout_data_from_engine(text):
    soup = BeautifulSoup(text, 'html.parser')
    level_timeout_data = {
        'txtApHours': int(soup.find(attrs={"name": "txtApHours"}).attrs['value']),
        'txtApMinutes': int(soup.find(attrs={"name": "txtApMinutes"}).attrs['value']),
        'txtApSeconds': int(soup.find(attrs={"name": "txtApSeconds"}).attrs['value']),
        'updateautopass': '',
    }
    if 'checked' in soup.find(id='chkTimeoutPenalty').attrs:
        level_timeout_data['chkTimeoutPenalty'] = 'on'
        level_timeout_data['txtApPenaltyHours'] = int(soup.find(attrs={"name": "txtApPenaltyHours"}).attrs['value'])
        level_timeout_data['txtApPenaltyMinutes'] = int(soup.find(attrs={"name": "txtApPenaltyMinutes"}).attrs['value'])
        level_timeout_data['txtApPenaltySeconds'] = int(soup.find(attrs={"name": "txtApPenaltySeconds"}).attrs['value'])

    return level_timeout_data


def get_sector_data_from_engine(text, sector_id):
    sector_data = dict()
    soup = BeautifulSoup(text, 'html.parser')
    sector_name = soup.find(id='divSectorManage_%s' % sector_id).contents[1].text if soup.find(id='divSectorManage_%s' % sector_id) else None
    if sector_name:
        sector_data['txtSectorName'] = sector_name
        sector_data['savesector'] = ''
    else:
        sector_data['saveanswers'] = 1
    answers_soup = BeautifulSoup(str(soup.find(id='divAnswersEdit_%s' % sector_id)), 'html.parser')
    answers = answers_soup.find_all(attrs={'name': re.compile('txtAnswer_\d+')})
    for i, answer in enumerate(answers):
        sector_data['txtAnswer_%s' % str(i)] = answer.attrs['value']
        sector_data['ddlAnswerFor_%s' % str(i)] = 0

    return sector_data


def get_answers_data(text, sector_id, answers_data=None):
    soup = BeautifulSoup(text, 'html.parser')
    sector_name = soup.find(id='divSectorManage_%s' % sector_id).contents[1].text if soup.find(id='divSectorManage_%s' % sector_id) else None
    if not sector_name:
        answers_soup = BeautifulSoup(str(soup.find(id='divAnswersEdit_%s' % sector_id)), 'html.parser')
        answers = answers_soup.find_all(attrs={'name': re.compile('txtAnswer_\d+')})
        answers_data = [{'answer_id': re.findall(r'txtAnswer_(\d+)', str(answer))[0], 'answer_code': answer.attrs['value']} for answer in answers]
    return answers_data


def check_empty_first_sector(level_page, sector_id_to_clean=None):
    level_soup = BeautifulSoup(level_page, 'html.parser')
    sectors = level_soup.find_all(id=re.compile('divSectorManage_\d+'))
    for sector in sectors:
        sector_soup = BeautifulSoup(str(sector), 'html.parser')
        sector_id = re.findall(r'divSectorManage_(\d+)', str(sector))[0]
        sector_name = sector_soup.find(id='divSectorManage_%s' % sector_id).contents[1].text
        answers = level_soup.find(id='divAnswersView_%s' % sector_id)
        if not answers and sector_name.encode('utf-8') == 'Сектор 1':
            sector_id_to_clean = sector_id
            break
    return sector_id_to_clean
