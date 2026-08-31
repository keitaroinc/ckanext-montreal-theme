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

Flask resolves an endpoint's blueprint by splitting on ``.`` recursively,
one frame per dot::

    # flask/helpers.py:639
    out.extend(_split_blueprint_path(name.rpartition(".")[0]))

so a request carrying enough dots raises ``RecursionError`` before the
``except FlaskRouteBuildError`` fallback is reached. The footer renders on
every page, and also inside CKAN's error handler, so one request could 500 a
page and then 500 its own error page.

Seen on montreal-prod: a path-traversal scanner sent 46 parameters of
``///////../../../../../../../../etc/passwd`` in a single 5,097-byte query
string, roughly 780 dots, giving ``RecursionError: maximum recursion depth
exceeded``. Error group ``CLz38ozEwunOdw``, 133 events over 30 days.

The templates now build ``'/' + locale + h.current_url()`` directly. These
tests pin the equivalence that rewrite relies on, which is the part that
could silently drift: if CKAN ever changes where the locale goes, the
hardcoded prefix would be wrong and these fail.

They deliberately do not render a page. The theme's templates pull in
``pages`` and ``showcase`` endpoints that are not installed in the test
environment, so a full render fails for reasons unrelated to this fix.
"""
import pytest

from ckan.plugins import toolkit


# Shaped after the request that caused the production incident.
TRAVERSAL = "///////../../../../../../../../etc/passwd"
DOTTED_QUERY = "&".join("p{0}={1}".format(i, TRAVERSAL) for i in range(46))

PATHS = [
    "/",
    "/dataset",
    "/dataset?q=test",
    "/dataset?q=test&page=2",
    "/organization",
]


@pytest.mark.parametrize("locale", ["en", "fr"])
@pytest.mark.parametrize("path", PATHS)
def test_locale_prefix_matches_what_url_for_produced(app, path, locale):
    """The rewrite must yield exactly what the old url_for call did.

    ``ckan.root_path`` is unset on every deployment of this theme, so
    ``url_for(path, locale=X)`` reduces to ``'/' + X + path``.
    """
    with app.flask_app.test_request_context(path):
        via_url_for = toolkit.h.url_for(path, locale=locale)

    assert via_url_for == "/" + locale + path


@pytest.mark.parametrize("locale", ["en", "fr"])
def test_prefixing_current_url_does_not_duplicate_the_locale(app, locale):
    """Switching from /fr/... must give /en/..., not /en/fr/....

    CKAN's i18n middleware strips the locale into ``CKAN_LANG`` and leaves
    ``CKAN_CURRENT_URL`` without it, which is what makes a bare prefix safe.
    A plain test request context has no CKAN middleware, so the environ key
    is supplied here the way CKAN would set it for a request to
    ``/fr/dataset?q=test``.
    """
    stripped = "/dataset?q=test"

    with app.flask_app.test_request_context(
        "/fr" + stripped, environ_overrides={"CKAN_CURRENT_URL": stripped}
    ):
        current = toolkit.h.current_url()

    assert current == stripped
    assert "/" + locale + current == "/" + locale + "/dataset?q=test"


def test_url_for_recurses_on_a_dotted_path(app):
    """Characterises the upstream bug this change works around.

    If this ever stops raising, CKAN or Flask has fixed the underlying
    problem and the templates can go back to ``url_for``.
    """
    dotted = "/?" + DOTTED_QUERY

    with app.flask_app.test_request_context(dotted):
        with pytest.raises(RecursionError):
            toolkit.h.url_for(dotted, locale="en")


def test_prefixing_a_dotted_path_is_safe(app):
    """The replacement handles the same input without recursing."""
    dotted = "/?" + DOTTED_QUERY

    with app.flask_app.test_request_context(
        dotted, environ_overrides={"CKAN_CURRENT_URL": dotted}
    ):
        built = "/en" + toolkit.h.current_url()

    assert built.startswith("/en/?")
    assert "etc/passwd" in built
