"""Tests for the query-string sanitiser.

The bad-input cases are taken verbatim from Cloud Error Reporting for
amplus-data, where they surfaced as Solr ``SyntaxError`` at ERROR level.
Every Solr verdict asserted here was checked against a live Solr 9 core
before being written down.
"""

import pytest

from ckanext.montreal_theme.middleware import (
    DropInvalidSearchParams,
    breaks_quoted_term,
    is_safe_param,
    sanitize_query_string,
)


@pytest.mark.parametrize('query_string', [
    # Facets CKAN core sends.
    'tags=Photographie&tags=Ville-Marie',
    'res_format=XLS&license_id=cc-by',
    'organization=ville-de-montreal&groups=infrastructures',
    # Free-text search. Values of q are never inspected: see
    # test_q_is_left_alone_even_when_solr_will_reject_it.
    'q=311+Montr%C3%A9al',
    'q=%3Aservice',
    'q=%29%22',
    # Sort and pagination.
    'q=eau&sort=score+desc%2C+metadata_modified+desc&page=2',
    'sort=metadata_modified+desc',
    'sort=title_string+asc%2C+score+desc',
    # Solr is case-insensitive about the direction (verified 200), so
    # rejecting these would be a false positive.
    'sort=score+DESC',
    'sort=metadata_modified+Asc',
    # Underscore-prefixed facet limits, skipped by CKAN before fq is built.
    '_tags_limit=0&_groups_limit=0&_res_format_limit=0',
    # Extension extras. CKAN skips these on /dataset but not on
    # /feeds/custom.atom, so only the name shape keeps them.
    'ext_bbox=-73.9%2C45.4%2C-73.4%2C45.7',
    # Dotted and hyphenated names are legal Solr fields.
    'vocab_theme=transport&extras_custom-field=1',
    # Accented facet names produce a valid Solr filter (verified 200).
    'extras_th%C3%A8me=eau',
    'extras_cat%C3%A9gorie=Environnement&tags=eau',
    # Lucene only treats the all-caps spellings as operators (verified 200).
    'and=x&or=y&And=z&TO=w',
    # Metacharacters inside a quoted term are harmless (verified 200).
    'tags=%28eau%29&res_format=a%3Ab&notes=%7B%21xjoin%7D',
    'tags=x%5C%5C',
    'tags=%5C%22',
    '',
])
def test_legitimate_query_strings_are_untouched(query_string):
    assert sanitize_query_string(query_string) == query_string


@pytest.mark.parametrize('query_string,expected', [
    # Tenable Web App Scanner fuzzing iaea-prod, 2026-08-11.
    ('%29=tenable_wasscan_name_fuzz', ''),
    ('%22%27%60--=tenable_wasscan_name_fuzz', ''),
    # Entity-mangled URLs from crawlers hitting montreal-prod.
    ('=311+Montr%C3%A9al', ''),
    ('%3ARuisseaux=1', ''),
    # A bad parameter must not take the good ones with it.
    ('tags=eau&%29=x&res_format=CSV', 'tags=eau&res_format=CSV'),
    ('%29=x&q=montreal', 'q=montreal'),
])
def test_invalid_parameter_names_are_dropped(query_string, expected):
    assert sanitize_query_string(query_string) == expected


@pytest.mark.parametrize('name', ['AND', 'OR', 'NOT'])
def test_uppercase_lucene_operators_are_dropped(name):
    """?AND=x builds fq ' AND:"x"', which Solr rejects (verified 400)."""
    assert sanitize_query_string('%s=x' % name) == ''
    assert sanitize_query_string('tags=eau&%s=x' % name) == 'tags=eau'


@pytest.mark.parametrize('query_string,expected', [
    # ext_ names DO reach fq on /feeds/custom.atom, which unlike /dataset
    # has no try/except around package_search: fq 'ext_):"x"' is a 500.
    ('ext_%29=x', ''),
    ('ext_%22=x', ''),
    ('ext_bbox=1&ext_%29=x', 'ext_bbox=1'),
])
def test_ext_prefixed_names_are_validated_too(query_string, expected):
    assert sanitize_query_string(query_string) == expected


@pytest.mark.parametrize('query_string', [
    # CKAN skips underscore names on every view that builds fq, so their
    # names can never reach the parser and must survive as sent.
    '_tags_limit=0',
    '_%29=x',
    '_=%22',
])
def test_underscore_names_are_always_kept(query_string):
    assert sanitize_query_string(query_string) == query_string


@pytest.mark.parametrize('value,unsafe', [
    ('eau', False),
    ('(eau)', False),
    ('a:b', False),
    ('{!xjoin}', False),
    ('x\\\\', False),   # escaped backslash: verified 200
    ('\\"', False),     # escaped quote: verified 200
    ('"', True),        # verified 400
    ('a"b', True),      # verified 400
    ('x\\', True),      # trailing backslash eats the closing quote: 400
    ('x\\\\\\', True),  # odd run of backslashes, same problem
])
def test_breaks_quoted_term_matches_solr(value, unsafe):
    assert breaks_quoted_term(value) is unsafe


@pytest.mark.parametrize('query_string,expected', [
    # A bare quote in a facet value closes the term early: fq ' tags:"""'.
    ('tags=%22', ''),
    ('tags=a%22b', ''),
    ('tags=eau&res_format=%22', 'tags=eau'),
    # A trailing backslash escapes the closing quote.
    ('tags=x%5C', ''),
])
def test_values_that_break_the_quoted_term_are_dropped(query_string, expected):
    assert sanitize_query_string(query_string) == expected


def test_q_is_left_alone_even_when_solr_will_reject_it():
    """q is free text handed to a full query parser, not a field name.

    CKAN skips dismax whenever q contains a colon, so 'q=:service' reaches
    the lucene parser and still logs at ERROR. Validating it would mean
    reimplementing the Lucene grammar in middleware and risks discarding a
    real search, so q is out of this middleware's remit by design.
    """
    for query_string in ['q=%3Aservice', 'q=a%3Ab%3Ac', 'q=eau%3A', 'q=%22%29']:
        assert sanitize_query_string(query_string) == query_string


@pytest.mark.parametrize('query_string,expected', [
    # Solr: Can't determine a Sort Order in sort spec ')'. Dropping the
    # param falls back to CKAN's default sort instead of a 400 page.
    ('sort=%29', ''),
    ('sort=score', ''),
    ('sort=title_string+sideways', ''),
    ('sort=score+desc%2C+%29', ''),
    ('q=eau&sort=%29', 'q=eau'),
])
def test_unparseable_sort_is_dropped(query_string, expected):
    assert sanitize_query_string(query_string) == expected


def test_page_is_never_inspected():
    """CKAN validates page itself; it never reaches fq or sort."""
    assert sanitize_query_string('page=%22') == 'page=%22'


def test_pairs_without_a_value_survive_name_validation():
    assert is_safe_param('tags') is True
    assert is_safe_param('%29') is False


def test_middleware_rewrites_environ():
    captured = {}

    def app(environ, start_response):
        captured['qs'] = environ['QUERY_STRING']
        return []

    environ = {'QUERY_STRING': 'tags=eau&%29=x'}
    DropInvalidSearchParams(app)(environ, lambda *a: None)

    assert captured['qs'] == 'tags=eau'
    assert environ['QUERY_STRING'] == 'tags=eau'


def test_middleware_leaves_clean_requests_alone():
    environ = {'QUERY_STRING': 'tags=eau'}
    DropInvalidSearchParams(lambda e, s: [])(environ, lambda *a: None)
    assert environ['QUERY_STRING'] == 'tags=eau'


def test_middleware_logs_what_it_drops(caplog):
    """A dropped pair must be diagnosable; it is invisible otherwise."""
    import logging
    with caplog.at_level(logging.DEBUG, logger='ckanext.montreal_theme.middleware'):
        DropInvalidSearchParams(lambda e, s: [])(
            {'QUERY_STRING': 'tags=eau&%29=x'}, lambda *a: None)
    assert any('%29=x' in r.getMessage() for r in caplog.records)


def test_make_middleware_returns_the_flask_app():
    """CKAN chains IMiddleware plugins: app = plugin.make_middleware(app, ...).

    Returning a bare WSGI wrapper hands the next plugin in the loop
    something with no Flask API on it, so core `tracking` -- which calls
    app.after_request -- dies at startup if it loads after this plugin.
    """
    from flask import Flask

    from ckanext.montreal_theme.plugin import MontrealThemePlugin

    flask_app = Flask(__name__)
    # Unbound call: exercises the method without the plugin registry.
    app = MontrealThemePlugin.make_middleware(None, flask_app, {})

    assert app is flask_app
    # The next plugin in CKAN's loop must still see a usable Flask app.
    app.after_request(lambda response: response)

    # ...and the sanitiser is still in the WSGI chain.
    @flask_app.route('/dataset')
    def dataset():
        from flask import request
        return '|'.join(sorted(request.args.keys()))

    with flask_app.test_client() as client:
        assert client.get('/dataset?tags=eau&%29=x').data == b'tags'
