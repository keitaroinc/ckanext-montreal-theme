import json

from ckan.common import g, config
import ckan.lib.helpers as h
from flask import Blueprint
import ckan.logic as logic
import ckan.model as model
from ckan.common import g, _, config, request

from ckan.plugins import toolkit as tk
from flask.views import MethodView
import ckan.lib.navl.dictization_functions as dict_fns
from ckan.views.home import CACHE_PARAMETERS

from ckanext.montreal_theme.model import SearchConfig


montreal_theme = Blueprint('montreal_theme', __name__)



def _get_config_options_frontend():
    styles = [{
        u'text': u'Default',
        u'value': u'/base/css/main.css'
    }, {
        u'text': u'Red',
        u'value': u'/base/css/red.css'
    }, {
        u'text': u'Green',
        u'value': u'/base/css/green.css'
    }, {
        u'text': u'Maroon',
        u'value': u'/base/css/maroon.css'
    }, {
        u'text': u'Fuchsia',
        u'value': u'/base/css/fuchsia.css'
    }]

    homepages = [{
        u'value': u'1',
        u'text': (u'Introductory area, search, featured'
                  u' group and featured organization')
    }, {
        u'value': u'2',
        u'text': (u'Search, stats, introductory area, '
                  u'featured organization and featured group')
    }, {
        u'value': u'3',
        u'text': u'Search, introductory area and stats'
    }, {
        u'value': u'4',
        u'text': u'Montreal Theme'
    }]

    return dict(styles=styles, homepages=homepages)


class ConfigViewFrontend(MethodView):
    def get(self):
        items = _get_config_options_frontend()
        schema = logic.schema.update_configuration_schema()
        data = {}
        for key in schema:
            data[key] = tk.config.get(key)

        vars = dict(data=data, errors={}, **items)

        return tk.render(u'admin/config.html', extra_vars=vars)

    def post(self):
        try:
            req = request.form.copy()
            req.update(request.files.to_dict())
            data_dict = logic.clean_dict(
                dict_fns.unflatten(
                    logic.tuplize_dict(
                        logic.parse_params(req,
                                           ignore_keys=CACHE_PARAMETERS))))

            del data_dict['save']
            data = logic.get_action(u'config_option_update')({
                u'user': g.user
            }, data_dict)
            print (data)

        except logic.ValidationError as e:
            items = _get_config_options_frontend()
            data = request.form
            errors = e.error_dict
            error_summary = e.error_summary
            vars = dict(data=data,
                        errors=errors,
                        error_summary=error_summary,
                        form_items=items,
                        **items)
            return tk.render(u'admin/config.html', extra_vars=vars)

        return h.redirect_to(u'admin.config')


class SearchConfigView(MethodView):
    def get(self):
        search_configs = model.Session.query(SearchConfig).all()
        data = {'search_config': search_configs}
        extra_vars = dict(data=data, errors={})
        return tk.render('admin/search_config.html', extra_vars=extra_vars)

    def post(self):
        try:
            req = request.form.copy()
            req.update(request.files.to_dict())
            data_dict = logic.clean_dict(
                dict_fns.unflatten(
                    logic.tuplize_dict(
                        logic.parse_params(req,
                                           ignore_keys=CACHE_PARAMETERS))))


            del data_dict['save']
            search_config = SearchConfig.delete_all();
            model.Session.commit()
            for link, value in zip(data_dict.get('link'), data_dict.get('value')):
                search_config = SearchConfig(
                    link=link,
                    value=value
                )
                model.Session.add(search_config)
                model.Session.commit()

        except logic.ValidationError as e:

            return tk.render(u'admin/search_config.html', extra_vars=vars)

        return h.redirect_to(u'montreal_theme.config')


class ResetSearchConfigView(MethodView):
    def get(self):
        if u'cancel' in request.args:
            return h.redirect_to(u'admin.config')
        return tk.render(u'admin/confirm_reset.html', extra_vars={})

    def post(self):
        # remove sys info items    
        model.delete_system_info('search-config')
        # reset to values in config
        return h.redirect_to(u'montreal_theme.config')

def collections():
    extra_vars = {}
    return tk.render('home/collections.html', extra_vars=extra_vars)

def contact_form():
    return tk.render('contact/form.html')

montreal_theme.add_url_rule(u'/ckan-admin/config', view_func=ConfigViewFrontend.as_view(str(u'config')))
montreal_theme.add_url_rule(u'/collections', view_func=collections)
montreal_theme.add_url_rule(u'/ckan-admin/search-config', view_func=SearchConfigView.as_view(str(u'search_config')))
montreal_theme.add_url_rule('/nous-joindre',
                      view_func=contact_form,
                      methods=[u'GET', u'POST'])

montreal_theme.add_url_rule('/contact-us',
                      view_func=contact_form,
                      methods=[u'GET', u'POST'])