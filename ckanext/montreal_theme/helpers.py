import ckan.plugins as p
import ckan.model as model

from ckan.plugins import toolkit as tk

from ckanext.montreal_theme.model import SearchConfig


g = tk.g

def get_all_organizations(include_dataset_count=True):
    '''Return a list of organizations that the current user has the specified
    permission for.
    '''
    context = {'user': g.user}
    data_dict = {
        'include_dataset_count': include_dataset_count,
        'all_fields': True}
    return tk.get_action('organization_list')(context, data_dict)


def get_latest_datasets():
    '''Return a list of the latest datasets that the current user has the specified
    permission for.
    '''
    context = {'user': g.user}
    data_dict = {'sort': 'metadata_modified desc', 'rows': 4, 'include_private': True}

    datasets = tk.get_action('package_search')(context, data_dict)
    return datasets.get('results', [])


def get_all_groups(include_dataset_count=True):
    '''Return a list of organizations that the current user has the specified
    permission for.
    '''
    context = {'user': g.user}
    data_dict = {
        'include_dataset_count': include_dataset_count,
        'all_fields': True}
    return tk.get_action('group_list')(context, data_dict)


def get_showcases(num=6):
    '''Return a list of showcases'''
    return tk.get_action("ckanext_showcase_list")() or []


def get_value_from_showcase_extras(extras, key):
    value = ''
    for item in extras:
        if item.get('key') == key:
            value = item.get('value', '')
    return value


def homepage_search_configs():
    return model.Session.query(SearchConfig).all()

