from apiclient.discovery import build
from httplib2 import Http
from oauth2client import file, client, tools
import re
from time import sleep
import logging
import requests
from bs4 import BeautifulSoup


class GoogleDocConnection(object):
    def __init__(self, spreadsheet_id):
        self.SCOPES = 'https://www.googleapis.com/auth/spreadsheets.readonly'
        self.service = build('sheets', 'v4', http=self.get_creds().authorize(Http()))
        self.SPREADSHEET_ID = spreadsheet_id

    def get_creds(self):
        store = file.Storage('credentials.json')
        creds = store.get()
        if not creds or creds.invalid:
            flow = client.flow_from_clientsecrets('client_secret.json', self.SCOPES)
            creds = tools.run_flow(flow, store)
        return creds

    def get_setup(self, login='', password='', domain='', gameid='', RANGE_NAME='Setup'):
        result = self.service.spreadsheets().values().get(spreadsheetId=self.SPREADSHEET_ID, range=RANGE_NAME).execute()
        values = result.get('values', [])
        for row in values:
            if 'login' in row:
                login = row[1]
            if 'password' in row:
                password = row[1]
            if 'domain' in row:
                domain = row[1]
            if 'gameid' in row:
                gameid = row[1]

        return login, password, domain, gameid

    def get_helps(self):
        RANGE_NAME = 'Helps'
        result = self.service.spreadsheets().values().get(spreadsheetId=self.SPREADSHEET_ID, range=RANGE_NAME).execute()
        values = result.get('values', [])[1:]
        return values

    def get_bonuses(self):
        RANGE_NAME = 'Bonuses'
        result = self.service.spreadsheets().values().get(spreadsheetId=self.SPREADSHEET_ID, range=RANGE_NAME).execute()
        values = result.get('values', [])[1:]
        return values

    def get_sectors(self):
        RANGE_NAME = 'Sectors'
        result = self.service.spreadsheets().values().get(spreadsheetId=self.SPREADSHEET_ID, range=RANGE_NAME).execute()
        values = result.get('values', [])[1:]
        return values

    def get_penalty_helps(self):
        RANGE_NAME = 'PenaltyHelps'
        result = self.service.spreadsheets().values().get(spreadsheetId=self.SPREADSHEET_ID, range=RANGE_NAME).execute()
        values = result.get('values', [])[1:]
        return values


class ENConnection(object):
    def __init__(self, domain, login, password, gameid):
        self.login_url = domain + '/Login.aspx'
        self.login = login
        self.password = password
        self.cookie = self.update_cookies()
        self.domain = domain
        self.gameid = gameid
        self.level_ids_dict = self.get_level_ids()

    def update_cookies(self):
        try:
            response = requests.post(self.login_url, data={'Login': self.login, 'Password': self.password}, headers={'Cookie': 'lang=ru'})
            cookie = response.request.headers['Cookie']
        except Exception:
            logging.exception("Can't get cookies by login URL")
            cookie = ''
        return cookie

    def get_level_ids(self):
        level_ids_dict = dict()
        url = self.domain + '/Administration/Games/LevelManager.aspx?gid=' + self.gameid
        response = requests.get(url, headers={'Cookie': self.cookie})
        soup = BeautifulSoup(response.text, 'html.parser')
        td = soup.find(id='ddlCopyFrom')
        for option_tag in td.contents:
            level_ids_dict[option_tag.text] = option_tag.attrs['value']
        return level_ids_dict

    def create_en_object(self, url, data, type):
        try:
            for i in xrange(2):
                response = requests.post(url, data=data, headers={'Cookie': self.cookie}, allow_redirects=False)
                if not response.status_code == 302:
                    logging.warning("Failed to create %s. Data: %s" % (type, str(data)))
                    break
                response_2 = requests.get(response.next.url, headers={'Cookie': self.cookie}, allow_redirects=False)
                if "your requests have been classified as robot's requests." in response_2.text.lower():
                    sleep(5)
                    self.cookie = self.update_cookies()
                    continue
                response_checker(data, type, response_2.text)
                break
        except Exception:
            logging.exception("Failed to create %s. Data: %s" % (type, str(data)))


def make_help_data_and_url(row, domain, gameid):
    help_data = {
        'ForMemberID': 0,
        'NewPromptTimeoutDays': int(row[1]) if row[1] else 0,
        'NewPromptTimeoutHours': int(row[2]) if row[2] else 0,
        'NewPromptTimeoutMinutes': int(row[3]) if row[3] else 0,
        'NewPromptTimeoutSeconds': int(row[4]) if row[4] else 0,
        'NewPrompt': row[0] if row[0] else ''
    }
    help_url = domain + '/Administration/Games/PromptEdit.aspx?gid=' + gameid + '&level=' + str(row[5])
    return help_data, help_url


# txt - award
# txtDelay - delay
# txtValid - time to answer
def make_bonus_data_and_url(row, domain, gameid, level_ids_dict):
    bonus_data = {
        "ddlBonusFor": 0,
        "txtBonusName": row[0] if row[0] else '',
        "txtTask": row[1] if row[1] else '',
        "rbAllLevels-1": 0 if 'true' in row[3].lower() else 1,
        "txtHours": int(row[5]) if row[5] else 0,
        "txtMinutes": int(row[6]) if row[6] else 0,
        "txtSeconds": int(row[7]) if row[7] else 0,
        "txtHelp": row[8] if row[8] else ''
    }
    answers = re.findall(r'.+\b', row[2])
    for i, answer in enumerate(answers):
        bonus_data['answer_-%s' % str(i+1)] = answer
    level_numbers = re.findall(r'.+\b', row[4])
    for level_number in level_numbers:
        bonus_data[str('level_%s' % level_ids_dict[level_number])] = 'on'
    if row[9] or row[10] or row[11]:
        bonus_data['chkDelay'] = 'on'
        bonus_data['txtDelayHours'] = int(row[9]) if row[9] else 0
        bonus_data['txtDelayMinutes'] = int(row[10]) if row[10] else 0
        bonus_data['txtDelaySeconds'] = int(row[11]) if row[11] else 0
    if row[12] or row[13] or row[14]:
        bonus_data['txtValidMinutes'] = int(row[12]) if row[12] else 0
        bonus_data['txtValidMinutes'] = int(row[13]) if row[13] else 0
        bonus_data['txtValidSeconds'] = int(row[14]) if row[14] else 0
    bonus_url = domain + '/Administration/Games/BonusEdit.aspx?gid=' + gameid + '&level=' + str(row[15]) + '&bonus=0&action=save'
    return bonus_data, bonus_url


def make_sector_data_and_url(row, domain, gameid):
    sector_data = {
        'txtSectorName': row[0] if row[0] else ''
    }
    answers = re.findall(r'.+\b', row[1])
    for i, answer in enumerate(answers):
        sector_data['txtAnswer_%s' % str(i)] = answer
        sector_data['ddlAnswerFor_%s' % str(i)] = 0
    sector_data['savesector'] = ''
    sector_url = domain + '/Administration/Games/LevelEditor.aspx?gid=' + gameid + '&level=' + str(row[2])
    return sector_data, sector_url


# PromptTimeout - delay
# PenaltyPrompt - penalty time
def make_penalty_help_data_and_url(row, domain, gameid):
    pen_help_data = {
        'ForMemberID': 0,
        'txtPenaltyComment': row[0] if row[0] else '',
        'NewPromptTimeoutDays': int(row[1]) if row[1] else 0,
        'NewPromptTimeoutHours': int(row[2]) if row[2] else 0,
        'NewPromptTimeoutMinutes': int(row[3]) if row[3] else 0,
        'NewPromptTimeoutSeconds': int(row[4]) if row[4] else 0,
        'PenaltyPromptHours': int(row[6]) if row[6] else 0,
        'PenaltyPromptMinutes': int(row[7]) if row[7] else 0,
        'PenaltyPromptSeconds': int(row[8]) if row[8] else 0,

    }
    if 'false' not in row[5].lower():
        pen_help_data['chkRequestPenaltyConfirm'] = 'on'
    pen_help_data['NewPrompt'] = ''
    pen_help_url = domain + '/Administration/Games/PromptEdit.aspx?gid=' + gameid + '&level=' + str(row[9]) + '&penalty=1'
    return pen_help_data, pen_help_url


def response_checker(data, type, text):
    try:
        type_checker_map[type](data, text)
    except Exception:
        logging.exception('Error in response_checker')


def help_checker(data, text):
    soup = BeautifulSoup(text, 'html.parser')
    help_text = soup.find(id='PromptText')
    if data['NewPrompt'] != help_text.text:
        logging.warning("Help text mismatch. Data: %s" % str(data))


def bonus_checker(data, text):
    soup = BeautifulSoup(text, 'html.parser')
    bonus_name = soup.find(id='panelBonusName')
    if data['txtBonusName'] and data['txtBonusName'] != bonus_name.text:
        logging.warning("There is a mismatch in a bonus name. Data: %s" % str(data))


def sector_checker(data, text):
    return


def penalty_help_checker(data, text):
    soup = BeautifulSoup(text, 'html.parser')
    pen_help_text = soup.find(id='divPromptComment')
    if data['txtPenaltyComment'] != pen_help_text.text:
        logging.warning("Penalty help text mismatch. Data: %s" % str(data))


type_checker_map = {
    'help': help_checker,
    'bonus': bonus_checker,
    'sector': sector_checker,
    'PenaltyHelp': penalty_help_checker,
}
