# -*- coding: utf-8 -*-
import re

from bs4 import BeautifulSoup


def get_source_bonus_data(text, level_ids_dict):
    soup = BeautifulSoup(text, 'html.parser')
    source_bonus_data = {
        "ddlBonusFor": int(soup.find(id='ddlBonusFor').contents[0].attrs['value']),
        "txtBonusName": soup.find(attrs={"name": "txtBonusName"}).attrs['value'],
        "txtTask": soup.find(attrs={"name": "txtTask"}).text,
        "rbAllLevels-1": 0 if 'checked' in soup.find(id='rbAllLevels').attrs else 1,
        "txtHours": soup.find(attrs={"name": "txtHours"}).attrs['value'],
        "txtMinutes": soup.find(attrs={"name": "txtMinutes"}).attrs['value'],
        "txtSeconds": soup.find(attrs={"name": "txtSeconds"}).attrs['value'],
        "txtHelp": soup.find(attrs={"name": "txtHelp"}).text,
    }
    answers = [answer.attrs['value'] for answer in soup.find_all(attrs={'name': re.compile("answer_")}) if 'value' in answer.attrs]
    for i, answer in enumerate(answers):
        source_bonus_data['answer_-%s' % str(i + 1)] = answer
    if source_bonus_data['rbAllLevels-1'] == 1:
        levels = [level for level in soup.find_all(attrs={'name': re.compile("level_"), 'checked': 'checked'})]
        for level in levels:
            level_number = level.parent.parent.contents[3].text
            source_bonus_data['level_%s' % level_ids_dict[level_number]] = 'on'
    # if row[9] or row[10] or row[11]:
    #     bonus_data['chkDelay'] = 'on'
    #     bonus_data['txtDelayHours'] = int(row[9]) if row[9] else 0
    #     bonus_data['txtDelayMinutes'] = int(row[10]) if row[10] else 0
    #     bonus_data['txtDelaySeconds'] = int(row[11]) if row[11] else 0
    # if row[12] or row[13] or row[14]:
    #     bonus_data['chkRelativeLimit'] = 'on'
    #     bonus_data['txtValidHours'] = int(row[12]) if row[12] else 0
    #     bonus_data['txtValidMinutes'] = int(row[13]) if row[13] else 0
    #     bonus_data['txtValidSeconds'] = int(row[14]) if row[14] else 0
    # if row[15] and row[16]:
    #     bonus_data['chkAbsoluteLimit'] = 'on'
    #     bonus_data['txtValidFrom'] = row[15] if row[15] else ''
    #     bonus_data['txtValidTo'] = row[16] if row[16] else ''
    return source_bonus_data
