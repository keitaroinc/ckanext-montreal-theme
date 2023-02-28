import ckan.plugins as p
import ckan.model as model
import ckan.lib.formatters as formatters

from ckan.plugins import toolkit as tk

from ckanext.montreal_theme.model import SearchConfig

import json

g = tk.g

def is_user_editor():
    all_organizations = get_all_organizations()

    for organization in all_organizations:
        info = get_organization_info(organization.get('id'))
            
        for user in (info.get('users')):
            if user.get('id') == g.userobj.id:
                if user.get('capacity') == 'editor':
                    return True

    return False

          

def get_organization_info(id,include_dataset_count=True):
    '''Return organization information.
    '''
    context = {'user': g.user}
    data_dict = {
        'id': id,
        'all_fields': True}
    return tk.get_action('organization_show')(context, data_dict)


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
    showcases = tk.get_action("ckanext_showcase_list")() or []
    return showcases[:9]


def get_value_from_showcase_extras(extras, key):
    value = ''
    for item in extras:
        if item.get('key') == key:
            value = item.get('value', '')
    return value


def homepage_search_configs():
    return model.Session.query(SearchConfig).all()


def format_size(size):
    try:
        value = formatters.localised_filesize(int(size))
    except Exception as e:
        value = size
    return value


def teritories_string(data):
    if data:
        return str(data)