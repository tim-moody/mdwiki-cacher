#!/usr/bin/env python3
# su - www-data -s /bin/bash -c '/srv/mdwiki-cacher/load-2025-cache.py' for testing
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

MDWIKI_CACHER_DIR = '/srv/mdwiki-cacher/'
os.chdir(MDWIKI_CACHER_DIR)

SESSION = CachedSession('2025_mdwiki_cache', backend='sqlite')

enwp_list = []
failed_mdwiki_articles = {}
failed_url_list = []

enwp_list = read_file_list('data/enwp.tsv')
mdwiki_list = read_file_list('data/mdwiki.tsv')

cacher_headers = get_cacher_headers()

# test pages
p1 = 'Adenomere'
p2 = 'Brivudine'

VERBOSE = False
force_refresh = False

def main():
    set_logger()
    args = parse_args()
    # args.device is either value or None
    if args.interactive: # allow override of path
        sys.exit()

    load_mdwiki_cache_list(mdwiki_list, force_refresh=force_refresh)
    write_json_file(failed_mdwiki_articles, 'failed_mdwiki_articles.json')
    write_list(failed_url_list, 'failed_mdwiki_urls.tsv')

def test():
    load_mdwiki_cache()
    cached_urls = list(SESSION.cache.urls)

def load_mdwiki_cache():
    global force_refresh
    global SESSION
    SESSION = CachedSession('2025_mdwiki_cache', backend='sqlite')
    force_refresh = True
    load_mdwiki_cache_list(mdwiki_list)

def load_mdwiki_cache_list(article_list, force_refresh=force_refresh):
    global SESSION
    global failed_mdwiki_articles
    SESSION = CachedSession('2025_mdwiki_cache', backend='sqlite')
    for title in article_list:
        refresh_mdwiki_title(title, force_refresh=force_refresh)

def refresh_mdwiki_title(title, force_refresh=force_refresh):
    global failed_mdwiki_articles
    page_urls = get_api_calls(CONST.mdwiki_domain, title)
    for url in page_urls:
        if not refresh_mdwiki_cache_url(url, force_refresh):
            failed_mdwiki_articles[title] = 'FAILED'
            break

def get_api_calls(host, title):
    title = page_encode(title)
    api_calls = []
    url = host + CONST.rest_page + title + '/html' # html from rest
    api_calls.append(url)
    url = host + CONST.redirect_query + title # revisions and redirects
    api_calls.append(url)
    url = host + CONST.modules_query + title.replace('_', '+') # modules
    api_calls.append(url)
    return api_calls

def refresh_mdwiki_cache_url(url, force_refresh):
    global failed_url_list
    get_except = False
    if not force_refresh and SESSION.cache.contains(url=url):
        return True
    try:
        # r = uncached_session.get(url, headers=CONST.cacher_headers)
        r = requests.get(url, headers=cacher_headers)
    except Exception as e:
        logging.error('Exception getting URL: %s\n', str(url))
        failed_url_list.append(url)
        return False
    if r.status_code == 503 or r.content.startswith(b'{"error":'):
        if r.content.startswith(b'{"error":'):
            print(r.content)
            if b'"code":"missingtitle"' in r.content:
                logging.info('Title missing in %s\n', str(url))
                failed_url_list.append(url)
                return False
        r = retry_url(url)
    if r:
        SESSION.cache.save_response(r)
        return True
    else:
        logging.info('Failed to get URL: %s\n', str(url))
        failed_url_list.append(url)
        return False

def retry_url(url):
    logging.info("Error or 503 in URL: %s\n", str(url))
    sleep_secs = 20
    for i in range(10):
        get_except = False
        try:
            resp = requests.get(url, headers=cacher_headers) # did not use mdwiki_uncached_session to avoid conflict on retry
        except:
            get_except = True
        if not get_except and resp.status_code != 503 and not resp.content.startswith(b'{"error":'):
            return resp
        if resp.content.startswith(b'{"error":'):
            print(resp.content)
        logging.info('Retrying URL: %s\n', str(url))
        time.sleep(i * sleep_secs)
    return None

def list_mdwiki_not_cached(article_list):
    global SESSION
    SESSION = CachedSession('2025_mdwiki_cache', backend='sqlite')
    not_cached = []
    for title in article_list:
        page_urls = get_api_calls(CONST.mdwiki_domain, title)
        for url in page_urls:
            if not SESSION.cache.contains(url=url):
                not_cached.append(url)
    return not_cached

def get_last_revision(page): # NOT USED
    url = CONST.last_revision_query + page
    resp = requests.get(url=url)
    data = resp.json()
    return data['query']['pages'][0]['revisions'][0]['timestamp']

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

    file_handler = logging.FileHandler('load-2025-cache.log')
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(formatter)

    logger.addHandler(file_handler)
    logger.addHandler(stdout_handler)

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
