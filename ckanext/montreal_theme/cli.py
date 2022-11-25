import click
import ckan.plugins.toolkit as tk

import ckanext.montreal_theme.model.search_config as search_config


@click.group("montreal", short_help="Montreal Theme commands")
def montreal():
    pass

@montreal.command("init_db")
def init_db():
    click.secho(u"Initializing Montreal Theme Config tables", fg=u"green")
    try:
        search_config.setup()
    except Exception as e:
       tk.error_shout(str(e))

    click.secho(u"Montreal Theme Config tables initialized", fg=u"green")


def get_commands():
    return [montreal]