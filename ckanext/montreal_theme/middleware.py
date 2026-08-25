"""Drop query-string parameters that would corrupt CKAN's Solr filter query.

Three views fold unrecognised query parameters straight into ``fq`` with no
validation of either side of the pair::

    # ckan/views/dataset.py:193  (also reached from group.py via
    # _get_search_details, so /organization and /group read pages too)
    for (param, value) in request.args.items(multi=True):
        if param not in ['q', 'page', 'sort'] \
                and len(value) and not param.startswith('_'):
            if not param.startswith('ext_'):
                fq += ' %s:"%s"' % (param, value)

    # ckan/views/feed.py:374  -- note: no ext_ skip here
    for (param, value) in request.args.items():
        if param not in ['q', 'page', 'sort'] \
                and len(value) and not param.startswith('_'):
            fq += '%s:"%s"' % (param, value)

So a request for ``?)=x`` builds the filter ``):"x"`` and Solr's lucene
parser rejects it::

    org.apache.solr.search.SyntaxError: Cannot parse '):"x" -dataset_type:harvest'

On ``/dataset`` CKAN catches that and logs at ERROR, so any client can fill
Cloud Error Reporting with noise. On ``/feeds/custom.atom`` there is no
try/except around ``package_search`` at all, so the same input is a 500.
Those lines are identical in 2.9.10, 2.11.5 and current upstream master, so
no CKAN upgrade removes them.

Stripping the offending pairs before routing keeps ``fq`` well formed without
patching CKAN or trying to unpick the filter query after it has been built.

What is checked, and why only this much:

* **Names** must be usable as a Solr field, and must not be one of Lucene's
  three all-caps boolean operators. Only the exact spellings ``AND``, ``OR``
  and ``NOT`` are keywords; ``and``, ``And`` and ``TO`` all parse fine.
* **Values** are checked for one thing only: whether they would terminate the
  quoted term they get wrapped in. Parentheses, colons and even ``{!...}``
  are inert inside ``field:"..."``; an unescaped ``"`` or a dangling
  backslash is not.
* **``sort``** is checked against Solr's ``field asc|desc`` grammar. Dropping
  a malformed one falls back to CKAN's default sort instead of a 400 page.
* **``q``** is deliberately left alone. It is free text handed to a full
  query parser -- CKAN skips dismax whenever ``q`` contains a colon, so
  ``?q=:service`` still reaches the lucene parser and still logs at ERROR.
  Validating that would mean reimplementing the Lucene grammar here, and a
  false positive would silently discard someone's search. Fixing it belongs
  in ``package_search`` (an ``edismax`` fallback), not in middleware.
* **``page``** and underscore-prefixed names are never inspected: CKAN
  validates ``page`` itself, and it skips ``_*`` on every view that builds
  ``fq``, so neither can reach a parser.

Every Solr verdict above was checked against a live Solr 9 core; the cases
are pinned in ``tests/test_middleware.py``.
"""

import logging
import re
from urllib.parse import unquote_plus

log = logging.getLogger(__name__)

#: A name usable as a Solr field: leading letter, then word characters, dots
#: or hyphens. Unicode-aware on purpose -- ``extras_thème`` is a facet a
#: French-language site really sends, and it yields a valid Solr filter.
VALID_PARAM_NAME = re.compile(r'^[^\W\d_][\w.-]*$')

#: Lucene's boolean operators. Only these exact spellings are keywords, so a
#: field named ``and`` or ``TO`` is fine while ``AND`` is a parse error.
LUCENE_OPERATORS = frozenset(('AND', 'OR', 'NOT'))

#: ``field asc|desc``, comma-separated. Solr rejects a bare field name.
VALID_SORT = re.compile(
    r'^[^\W\d_][\w.-]*\s+(asc|desc)$', re.IGNORECASE)

#: Parameters the views above handle themselves instead of folding into fq.
#: ``q`` and ``page`` are passed through untouched; see the module docstring.
PASSTHROUGH_PARAMS = frozenset(('q', 'page'))


def breaks_quoted_term(value):
    """Whether ``value`` would end the quotes early in ``field:"<value>"``.

    A backslash escapes whatever follows it, so the only two ways out of the
    term are an unescaped ``"`` and a trailing backslash that goes on to
    escape the closing quote.
    """
    i = 0
    length = len(value)
    while i < length:
        if value[i] == '\\':
            i += 2
            continue
        if value[i] == '"':
            return True
        i += 1
    # The last backslash had nothing to escape, so it will eat the closing
    # quote instead.
    return i > length


def is_safe_param(pair):
    """Whether a raw ``name=value`` pair may stay in the query string."""
    if not pair:
        return False

    raw_name, _, raw_value = pair.partition('=')
    name = unquote_plus(raw_name)

    # CKAN skips these before building fq, so they cannot reach a parser.
    if name.startswith('_') or name in PASSTHROUGH_PARAMS:
        return True

    if name == 'sort':
        value = unquote_plus(raw_value)
        return all(VALID_SORT.match(spec.strip())
                   for spec in value.split(','))

    if not VALID_PARAM_NAME.match(name) or name in LUCENE_OPERATORS:
        return False

    return not breaks_quoted_term(unquote_plus(raw_value))


def sanitize_query_string(query_string):
    """Return ``query_string`` without pairs that would corrupt ``fq``."""
    if not query_string:
        return query_string
    kept = [pair for pair in query_string.split('&') if is_safe_param(pair)]
    return '&'.join(kept)


class DropInvalidSearchParams(object):
    """WSGI middleware that sanitises QUERY_STRING before CKAN routes."""

    def __init__(self, app):
        self.app = app

    def __call__(self, environ, start_response):
        query_string = environ.get('QUERY_STRING', '')
        sanitized = sanitize_query_string(query_string)
        if sanitized != query_string:
            # Without this a working filter that merely trips the name rules
            # would vanish with no way to find out why.
            dropped = [pair for pair in query_string.split('&')
                       if not is_safe_param(pair)]
            log.debug(
                'Dropped unusable search params from %s: %s',
                environ.get('PATH_INFO', '?'), '&'.join(dropped))
            environ['QUERY_STRING'] = sanitized
        return self.app(environ, start_response)
