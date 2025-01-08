import sys
import time
from datetime import timedelta
import requests
import json
import base64
# import pymysql.cursors
from urllib.parse import urljoin, urldefrag, urlparse, parse_qs
# from requests_cache import CachedSession
from common import * # functions common to several modules
import constants as CONST

qhost = 'https://en.wikipedia.org'
qhost = 'https://mdwiki.wmcloud.org'

q = '/w/api.php?action=query&format=json&prop=redirects%7Crevisions%7Ccoordinates&rdlimit=max&rdnamespace=0%7C3000%7C3002&redirects=true&formatversion=2&titles=Amikacin%7CAmiloride%7CAminocaproic_acid%7CAminolevulinic_acid%7CAmiodarone%7CAmisulpride%7CAmitriptyline%7CAmivantamab%7CAmlodipine%7CAmlodipine%2Fbenazepril%7CAmnesia%7CAmniotic_fluid_embolism%7CAmodiaquine%7CAmodiaquine%2Fsulfadoxine%2Fpyrimethamine%7CAmoebiasis%7CAmoebic_brain_abscess%7CAmoebic_encephalitis%7CAmoebic_liver_abscess%7CAmorolfine%7CAmoxapine%7CAmoxicillin%7CAmoxicillin%2Fclavulanic_acid%7CAmphetamine%7CAmphetamine_dependence%7CAmphotericin_B%7CAmpicillin%7CAmpicillin%2Fflucloxacillin%7CAmpicillin%2Fsulbactam%7CAmyl_nitrite%7CAmyloidosis%7CAmyotrophic_lateral_sclerosis%7CAmyotrophic_lateral_sclerosis_research%7CAmyotrophy%7CAnacaulase%7CAnaerobic_organism%7CAnagen_effluvium%7CAnagrelide%7CAnakinra%7CAnal_cancer%7CAnal_fissure%7CAnal_fistula%7CAnaphylaxis%7CAnaplasma_phagocytophilum%7CAnaplastic_astrocytoma%7CAnaplastic_oligodendroglioma%7CAnaplastic_thyroid_cancer%7CAnastrozole%7CAnatomical_Therapeutic_Chemical_Classification_System%7CAncylostoma_duodenale%7CAncylostomiasis&colimit=max'
q1 = qhost + q
q2 = q1 + '&rdcontinue=Amoxicillin|26588103'
q3 = q1 + '&rdcontinue=Anastrozole|46355933'

r1 = json.loads(requests.get(q1, headers=CONST.cacher_headers).content)
r2 = json.loads(requests.get(q2, headers=CONST.cacher_headers).content)
r3 = json.loads(requests.get(q3, headers=CONST.cacher_headers).content)

p1 = r1['query']['pages']
p2 = r2['query']['pages']
p3 = r3['query']['pages']

for i in range(0, 50):
    p1rev = p1[i].get('revisions')
    p2rev = p2[i].get('revisions')
    p3rev = p3[i].get('revisions')
    if p1rev != p2rev:
        print(i)
    if p2rev != p3rev:
        print(i)

for i in range(0, 50):
    p1red = p1[i].get('redirects')
    p2red = p2[i].get('redirects')
    p3red = p3[i].get('redirects')
    if p1red != p2red:
        print(i)
    if p2red != p3red:
        print(i)

i = 0
for p in p1:
    i +=1
    pageid = p.get('pageid')
    if pageid:
        print(i,pageid)

page_redir = {}
page_redir = p1

for i in range(0, 50):
    if 'redirects' in p2[i]:
        print ('updating redir', i)
        print (p1[i]['title'], len(p1[i]['redirects']))
        if 'redirects' in page_redir[i]:
            for j in range(0, len(p2[i]['redirects'])):
                if p2[i]['redirects'][j] not in page_redir[i]['redirects']:
                    page_redir[i]['redirects'].append(p2[i]['redirects'])
        else:
            page_redir[i]['redirects'] = (p2[i]['redirects'])

for i in range(0, 50):
    print (i, p1[i]['title'], len(p1[i].get('redirects',[])), len(p2[i].get('redirects',[])), len(p3[i].get('redirects',[])))

    p1red = p1[i].get('redirects')
    p2red = p2[i].get('redirects')
    p3red = p3[i].get('redirects')
    if p1red != p2red:
        print(i)
    if p2red != p3red:
        print(i)

>>> r3.keys()
dict_keys(['batchcomplete', 'warnings', 'query', 'limits'])

>>> r3['batchcomplete']
True

>>> r1['warnings']
{'redirects': {'warnings': 'Unrecognized values for parameter "rdnamespace": 3000, 3002'}}
>>> r2['warnings']
{'redirects': {'warnings': 'Unrecognized values for parameter "rdnamespace": 3000, 3002'}}
>>> r3['warnings']
{'redirects': {'warnings': 'Unrecognized values for parameter "rdnamespace": 3000, 3002'}}

>>> r1['limits']
{'redirects': 500, 'coordinates': 500}
>>> r2['limits']
{'redirects': 500, 'coordinates': 500}
>>> r3['limits']
{'redirects': 500, 'coordinates': 500}

>>> r1['query'].keys()
dict_keys(['normalized', 'redirects', 'pages'])
>>> r2['query'].keys()
dict_keys(['normalized', 'redirects', 'pages'])
>>> r3['query'].keys()
dict_keys(['normalized', 'redirects', 'pages'])

>>> r1['query']['normalized'] == r2['query']['normalized']
True
>>> r1['query']['normalized'] == r3['query']['normalized']
True
>>> r1['query']['redirects'] == r3['query']['redirects']
True
>>> r1['query']['redirects'] == r2['query']['redirects']
True

return_batch = {'batchcomplete': True, 'warnings': {}, 'query': {}, 'limits': {}}



########################

q = '/w/api.php?action=query&format=json&prop=redirects%7Crevisions%7Cpageimages%7Ccoordinates&rdlimit=max&rdnamespace=0%7C3000%7C3002&redirects=true&formatversion=2&titles='
for i in range(100, 148):
    q += enwp_list[i] + '%7C'
q += 'Gout'

r = requests.get(u + q, headers=CONST.cacher_headers)
d = json.loads(r.content)
q2 = q + '&rdcontinue=' + d['continue']['rdcontinue']





args = parse_qs(urlparse(path).query)
titles = args['titles'][0].split('|')
mdwiki_article_list = []
enwp_article_list = []
for title in titles: # split out titles for subsequent processing
    if title in mdwiki_list:
        mdwiki_article_list.append(title)
    elif title in enwp_list:
        enwp_article_list.append(title)
# get enwp article redirects if any
enwp_query = calc_redir_query(enwp_article_list)
mdwiki_query = calc_redir_query(mdwiki_article_list)
if enwp_query:
    resp = requests.get(CONST.enwp_domain + enwp_query, headers=CONST.cacher_headers)
    enwp_batch_resp = json.loads(resp.content)
else:
    enwp_batch_resp = {}
if mdwiki_query:
    resp = requests.get(CONST.mdwiki_domain + mdwiki_query, headers=CONST.cacher_headers)
    mdwiki_batch_resp = json.loads(resp.content)
else:
    mdwiki_batch_resp = {}
batch_resp = mdwiki_batch_resp | enwp_batch_resp



args = parse_qs(urlparse(path).query)
titles = args['titles'][0].split('|')
base_query = path.split('&titles=')[0] + '&titles='
more_rd_query = '/w/api.php?action=query&format=json&prop=redirects&rdlimit=max&rdnamespace=0&redirects=true&titles='

pages_resp = {}
title_page_ids = {}
mdiwki_article_list = []
enwp_article_list = []
for title in titles: # split out titles for subsequent processing
    if title in mdwiki_list:
        mdiwki_article_list.append(title)
    elif title in enwp_list:
        enwp_article_list.append(title)
# get enwp article redirects if any
query = calc_redir_query(enwp_article_list)
if query:
    resp = requests.get(CONST.enwp_domain + query, headers=CONST.cacher_headers)
    batch_resp = json.loads(resp.content)
else:
    batch_resp = calc_empty_batch_resp()

for title in mdiwki_article_list:
    # we are missing to id
    # query = CONST.rest_page + title + '/bare'
    # resp = requests.get(CONST.mdwiki_domain + query, headers=CONST.cacher_headers)
    # page_meta = json.loads(resp.content)
    redirects = get_mdwiki_redirects(title) # all redirects for this title known to mdwiki
    # page_ns = redirects[0]['ns']
    page_dict = {"pageid":mdwiki_list[title]['pageid'],
                "ns":mdwiki_list[title]['ns'],
                "title":title,
                "redirects":redirects}

    batch_resp['query']['pages'].append(page_dict)

#!/usr/bin/env python3
import sys
import time
import requests
import json
import base64
# import pymysql.cursors
from urllib.parse import urljoin, urldefrag, urlparse, parse_qs
from requests_cache import CachedSession
from common import * # functions common to several modules

def read_list(name):
    with open(name) as f:
        txt = f.read()
    itemlist = txt.split('\n')
    return itemlist

mdwiki = 'mdwiki_en_all_maxi_2022-02.list'
enwp = 'wikipedia_en_medicine_maxi_2022-02.list'
bot = 'medicine.tsv'

mdwiki_list = read_list(mdwiki)
enwp_list = read_list(enwp)
bot_list = read_list(bot)
enwp_not_mdwiki = []

json_query = 'https://en.wikipedia.org/w/api.php?action=visualeditor&mobileformat=html&format=json&paction=parse&page='

parse_page = 'https://en.wikipedia.org/w/api.php?action=parse&format=json&prop=modules%7Cjsconfigvars%7Cheadhtml&page='
videdit_page = 'https://en.wikipedia.org/w/api.php?action=visualeditor&mobileformat=html&format=json&paction=parse&page='
wiki_page = 'https://en.wikipedia.org/wiki/'
get_page = 'https://en.wikipedia.org/w/index.php?redirect=no&title='

p1 = '1832_cholera_epidemic' # redirect
p2 = '1832_cholera_pandemic' # to this and then [or not anymore]
p3 = '1826–1837_cholera_pandemic' # to this

t1 = 'Stomach_ache'
t2 = 'Abdominal_pain'

for article in enwp_list:
    if article[0:2] != 'A/': # is it an article
        continue
    if article in mdwiki_list: # is it an mdwiki article or redirect
        continue
    # p = article[2:-1]
    enwp_not_mdwiki.append(article)
    # print(article)

for article in enwp_not_mdwiki:
    if article[0:2] == 'A/':
        p = article[2:-1]
        if article not in mdwiki_list:
            enwp_not_mdwiki.append(article)
            print(article)

a = requests.get(get_page + t1)
>>> 'Redirect page' in a.text
True
a2 = requests.get(get_page + t2)
>>> 'Redirect page' in a2.text
False

r = requests.get(parse_page + p1)
r2 = requests.get(videdit_page + p1)

r.headers
r2.headers
r.json()
r2.json()

h1p1 = requests.head(parse_page + p1)
h2p1 = requests.head(videdit_page + p1)

h1p2 = requests.head(parse_page + p2)
h2p2 = requests.head(videdit_page + p2)

h1p1.headers
h2p1.headers

h1p2.headers
h2p2.headers

# cause errors
h1p1.json()
h2p1.json()
h1p2.json()
h2p2.json()

headers = {}
headers['User-Agent'] = 'MWOffliner/HEAD (info@iiab.me)'
headers['Cookie'] = ''
headers['Connection'] = 'close'

# test cache with expiry
from requests_cache import CachedSession
import datetime
cache_db = 'expire-test-60' # need expiry on creation
session = CachedSession(cache_db, backend='sqlite', expire_after=60) # in seconds

url1  = 'https://mdwiki.org/wiki/Gout'
url2 = 'https://mdwiki.org/wiki/Heart'
url = 'http://iiab-ref/test/expire3.html'

r = session.get(url)

r.from_cache
r.expires
datetime.datetime.now()

r = session.get(url, expire_after=120)


# first try
from requests_cache import CachedSession
cache_db = 'expire-test'
session = CachedSession(cache_db, backend='sqlite')
session = CachedSession(cache_db, backend='sqlite', expire_after=60) # in seconds

url  = 'https://mdwiki.org/wiki/Gout'
url2 = 'https://mdwiki.org/wiki/Heart'
url3 = 'http://iiab-ref/test/expire3.html'

r = session.get(url)
r = session.get(url2)
r = session.get(url3)
r.from_cache
r.expires

def get_url(session, url):
    r = session.get(url)
    print(r.from_cache, r.expires)
    print(datetime.datetime.now())

# https://en.wikipedia.org/w/api.php?action=query&prop=redirects&titles=Cilazapril


for rd in mdwiki_redirects_hex:
    if rd['rd_to_namespace'] != 0: # skip if not in 0 namespace
        continue
    rd_from_title = bytearray.fromhex(rd['rd_from_name_hex']).decode()
    #print('hex: ' + rd['rd_from_name_hex'])
    # rd_from_title = decode_b64(rd['rd_from_name_hex'])
    #print('decoded: ' + rd_from_title)
    #print('hex2: ' + rd['rd_to_title_hex'])
    #rd_to_title = decode_b64(rd['rd_to_title_hex'])
    #print('decoded2: ' + rd_to_title)
    rd_to_title = bytearray.fromhex(rd['rd_to_title_hex']).decode()
    mdwiki_redirect_list.append(rd_from_title)
    if rd_to_title not in mdwiki_rd_lookup:
        mdwiki_rd_lookup[rd_to_title] = []
    mdwiki_rd_lookup[rd_to_title].append({'pageid': rd['rd_from_id'], 'ns': rd['rd_to_namespace'], 'title': rd_from_title})

# did Pandemic in Cuba get caches
u1 = ' https://mdwiki.wmcloud.org/w/api.php?action=visualeditor&mobileformat=html&format=json&paction=parse&page=COVID-19_pandemic_in_Cuba'
mdwiki_db  = 'mdwiki_api'
mdwiki_session  = CachedSession(mdwiki_db, backend='sqlite')
resp = mdwiki_session.get(u1)
