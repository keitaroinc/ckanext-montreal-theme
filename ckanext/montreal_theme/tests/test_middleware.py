"""Tests for the query-string sanitiser.

The bad-input cases are taken verbatim from Cloud Error Reporting for
amplus-data, where they surfaced as Solr ``SyntaxError`` at ERROR level.
"""

import pytest

from ckanext.montreal_theme.middleware import (
    DropInvalidSearchParams,
    sanitize_query_string,
)


@pytest.mark.parametrize('query_string', [
    # Facets CKAN core sends.
    'tags=Photographie&tags=Ville-Marie',
    'res_format=XLS&license_id=cc-by',
    'organization=ville-de-montreal&groups=infrastructures',
    # Free-text search, including the values that used to break the parser.
    'q=311+Montr%C3%A9al',
    'q=%3Aservice',
    'q=%29%22',
    # Sort and pagination.
    'q=eau&sort=score+desc%2C+metadata_modified+desc&page=2',
    # Underscore-prefixed facet limits, skipped by CKAN before fq is built.
    '_tags_limit=0&_groups_limit=0&_res_format_limit=0',
    # Extension extras, also skipped by CKAN.
    'ext_bbox=-73.9%2C45.4%2C-73.4%2C45.7',
    # Dotted and hyphenated names are legal Solr fields.
    'vocab_theme=transport&extras_custom-field=1',
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


def test_values_are_never_inspected():
    """Only the name decides; a value may contain any Solr metacharacter."""
    query_string = 'q=%29%3A%22%7B%21xjoin%7D'
    assert sanitize_query_string(query_string) == query_string


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
