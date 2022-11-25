import ckan.plugins as plugins
import ckan.plugins.toolkit as toolkit

from ckanext.montreal_theme.views.config import montreal_theme
from ckanext.montreal_theme import helpers as h
import ckanext.montreal_theme.cli as cli

class MontrealThemePlugin(plugins.SingletonPlugin):
    plugins.implements(plugins.IConfigurer)
    plugins.implements(plugins.IBlueprint)
    plugins.implements(plugins.ITemplateHelpers)
    plugins.implements(plugins.IFacets)
    plugins.implements(plugins.IClick)
    plugins.implements(plugins.IGroupForm, inherit=True)


    # IClick
    def get_commands(self):
        return cli.get_commands()

    # IConfigurer
    def update_config(self, config_):
        toolkit.add_template_directory(config_, 'templates')
        toolkit.add_public_directory(config_, 'public')
        toolkit.add_resource('assets', 'montreal_theme')
        toolkit.add_ckan_admin_tab(config_, 'montreal_theme.search_config',
                                  toolkit._('Search Config'))

    def get_blueprint(self):
        # Register the new blueprint
        return [montreal_theme]

    # ITemplateHelpers
    def get_helpers(self):
        return {
            'all_organizations': h.get_all_organizations,
            'all_groups': h.get_all_groups,
            'latest_datasets': h.get_latest_datasets,
            'get_showcases': h.get_showcases,
            'get_value_from_showcase_extras': h.get_value_from_showcase_extras,
            'homepage_search_configs': h.homepage_search_configs,
        }

    # IFacets
    def dataset_facets(self, facets_dict, package_type):
        facets_dict['groups'] = toolkit._('Collections')
        return facets_dict

    def group_facets(self, facets_dict, group_type, package_type):
        return facets_dict

    def organization_facets(self, facets_dict, organization_type, package_type):
        return facets_dict

    # IGroupForm
    def group_types(self):
        return ['collections']
