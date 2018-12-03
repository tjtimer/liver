"""
db
author: Tim "tjtimer" Jedro
created: 30.11.18
"""

from aio_arango.client import ArangoAdmin

import datetime

import inflect as inflect
from graphene import ObjectType, ID, String, DateTime, Scalar

ifl = inflect.engine()
node_registry = set()
edge_registry = set()


class BaseModel(ObjectType):
    @classmethod
    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        cls._collection_name_ = ifl.plural(cls.__name__.lower())
        cls._id = ID()
        cls._key = String()
        cls._rev = String()
        cls._created = DateTime()
        cls._updated = DateTime()

    @property
    def collection_name(self)->str:
        return self._collection_name_

    @property
    def data(self) -> dict:
        return {k: v for k, v in self.__dict__.items() if not k.startswith('_')}

    async def create(self, client):
        data = self.data
        self._created = datetime.datetime.utcnow()
        data['_created'] = self._created.isoformat()
        obj = await client[self.collection_name].add(data)
        self.__dict__.update(**obj)
        return self

    async def get(self, client):
        obj = await client[self.collection_name].get(self._id)
        self.__dict__.update(**obj)
        return self

    async def update(self, client):
        obj = await client[self.collection_name].get(self._id)
        self.__dict__.update(**obj)
        return self


class Node(BaseModel):

    @classmethod
    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        node_registry.add(ifl.plural(cls.__name__.lower()))


class Edge(BaseModel):

    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        edge_registry.add(ifl.plural(cls.__name__.lower()))
        cls._from = String()
        cls._to = String()


async def setup(config: dict):
    db = ArangoAdmin(*config.DATABASE.split(':'))
    await db.login()
    return db
