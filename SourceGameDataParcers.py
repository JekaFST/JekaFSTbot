# -*- coding: utf-8 -*-
from bs4 import BeautifulSoup


def get_source_bonus_data(text):
    soup = BeautifulSoup(text, 'html.parser')
    source_bonus_data = {
        "ddlBonusFor": soup.find(id='ddlBonusFor'),
        "txtBonusName": soup.find(attrs={"name": "txtBonusName"}).text,
        "txtTask": soup.find(attrs={"name": "txtTask"}).text,
        "rbAllLevels-1": soup.find(id='rbAllLevels'),
        "txtHours": soup.find(attrs={"name": "txtHours"}).text,
        "txtMinutes": soup.find(attrs={"name": "txtMinutes"}).text,
        "txtSeconds": soup.find(attrs={"name": "txtSeconds"}).text,
        "txtHelp": soup.find(attrs={"name": "txtHelp"}).text,
    }
    return source_bonus_data
