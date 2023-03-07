import ckan.plugins as p
import ckan.model as model
import ckan.lib.formatters as formatters

from ckan.plugins import toolkit as tk



from ckanext.montreal_theme.model import SearchConfig

import json

g = tk.g

def is_user_editor_no_arg():
       
    info = get_organization_info_for_user()  #Gets the whole information for every organization the user has permissions for 

    for organization in info: 
            #checking if the user has the role of editor or admin in the organizations for which it has permissions
        if organization.get('capacity') == 'editor':
            return True
        elif organization.get('capacity') == 'admin':
            return True
        
    return False

def is_user_editor(org_id):
       
    info = get_organization_info_for_user()  #Gets the whole information for every organization the user has permissions for 

    for organization in info: 
            #checking if the user has the role of editor in the organizations for which it has permissions
        if (organization.get('id') == org_id and organization.get('capacity') == 'editor') or (organization.get('id') == org_id and organization.get('capacity') == 'admin'):
            return True
        
    return False
    

def get_organization_info_for_user(include_dataset_count=True):
    '''Return a list of organizations with additional data such as user role ('capacity')
       for the ones that the user has permission.
    '''
    context = {'user': g.user}
    data_dict = {
        'id': g.userobj.id,
        }
    return tk.get_action('organization_list_for_user')(context, data_dict)


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
        
        if "KiB" in value:
            value = value.replace("KiB","KB")
        if "MiB" in value:
            value = value.replace("MiB","MB")
        if "GiB" in value:
            value = value.replace("GiB","GB")
        if "TiB" in value:
            value = value.replace("TiB","TB")
            
    except Exception as e:
        value = size
    return value


def teritories_string(data):
    if data:
        return str(data)