#!/usr/bin/env python3
# su - www-data -s /bin/bash -c '/srv2/mdwiki-cacher/load-cache.py' for testing
import os
import logging
import sys
from datetime import timedelta, date
import time
import time
import requests
import json
import argparse
from urllib.parse import urljoin, urldefrag, urlparse, parse_qs
from requests_cache import CachedSession
from requests_cache import FileCache
from common import *
import constants as CONST

# ToDo set enwp cache to 1 or 7 day expire or check url against some date

MDWIKI_CACHER_DIR = '/srv/mdwiki-cacher/'
os.chdir(MDWIKI_CACHER_DIR)

SESSION = CachedSession('2025_mdwiki_cache', backend='sqlite')

enwp_list = []
failed_url_list = []

ENWP_CACHE_HIST_FILE = 'enwp_cache-refresh-hist.txt'
enwp_api = "https://en.wikipedia.org/w/api.php"

test_enwp = '100med-enwp.tsv'
test_mdwiki = '100med-mdwiki.tsv'

enwp_list = read_file_list(test_enwp)
mdwiki_list = read_file_list('data/mdwiki.tsv')


# test pages
p1 = 'Adenomere'
p2 = 'Brivudine'

VERBOSE = False
force_refresh = False

def main():
    global enwp_list
    set_logger()

def test():
    load_cache('enwp', enwp_list)
    load_cache('mdwiki', mdwiki_list)
    cached_urls = list(SESSION.cache.urls)

def load_mdwiki_cache():
    global force_refresh
    global SESSION
    SESSION = CachedSession('2025_mdwiki_cache', backend='sqlite')
    force_refresh = True
    for page in mdwiki_list:
        page_urls = get_api_calls(CONST.mdwiki_domain, CONST, page)
        for url in page_urls:
            refresh_mdwiki_cache_url(url, force_refresh)

def load_cache(target, article_list):
    for title in article_list:
        refresh_cache_page(target, page_encode(title), force_refresh)

def refresh_cache_page(target, page, force_refresh=False):

    url = CONST.rest_page + page + '/html' # html from rest
    refresh_cache_url(target, url, force_refresh)

    url = CONST.redirect_query + page # revisions and redirects
    refresh_cache_url(target, url, force_refresh)

    url = CONST.modules_query + page.replace('_', '+') # modules
    refresh_cache_url(target, url, force_refresh)

    #url = CONST.enwp_domain + CONST.videdit_page + page
    #refresh_cache_url(url, force_refresh)

def get_api_calls(host, constants, page):
    api_calls = []
    url = host + constants.rest_page + page + '/html' # html from rest
    api_calls.append(url)
    url = host + constants.redirect_query + page # revisions and redirects
    api_calls.append(url)
    url = host + constants.modules_query + page.replace('_', '+') # modules
    api_calls.append(url)
    return api_calls

def refresh_cache_url(target, url, force_refresh):
    if target == 'enwp':
        url = CONST.enwp_domain + url
        refresh_enwp_cache_url(url, force_refresh)
    else:
        url = CONST.mdwiki_domain + url
        refresh_mdwiki_cache_url(url, force_refresh)

def refresh_enwp_cache_url(url, force_refresh):
    global failed_url_list
    get_except = False
    if not force_refresh and SESSION.cache.contains(url=url):
        return
    try:
        # r = uncached_session.get(url, headers=CONST.cacher_headers)
        r = requests.get(url, headers=CONST.cacher_headers)
    except:
        get_except = True

    if get_except or r.status_code != 200:
        logging.info('Failed to get URL: %s\n', str(url))
        failed_url_list.append(url)
    elif r.content.startswith(b'{"error":'):
        logging.info('Error getting: %s\n', str(url))
        logging.info(r.content + '\n')
        failed_url_list.append(url)
    else:
        SESSION.cache.save_response(r)

def refresh_mdwiki_cache_url(url, force_refresh):
    global failed_url_list
    get_except = False
    if not force_refresh and SESSION.cache.contains(url=url):
        return
    try:
        # r = uncached_session.get(url, headers=CONST.cacher_headers)
        r = requests.get(url, headers=CONST.cacher_headers)
    except:
        get_except = True

    if get_except or r.status_code == 503 or r.content.startswith(b'{"error":'):
        r = retry_url(url)
    if r:
        SESSION.cache.save_response(r)
    else:
        logging.info('Failed to get URL: %s\n', str(url))
        failed_url_list.append(url)

def retry_url(url):
    logging.info("Error or 503 in URL: %s\n", str(url))
    sleep_secs = 20
    for i in range(10):
        get_except = False
        try:
            resp = requests.get(url, headers=CONST.cacher_headers) # did not use mdwiki_uncached_session to avoid conflict on retry
        except:
            get_except = True
        if not get_except and resp.status_code != 503 and not resp.content.startswith(b'{"error":'):
            return resp
        logging.info('Retrying URL: %s\n', str(url))
        time.sleep(i * sleep_secs)
    return None

def get_enwp_url(url, force_refresh): # NOT USED
    # check if url in cache
    # if not get it to add to cache
    # no retry

    if force_refresh or not SESSION.cache.contains(url=url):
        global failed_url_list
        if VERBOSE:
            logging.info('Getting URL: %s\n', str(url))
        resp = SESSION.get(url)
        if resp.status_code != 200 or resp.content.startswith(b'{"error":'):
            logging.error('Failed URL: %s\n', str(url))
            failed_url_list.append(url)
    return

def get_last_revision(page):
    url = CONST.last_revision_query + page
    resp = requests.get(url=url)
    data = resp.json()
    return data['query']['pages'][0]['revisions'][0]['timestamp']

def get_last_edit_date(page): # does not do redirects from redirect to real page
    params = {
        'action':"compare",
        'format':"json",
        'fromtitle':page,
        'totitle':page,
        'prop':'timestamp'
    }
    resp = requests.get(url=enwp_api, params=params)
    data = resp.json()
    return data['compare']['fromtimestamp']

def breakout_resp(resp):
    headers = calc_resp_headers(resp)
    # print(resp.content)
    return str(resp.status_code), headers, resp.content

def calc_resp_headers(resp):
    headers = [('Content-type', resp.headers['content-type'])]
    # the received content length is 1 less than true length
    #if 'content-length' in resp.headers:
    #    headers.append(('content-length', resp.headers['content-length']))
    return headers

def set_logger():
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)
    formatter = logging.Formatter('%(asctime)s | %(levelname)s | %(message)s',
                                '%m-%d-%Y %H:%M:%S')

    stdout_handler = logging.StreamHandler(sys.stdout)
    stdout_handler.setLevel(logging.INFO)
    stdout_handler.setFormatter(formatter)

    file_handler = logging.FileHandler('enwp-refresh-cache.log')
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(formatter)

    logger.addHandler(file_handler)
    logger.addHandler(stdout_handler)

def write_list(data, file):
    with open(file, 'w') as f:
        for d in data:
            f.write(d + '\n')

def get_enwp_page_list():
    global enwp_list
    #mdwiki_redirects = read_json_file('data/mdwiki_redirects.json')
    try:
        with open('data/enwp.tsv') as f:
            txt = f.read()
        enwp_list = txt.split('\n')[:-1]
    except Exception as error:
        print(error)
        print('Failed to read enwp.tsv. Exiting.')
        sys.exit(1)

def parse_args(): # for future
    parser = argparse.ArgumentParser(description="Create or refresh cache for mdwiki-cacher.")
    parser.add_argument("-i", "--interactive", help="exit so can be run interactively", action="store_true")
    parser.add_argument("-a", "--all", help="Print messages.", action="store_true")
    return parser.parse_args()

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        pass
