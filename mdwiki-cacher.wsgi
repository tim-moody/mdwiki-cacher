#!/usr/bin/env python3
import sys
import time
from datetime import timedelta
import requests
import json
import base64
# import pymysql.cursors
from urllib.parse import urljoin, urldefrag, urlparse, parse_qs, unquote
from requests_cache import CachedSession
from common import * # functions common to several modules
import constants as CONST

mdwiki_list = {}
mdwiki_redirects = {}
mdwiki_redirect_list = []
mdwiki_rd_lookup = {}
enwp_list = []

# replaced with constants
# mdwiki_domain = 'https://mdwiki.org'
# enwp_domain = 'https://en.wikipedia.org'
# mdwiki_api_db  = 'mdwiki_api'
# mdwiki_wiki_db  = 'mdwiki_wiki'
# mdwiki_other_db  = 'mdwiki_other'
# enwp_db ='enwp'

expiry_days = timedelta(days=7)

# mdwiki_cache = CachedSession('2025_mdwiki_cache.sqlite', backend='sqlite')
# et al

auth_cacher_headers = get_auth_cacher_headers()

mdwiki_intro_page = '/wiki/App%2FIntroPage'
nonwiki_url = '/nonwiki/'
article_list = 'data/mdwikimed.tsv'
uwsgi_log = '/var/log/uwsgi/app/mdwiki-cacher.log'
extract_api = '/w/api.php?action=query&format=json&titles='

VERSION = CONST.VERSION
VERBOSE = True
TRAFFIC_ENABLED = False # Determines whether traffic sent to mdwik
skipped_page_count = 0

# /robots.txt handled by nginx

###################
# is it /api/rest_v1 or /w/rest.php/v1
# it is /w/rest.php/v1
# requires mwoffliner:dev and --forceRender="RestApi"
####################
# these are probing queris at the start of a run
# for now we will leave the rest_v1 versions in case they are probed

mdwiki_urls = ['/',
                '/wiki/',
                mdwiki_intro_page,
                '/api/rest_v1/page/mobile-sections/Main_Page',
                '/api/rest_v1/page/html/Main_Page',
                '/w/rest.php/v1/page/Main_Page',
                '/w/api.php?action=visualeditor&mobileformat=html&format=json&paction=parse&page=Main_Page',
                '/w/api.php?',
                '/w/api.php?action=query&format=json&prop=redirects%7Crevisions%7Ccoordinates&rdlimit=max&rdnamespace=',
                '/w/api.php?action=query&meta=siteinfo&siprop=namespaces%7Cnamespacealiases&format=json',
                '/wiki/?title=Mediawiki%3Aoffline.css&action=raw',
                '/logo.png',
                '/logo.svg',
                '/favicon.ico']

accepted_user_agents = ['axios/1.6.8',
                        'MWOffliner/HEAD',
                        'MWOffliner/HEAD (info@iiab.me)',
                        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36']

#enwp_session = CachedSession(enwp_db, backend='sqlite')
#mdwiki_session = CachedSession(mdwiki_db, backend='sqlite')

def application(environ, start_response):
    # print(environ['HTTP_USER_AGENT'])
    # there are too manu user agents and they are likely to change
    #if environ['HTTP_USER_AGENT'] not in accepted_user_agents:
    #    start_response('401', [('Content-type', 'text/plain')])
    #    return('not permitted')

    req_method = environ['REQUEST_METHOD']
    # req_uri = environ['REQUEST_URI'].split('?')[0] # remove any cache buster
    req_uri = environ['REQUEST_URI']

    print(req_method, req_uri)
    if req_method == 'GET':
        log_request(req_uri, environ)
        if req_uri == mdwiki_intro_page: # reset count on start of run
            skipped_page_count = 0
        if req_uri in mdwiki_urls: # some hardcoded urls that must go to mdwiki
            if not TRAFFIC_ENABLED: # if traffic not enabled, return 403
                status, response_headers, response_body = respond_403()
            else:
                # status, response_headers, response_body = get_mdwiki_url_direct(req_uri)
                url = CONST.mdwiki_domain + req_uri
                # headers = get_request_headers()
                # resp = requests.get(url, headers=CONST.cacher_headers, allow_redirects=False) # non authorized
                resp = requests.get(url, allow_redirects=True) # non authorized
                status, response_headers, response_body = breakout_resp(resp)
                print('mdwiki_urls: ' + url + ' Status: ' + status + '\n')
                if status == 400:
                    print(resp.content)
        elif req_uri.startswith(nonwiki_url):
            status, response_headers, response_body = do_nonwiki(req_uri, environ)

        else:
            if not TRAFFIC_ENABLED: # if traffic not enabled, return 403
                status, response_headers, response_body = respond_403()
            else:
                # status, response_headers, response_body = do_GET(req_uri)
                status, response_headers, response_body = get_mdwiki_url_direct_authorized(req_uri)
                print('direct_urls: ' + req_uri + ' Status: ' + status + '\n')
                print(response_body[:50] + '\n'))
        start_response(status, response_headers)
        # convert string response back to bytes
        # return [response_body.encode()]
        return [response_body]

    elif req_method == 'POST':
        pass


def do_POST():
    pass

def dump(environ):
    print("Dump Environment")
    response_body = ['%s: %s' % (key, value) for key, value in sorted(environ.items())]
    response_body = '\n'.join(response_body)
    return response_body

def get_mdwiki_url_direct_authorized(path):
    if VERBOSE:
        print('In get_mdwiki_url_direct_authorized', path + '\n')
    # ADD RETRY
    url = CONST.mdwiki_domain + path
    #logging.info("Downloading from URL: %s\n", str(url))
    resp = requests.get(url, headers=auth_cacher_headers)
    return breakout_resp(resp)

def get_mwoffliner_request_headers(): # non-auth headers
    headers = {}
    headers['User-Agent'] = 'MWOffliner/HEAD (info@iiab.me)'
    headers['Cookie'] = ''
    headers['Connection'] = 'close'
    return headers

def respond_json(data_dict):
    outp = json.dumps(data_dict)
    status_code = '200'
    headers = [('Content-type', 'application/json; charset=utf-8')]
    return status_code, headers, outp.encode()

def respond_403():
    headers = [('Content-type', 'text/html; charset=UTF-8')]
    status_code = '403'
    body = b''
    return status_code, headers, body

def respond_404(reason, path):
    print("Skipping " + reason + " Page: " + str(path))
    # REWRITE  send_response(404)
    # REWRITE  send_header('Content-type', 'text/html')
    # REWRITE  end_headers()
    # REWRITE  wfile.write(b'Unknown Page')
    headers = [('Content-type', 'text/html; charset=UTF-8')]
    status_code = '404'
    body = b'Unknown Page'
    return status_code, headers, body

def respond_rest_404(reason, path):
    print("Skipping " + reason + " Page: " + str(path))
    # REWRITE  send_response(404)
    # REWRITE  send_header('Content-type', 'text/html')
    # REWRITE  end_headers()
    # REWRITE  wfile.write(b'Unknown Page')
    headers = [('Content-type', 'application/json')]
    status_code = '404'
    bpath = str.encode(path)
    body = b'{"errorKey":"rest-nonexistent-title",'
    body += b'"messageTranslations":{"en":"The specified page (' + bpath
    body += b') does not exist"},"httpCode":404,"httpReason":"Not Found"}'
    return status_code, headers, body

def respond_action_no_page(path):
    print("Skipping Page: " + str(path))
    # REWRITE  send_response(404)
    # REWRITE  send_header('Content-type', 'text/html')
    # REWRITE  end_headers()
    # REWRITE  wfile.write(b'Unknown Page')
    headers = [('Content-type', 'application/json')]
    status_code = '200'
    bpath = str.encode(path)
    body = b'{"error":{"code":"missingtitle","info":"The page you specified does not exist."},"servedby":"mdwiki-cacher"}'
    return status_code, headers, body

def respond_modules_no_page(path): # not used as breaks mwoffliner
    print("Skipping Page: " + str(path))
    # REWRITE  send_response(404)
    # REWRITE  send_header('Content-type', 'text/html')
    # REWRITE  end_headers()
    # REWRITE  wfile.write(b'Unknown Page')
    headers = [('Content-type', 'application/json')]
    status_code = '200'
    bpath = str.encode(path)
    body = b'{"error":{"code":"missingtitle","info":"The page you specified does not exist."},"servedby":"mdwiki-cacher"}'
    return status_code, headers, body

def respond_redirects_no_page(page, path): # not used as breaks mwoffliner
    print("Skipping Page: " + str(path))
    # REWRITE  send_response(404)
    # REWRITE  send_header('Content-type', 'text/html')
    # REWRITE  end_headers()
    # REWRITE  wfile.write(b'Unknown Page')
    headers = [('Content-type', 'application/json')]
    status_code = '200'
    bpath = str.encode(path)
    body = b'{"error":{"code":"missingtitle","info":"The page you specified does not exist."},"servedby":"mdwiki-cacher"}'
    body = b'{"batchcomplete":true,"query":{"pages":[{"ns":0,"title":"'
    body += page.encode(encoding="utf-8")
    body += b'","missing":true}]},"limits":{"redirects":5000}}'
    return status_code, headers, body

def start_response( resp):
    # REWRITE  send_response(resp.status_code)
    # REWRITE  send_header('Content-type', resp.headers['content-type'])
    #if 'content-length' in resp.headers:
    #    # REWRITE  send_header('content-length', resp.headers['content-length'])
    # REWRITE  end_headers()
    pass

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

def do_nonwiki(path, environ):
    # all special non-wiki requests come here
    global VERBOSE
    status = '200 OK'
    response_headers = [('Content-type', 'text/plain')]
    if path == nonwiki_url + 'status':
        response_body = get_cacher_stat(environ)
    elif path == nonwiki_url + 'lists/mdwikimed.tsv':
        with open(article_list, 'rb') as f:
            response_body = f.read()
    elif path == nonwiki_url + 'commands/read-data':
        try:
            init()
            response_body = b'OK'
        except:
            response_body = b'Init Failed'
    elif path == nonwiki_url + 'commands/get-redirects':
        return respond_json(mdwiki_redirects)
    elif path == nonwiki_url + 'commands/set-verbose-on':
        VERBOSE = True
        response_body = b'Verbose turned ON'
    elif path == nonwiki_url + 'commands/set-verbose-off':
        VERBOSE = False
        response_body = b'Verbose turned OFF'
    else:
        response_body = b'???'
    return status, response_headers, response_body

def get_cacher_stat(environ):
    response_body = 'MdWiki Cacher Version: ' + VERSION + '\n'
    response_body += 'MDWiki Cache Refresh History:\n'
    response_body += read_file_tail('mdwiki_cache-refresh-hist.txt')
    response_body += 'ENWP Cache Refresh History:\n'
    response_body += read_file_tail('enwp_cache-refresh-hist.txt')

    response_body += '\nArticle Lists Refresh History:\n'
    hist = read_file_list('data/mdwiki-list.log')
    hist.reverse()
    for i in hist:
        response_body += i + '\n'
        if 'List Creation Succeeded' in i:
            break

    response_body += '\nZim Farm (mdwiki) - '
    stat =  get_zimfarm_stat('mdwiki')
    response_body += stat['most_recent_task']['updated_at'] + ': ' + stat['most_recent_task']['status'] +'\n'
    response_body += 'Zim Farm (mdwiki_app) - '
    stat =  get_zimfarm_stat('mdwiki_app')
    response_body += stat['most_recent_task']['updated_at'] + ': ' + stat['most_recent_task']['status'] +'\n'

    response_body += '\nRecently Failed Requests:\n'
    response_body += '(Ignore if have been fixed.)\n'
    response_body += read_file('failed_mdwiki_urls.txt')


    # don't really need env
    #env = '\nEnvironment:\n' + dump(environ)
    #response_body += env
    return response_body.encode()

def get_enwp_page_list():
    global enwp_list
    #mdwiki_redirects = read_json_file('data/mdwiki_redirects.json')
    try:
        enwp_list = read_file_list('data/enwp.tsv')
    except Exception as error:
        print(error)
        print('Failed to read enwp.tsv. Exiting.')
        sys.exit(1)

def get_mdwiki_page_list():
    global mdwiki_list
    try:
        mdwiki_list = read_file_list('data/mdwiki.tsv')
    except Exception as error:
        print(error)
        print('Failed to read mdwiki.tsv. Exiting.')
        sys.exit(1)

def get_mdwiki_redirect_lists():
    # redirect.json
    #   rd_from_id
    #   rd_to_namespace
    #   rd_to_title_hex
    #   rd_from_name_hex
    global mdwiki_redirects
    global mdwiki_redirect_list
    global mdwiki_rd_lookup
    mdwiki_redirects = read_json_file('data/mdwiki_redirects.json')
    mdwiki_redirect_list = mdwiki_redirects['list']
    mdwiki_rd_lookup = mdwiki_redirects['lookup']

def log_request(req_uri, environ):
    print(f"GET request, Path: {str(req_uri)} \n")
    # print(f"GET request, Path: {str(req_uri)} \nHeaders:\n{str(environ)}\n")

def init():
    print('Starting httpd...\n')
    #print('Getting page and redirect lists...\n')
    #get_mdwiki_page_list()
    #get_mdwiki_redirect_lists()
    #get_enwp_page_list()
    print('Mdwiki cache ready\n')

# initialize lists
init()
