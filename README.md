[![Tests](https://github.com/keitaroinc/ckanext-montreal-theme/actions/workflows/test.yml/badge.svg)](https://github.com/keitaroinc/ckanext-montreal-theme/actions)

# ckanext-montreal-theme

The custom CKAN theme and portal extension behind the City of Montreal open data
portal (Donnees Quebec / Donnees Montreal). It replaces the default CKAN look and
feel and adds the portal-specific behaviour the site depends on:

- **Theme & templates** — full override of the CKAN base, header, footer, home,
  dataset, organization, group, user, showcase and `ckanext-pages` templates,
  plus the compiled SCSS/JS assets under `ckanext/montreal_theme/assets/`.
- **Custom dataset schema** — a `ckanext-scheming` dataset schema
  (`donneesqc_metadonnee_scheming.json`) with its own field presets
  (`presets.json`) and a curated licence list (`ckan-licenses.json`).
- **Configurable homepage search** — a `search_config` table and admin views for
  managing the homepage search shortcuts (`ckan montreal init_db` creates the
  table).
- **Bilingual UI** — French translations shipped via `ITranslation`.


## Requirements

Compatibility with core CKAN versions:

| CKAN version    | Compatible?   |
| --------------- | ------------- |
| 2.11            | Yes           |
| 2.12            | not tested    |


## Installation

To install ckanext-montreal-theme:

1. Activate your CKAN virtual environment, for example:

     . /usr/lib/ckan/default/bin/activate

2. Clone the source and install it on the virtualenv

    git clone https://github.com/keitaroinc/ckanext-montreal-theme.git
    cd ckanext-montreal-theme
    pip install -e .
	pip install -r requirements.txt

3. Add `montreal-theme` to the `ckan.plugins` setting in your CKAN
   config file (by default the config file is located at
   `/etc/ckan/default/ckan.ini`).

4. Restart CKAN. For example if you've deployed CKAN with Apache on Ubuntu:

     sudo service apache2 reload


## Config settings

It expects these core / `ckanext-scheming` settings to point at the files it
ships:

	# Custom dataset schema and field presets
	scheming.dataset_schemas = ckanext.montreal_theme:donneesqc_metadonnee_scheming.json
	scheming.presets = ckanext.scheming:presets.json ckanext.montreal_theme:presets.json

	# Curated licence list
	licenses_group_url = file:///path/to/ckanext-montreal-theme/ckanext/montreal_theme/ckan-licenses.json



## Developer installation

To install ckanext-montreal-theme for development, activate your CKAN virtualenv and
do:

    git clone https://github.com/keitaroinc/ckanext-montreal-theme.git
    cd ckanext-montreal-theme
    python setup.py develop
    pip install -r dev-requirements.txt


## Tests

To run the tests, do:

    pytest --ckan-ini=test.ini


## Releasing a new version of ckanext-montreal-theme

If ckanext-montreal-theme should be available on PyPI you can follow these steps to publish a new version:

1. Update the version number in the `setup.py` file. See [PEP 440](http://legacy.python.org/dev/peps/pep-0440/#public-version-identifiers) for how to choose version numbers.

2. Make sure you have the latest version of necessary packages:

    pip install --upgrade setuptools wheel twine

3. Create a source and binary distributions of the new version:

       python setup.py sdist bdist_wheel && twine check dist/*

   Fix any errors you get.

4. Upload the source distribution to PyPI:

       twine upload dist/*

5. Commit any outstanding changes:

       git commit -a
       git push

6. Tag the new release of the project on GitHub with the version number from
   the `setup.py` file. For example if the version number in `setup.py` is
   0.0.1 then do:

       git tag 0.0.1
       git push --tags

## License

[AGPL](https://www.gnu.org/licenses/agpl-3.0.en.html)
