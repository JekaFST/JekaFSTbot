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
