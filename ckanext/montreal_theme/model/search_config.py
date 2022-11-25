from ckan.model.meta import metadata, mapper, Session
from ckan.model.domain_object import DomainObject
from ckan.model.types import make_uuid
from sqlalchemy import types, Column, Table

import logging

log = logging.getLogger(__name__)

search_config = None


search_config = Table(
    'search_config',
    metadata,
    Column('id',
        types.UnicodeText,
        primary_key=True,
        default=make_uuid()),
    Column('link',
        types.UnicodeText,
        nullable=False),
    Column('value',
        types.UnicodeText,
        nullable=False)
)

class SearchConfig(DomainObject):

    def __init__(self, **kwargs):
        for k, v in kwargs.items():
            setattr(self, k, v)
        self.id = make_uuid()

    @classmethod
    def get_all(cls):
        return Session.query(cls).all()

    @classmethod
    def delete(cls, id):
        obj = Session.query(cls).get(id)
        if obj:
            Session.delete(obj)
            Session.commit()

    @classmethod
    def delete_all(cls):
        Session.query(cls).delete()
        Session.commit()


mapper(SearchConfig, search_config, properties={})
