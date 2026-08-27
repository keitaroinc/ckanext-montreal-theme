"""Tests for the footer's language-switch links.

``footer.html`` used to build them with CKAN's ``url_for``::

    {% url_for h.current_url(), locale='en' %}

``h.current_url()`` returns the request path plus query string, but
``url_for`` hands its first argument to ``flask.url_for`` as an *endpoint
name* and only treats it as a path once that raises ``BuildError``::

    # ckan/lib/helpers.py, _url_for_flask
    try:
        my_url = _flask_default_url_for(*args, **kw)
    except FlaskRouteBuildError:
        # Check if this a relative path
        if len(args) and args[0].startswith('/'):
            my_url = args[0]

Flask resolves an endpoint's blueprint by splitting on ``.`` recursively, one
frame per dot::

    # flask/helpers.py:639
    out.extend(_split_blueprint_path(name.rpartition(".")[0]))

so a request carrying enough dots raises ``RecursionError`` before the
``except FlaskRouteBuildError`` fallback is ever reached. The footer renders
on every page, and also inside CKAN's error handler, so one request could
500 a page and then 500 its own error page.

Seen in production on montreal-prod: a path-traversal scanner sent 46
parameters of ``///////../../../../../../../../etc/passwd`` in a single
5,097-byte query string, roughly 780 dots, producing
``RecursionError: maximum recursion depth exceeded``.

CKAN core's own ``snippets/language_selector.html`` uses the same idiom, so
this is an upstream pattern rather than something unique to this theme.

With ``ckan.root_path`` unset, which is the case here, ``url_for(path,
locale=X)`` reduces to ``'/' + X + path``, so the templates now build that
directly and never enter endpoint resolution.
"""
import pytest


# Shaped after the request that caused the production incident.
TRAVERSAL = "///////../../../../../../../../etc/passwd"
DOTTED_QUERY = "&".join("p{0}={1}".format(i, TRAVERSAL) for i in range(46))


@pytest.mark.usefixtures("with_plugins")
def test_dotted_query_string_does_not_blow_the_recursion_limit(app):
    """A query string full of dots must not 500 the page."""
    response = app.get("/?" + DOTTED_QUERY, status="*")

    assert response.status_code != 500


@pytest.mark.usefixtures("with_plugins")
def test_dotted_query_string_does_not_break_the_error_page(app):
    """The same input on a URL that 404s must still render the error page."""
    response = app.get("/does-not-exist?" + DOTTED_QUERY, status="*")

    assert response.status_code == 404


@pytest.mark.usefixtures("with_plugins")
def test_language_links_keep_their_previous_target(app):
    """The rewrite must produce the same hrefs the old url_for call did."""
    response = app.get("/dataset?q=test", status="*")

    # '&' is escaped by Jinja's autoescaping, exactly as it was before.
    assert "/en/dataset?q=test" in response.body
