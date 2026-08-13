"""Drop query-string parameters whose names cannot be Solr field names.

CKAN's dataset search view folds every unrecognised query parameter straight
into the Solr filter query::

    # ckan/views/dataset.py
    for (param, value) in request.args.items(multi=True):
        if param not in ['q', 'page', 'sort'] \
                and len(value) and not param.startswith('_'):
            if not param.startswith('ext_'):
                fields.append((param, value))
                fq += ' %s:"%s"' % (param, value)

The parameter *name* is interpolated with no validation, so a request for
``?)=x`` builds the filter ``):"x"`` and Solr's lucene parser rejects it::

    org.apache.solr.search.SyntaxError: Cannot parse '):"x" -dataset_type:harvest'

CKAN catches that and logs it at ERROR level, which means any client can fill
Cloud Error Reporting with noise just by sending an oddly named parameter. The
line above is identical in 2.9.10, 2.11.5 and current upstream master, so no
CKAN upgrade removes it.

Stripping such parameters before routing keeps the filter query well formed
without patching CKAN or trying to unpick ``fq`` after it has been built. Only
the parameter name is inspected; values are left untouched, so search terms
still reach Solr exactly as typed.
"""

import re
from urllib.parse import unquote_plus

#: A name usable as a Solr field: leading letter, then word characters, dots
#: or hyphens. Matches every facet CKAN and our extensions actually send
#: (``tags``, ``res_format``, ``license_id``, ``organization``, ``vocab_*``).
VALID_PARAM_NAME = re.compile(r'^[A-Za-z][A-Za-z0-9_.-]*$')


def is_safe_param(pair):
    """Whether a raw ``name=value`` pair may stay in the query string.

    Parameters CKAN never forwards to ``fq`` are kept regardless: it skips
    anything starting with an underscore (facet limits such as
    ``_tags_limit``) and anything starting with ``ext_`` (extension extras
    such as ``ext_bbox``), so their names cannot reach the parser.
    """
    if not pair:
        return False
    name = unquote_plus(pair.split('=', 1)[0])
    if name.startswith('_') or name.startswith('ext_'):
        return True
    return bool(VALID_PARAM_NAME.match(name))


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
            environ['QUERY_STRING'] = sanitized
        return self.app(environ, start_response)
