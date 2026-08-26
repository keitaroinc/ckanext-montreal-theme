import ckan.plugins as p
import ckan.model as model
import ckan.lib.formatters as formatters

from ckan.plugins import toolkit as tk

from ckan.plugins.toolkit import get_action

from datetime import datetime

from ckanext.montreal_theme.model import SearchConfig

import json
import logging
import time
import threading
import functools

log = logging.getLogger(__name__)

g = tk.g

_cache_lock = threading.Lock()
_cache_store = {}


def _ttl_cached(ttl=300):
    """In-process TTL cache keyed by function name, args, and current user."""
    def decorator(fn):
        @functools.wraps(fn)
        def wrapper(*args, **kwargs):
            user = getattr(g, 'user', None)
            key = (fn.__name__, args, tuple(sorted(kwargs.items())), user)
            now = time.monotonic()
            with _cache_lock:
                entry = _cache_store.get(key)
                if entry and now < entry['expires']:
                    return entry['value']
            result = fn(*args, **kwargs)
            with _cache_lock:
                _cache_store[key] = {'value': result, 'expires': now + ttl}
            return result
        return wrapper
    return decorator


def _timed(fn):
    @functools.wraps(fn)
    def wrapper(*args, **kwargs):
        t0 = time.perf_counter()
        result = fn(*args, **kwargs)
        ms = (time.perf_counter() - t0) * 1000
        log.info('[HOMEPAGE TIMING] %s took %.1f ms', fn.__name__, ms)
        return result
    return wrapper

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
    

@_timed
def get_organization_info_for_user(include_dataset_count=True):
    '''Return a list of organizations with additional data such as user role ('capacity')
       for the ones that the user has permission.
    '''
    if not getattr(g, 'user', None) or not getattr(g, 'userobj', None):
        return {}

    context = {'user': g.user}
    data_dict = {
        'id': g.userobj.id,
    }

    return tk.get_action('organization_list_for_user')(context, data_dict)


@_timed
@_ttl_cached(ttl=300)
def get_all_organizations(include_dataset_count=False):
    '''Return a list of organizations that the current user has the specified
       permission for.
    '''
    context = {'user': g.user}
    data_dict = {
        'include_dataset_count': include_dataset_count,
        'all_fields': True}
    return tk.get_action('organization_list')(context, data_dict)


@_timed
@_ttl_cached(ttl=120)
def get_latest_datasets():
    '''Return a list of the latest datasets that the current user has the specified
    permission for.
    '''
    context = {'user': g.user}
    data_dict = {'sort': 'metadata_modified desc', 'rows': 4, 'include_private': True}

    datasets = tk.get_action('package_search')(context, data_dict)
    return datasets.get('results', [])


def get_groups():
    # Helper used on the homepage for showing groups

    data_dict = {
        'all_fields': True
    }
    groups = tk.get_action('group_list')({}, data_dict)

    return groups


@_timed
@_ttl_cached(ttl=300)
def get_all_groups(include_dataset_count=False):
    '''Return a list of organizations that the current user has the specified
    permission for.
    '''
    context = {'user': g.user}
    data_dict = {
        'include_dataset_count': include_dataset_count,
        'all_fields': True}
    return tk.get_action('group_list')(context, data_dict)


@_timed
@_ttl_cached(ttl=300)
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

    if size == None:
        value = "--"
        return value
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


def get_google_tag():
    gtag = tk.config.get('ckanext.montreal_theme.gtag')
    return gtag


def datetime():
    return datetime



def get_package_showcases(package_id):
    try:
        # Use CKAN's internal action API
        context = {}
        data_dict = {"package_id": package_id}
        showcases = get_action("ckanext_package_showcase_list")(context, data_dict)
        return showcases
    except Exception as e:
        # Log or handle the exception if needed
        return []


def get_showcase_pkgs(showcase_id):
    return tk.get_action('ckanext_showcase_package_list')(
        {'ignore_auth': True},
        {'showcase_id': showcase_id}
    )
