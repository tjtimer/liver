"""
db
author: Tim "tjtimer" Jedro
created: 30.11.18
"""
from pprint import pprint

import arrow
import inflect as inflect
from aio_arango.client import ArangoAdmin, AccessLevel
from aio_arango.db import ArangoDB, DocumentType
from graphene import ID, ObjectType, Scalar, String
from graphql.language import ast

ifl = inflect.engine()
node_registry = set()
edge_registry = set()


class ArrowType(Scalar):

    @staticmethod
    def serialize(value):
        try:
            dt = arrow.get(value)
            return dt.for_json()
        except TypeError:
            return None

    @classmethod
    def parse_literal(cls, node):
        if isinstance(node, ast.StringValue):
            return cls.parse_value(node.value)

    @staticmethod
    def parse_value(value):
        try:
            return arrow.get(value)
        except ValueError:
            return None


class BaseModel(ObjectType):
    @classmethod
    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        print("init subclass", cls)
        pprint(cls.__dict__)
        cls.__collection_name = ifl.plural(cls.__name__.lower())
        cls._id = ID()
        cls._key = String()
        cls._rev = String()
        cls._created = ArrowType()
        cls._updated = ArrowType()

    @property
    def collection_name(self)->str:
        return self.__collection_name

    @property
    def data(self) -> dict:
        return {k: v for k, v in self.__dict__.items() if not k.startswith('_')}

    async def create(self, client):
        data = self.data
        self._created = arrow.utcnow()
        data['_created'] = self._created.timestamp
        obj = await client[self.collection_name].add(data)
        self.__dict__.update(**obj)
        return self

    async def get(self, client):
        obj = await client[self.collection_name].get(self._id)
        self.__dict__.update(**obj)
        return self

    async def update(self, client):
        obj = await client[self.collection_name].update(self._id, self.data)
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


async def setup_admin(config: dict):
    db = ArangoAdmin(*config.DB_ADMIN.split(':'))
    await db.login()
    return db


async def setup(cli: ArangoAdmin, cfg: dict)->ArangoDB:
    db_name = cfg['name']
    name, passwd = cfg['user'].split(':')
    if db_name not in await cli.get_dbs():
        await cli.create_user(name, passwd)
        await cli.create_db(db_name)
        await cli.set_access_level(name, db_name, level=AccessLevel.FULL)
    db = ArangoDB(name, passwd, db_name)
    await db.login()
    return db
