# constants

VERSION = '1.0.1'

mdwiki_domain = 'https://mdwiki.org'
enwp_domain = 'https://en.wikipedia.org'

cache_dir = '/srv/cache/'
mdwiki_api_cache  = cache_dir + 'mdwiki_api'
mdwiki_wiki_cache  = cache_dir + 'mdwiki_wiki'
mdwiki_other_cache  = cache_dir + 'mdwiki_other'
# mdwiki_rest_cache  = cache_dir + 'mdwiki_rest' # put in api cache
enwp_api_cache = cache_dir + 'enwp_api'
enwp_other_cache = cache_dir + 'enwp_other'

user_agent = 'MDWikiCacher/' + VERSION + ' (https://mdwiki.wmcloud.org/nonwiki/status)'
cacher_headers =  {'User-Agent': user_agent} # not auth_cacher_headers

# paste these
# mdwiki_api_session = CachedSession(CONST.mdwiki_api_cache, backend='filesystem')
# mdwiki_wiki_session = CachedSession(CONST.mdwiki_wiki_cache, backend='filesystem')
# mdwiki_other_session = CachedSession(CONST.mdwiki_other_cache, backend='filesystem')
# mdwiki_rest_session = CachedSession(CONST.mdwiki_rest_cache, backend='filesystem')
# enwp_api_session = CachedSession(CONST.enwp_api_cache, backend='filesystem')
# enwp_other_session = CachedSession(CONST.enwp_api_other_cache, backend='filesystem')
# uncached_session = CachedSession(expire_after=DO_NOT_CACHE)

modules_query = '/w/api.php?action=parse&format=json&prop=modules%7Cjsconfigvars%7Cheadhtml&page='
videdit_page = '/w/api.php?action=visualeditor&mobileformat=html&format=json&paction=parse&page='
redirect_query = '/w/api.php?action=query&format=json&prop=redirects%7Crevisions%7Cpageimages&rdlimit=max&rdnamespace=0%7C3000%7C3002&redirects=true&formatversion=2&titles='
last_revision_query = '/w/api.php?action=query&prop=revisions&rvprop=timestamp&format=json&formatversion=2&redirects=true&titles='

rest_page = '/w/rest.php/v1/page/'
wiki_page = '/wiki/'
