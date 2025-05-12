# common functions
import sys
import requests
import json
import yaml
from datetime import datetime
from urllib.parse import unquote
import constants as CONST

def is_medicine_tsv_avail():
    # e.g. http://download.openzim.org/wp1/enwiki_2022-03/customs/medicine.tsv
    url = 'http://download.openzim.org/wp1/enwiki_'
    url += datetime.now().strftime('%Y-%m')
    url += '/customs/medicine.tsv'

    r = requests.head(url)
    if r.status_code == 200:
        return True
    else:
        return False

def zimfarm_running(recipe):
    stat = get_zimfarm_stat(recipe)
    if stat['most_recent_task']['status'] == 'scraper_started':
        return True
    else:
        return False

def get_zimfarm_stat(recipe):
    # status of current run in ['most_recent_task']['status']
    zimfarm_api = 'https://api.farm.openzim.org/v1/schedules/'
    r = requests.get(zimfarm_api + recipe)
    return r.json()

def page_encode(page):
    # encoded_page = page.replace('_', '%20').replace('/', '%2F').replace(':', '%3A').replace("'", '%27').replace("+", '%2B')
    encoded_page = page.replace(' ', '_').replace('/', '%2F').replace(':', '%3A').replace("'", '%27').replace("+", '%2B').replace("&", '%26')
    return encoded_page

def page_decode(encoded_page):
    page = unquote(encoded_page)
    return page

def get_cacher_headers():
    tokens = read_yaml('data/token.yml')
    cacher_headers = CONST.cacher_headers
    cacher_headers.update({'Authorization': 'Bearer {}'.format(tokens['cacher_token'])})
    return cacher_headers

# taken from sp_lib
def read_json_file(file_path):
    try:
        with open(file_path, 'r') as json_file:
            readstr = json_file.read()
            json_dict = json.loads(readstr)
        return json_dict
    except OSError as e:
        print('Unable to read url json file', e)
        raise

def write_json_file(src_dict, target_file, sort_keys=False):
    try:
        with open(target_file, 'w', encoding='utf8') as json_file:
            json.dump(src_dict, json_file, ensure_ascii=False, indent=2, sort_keys=sort_keys)
            json_file.write("\n")  # Add newline cause Py JSON does not
    except OSError as e:
        raise

def write_list(data, file):
    with open(file, 'w') as f:
        for d in data:
            f.write(d + '\n')

def read_file_tail(file_path, num_lines=8):
    text_list = read_file_list(file_path)
    if num_lines >= len(text_list):
        num_lines = 0
    text = ''
    for item in text_list[num_lines * -1:]:
        text += item + '\n'
    return text

def read_file_list(file_path):
    text = read_file(file_path)
    text_list = text.split('\n')[:-1]
    return text_list

def read_file(file_path, mode='rt'):
    try:
        with open(file_path, mode) as f:
            return f.read()
    except OSError as e:
        print('Unable to read file', e)
        raise

def read_yaml(file_name, loader=yaml.SafeLoader):
    try:
        with open(file_name, 'r') as f:
            y = yaml.load(f, Loader=loader)
            if y == None: # file is empty
                y = {}
            return y
    except:
        raise
