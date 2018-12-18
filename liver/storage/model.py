"""
model
author: Tim "tjtimer" Jedro
created: 04.12.18
"""
import asyncio
from typing import Optional
from uuid import UUID

import arrow
from aio_arango.client import ClientError
from aio_arango.db import ArangoDB, DocumentType
from graphene import Field, Interface, List, ObjectType, Scalar, String, Schema, Mutation
from graphql.language import ast
from graphql.language.ast import StringValue

from utilities import ifl, snake_case


class ModelMiddleware:
    async def resolve(self, next, root, info, *args):
        return await next(root, info, args)


def _find(cls):
    async def inner(slf, info, **kwargs):
        print(slf)
        obj = cls(**kwargs)
        db = info.context['db']
        await obj.get(db)
        return obj

    return inner


def _all(cls):
    async def inner(slf, info, **kwargs):
        print(slf)
        db = info.context['db']
        cls_query = f'FOR x in {cls._meta.collname} RETURN x'
        async for obj in db.query(cls_query):
            yield cls(**obj)
    return inner


def _create(cls):
    async def inner(slf, info, **kwargs):
        print(slf)
        obj = cls.__init__(**kwargs)
        res = await obj.create(info.context['db'])
        return res
    return inner


class LiverSchema:
    def __init__(self,
                 db: ArangoDB, *,
                 models: Optional[tuple]=None,
                 queries: Optional[tuple]=None,
                 mutations: Optional[tuple] = None,
                 subscriptions: Optional[tuple] = None):
        self._db = db
        self._meta = None
        self._models = {
            'nodes': {},
            'edges': {}
        }
        self._queries = {}
        self._mutations = {}
        self._subscriptions = {}
        if isinstance(models, tuple):
            self.register_models(*models)
        if isinstance(queries, tuple):
            self.register_queries(*queries)

        if isinstance(mutations, tuple):
            self.register_mutations(*mutations)
        if isinstance(subscriptions, tuple):
            self.register_subscriptions(*subscriptions)

    def setup(self):
        await asyncio.gather(*(
            self._db.create_collection(name=name)
            for name in self._models['nodes'].values()
        ))
        await asyncio.gather(*(
            self._db.create_collection(name=name, doc_type=DocumentType.EDGE)
            for name in self._models['edges'].values()
        ))

        if self._meta is None:
            query_master = type(
                'QueryMaster',
                (*self._queries.values(), ObjectType),
                {}
            )
            mutation_master = type(
                'MutationMaster',
                (*self._mutations.values(), ObjectType),
                {}
            )
            subscription_master = type(
                'SubscriptionMaster',
                (*self._subscriptions.values(), ObjectType),
                {}
            )
            self._meta = Schema(
                query=query_master
            )
        return self._meta

    def register_model(self, model):
        if EdgeInterface in model._meta.interfaces:
            self._models['edges'][model.collname] = model
        else:
            self._models['nodes'][model.collname] = model

    def register_query(self, query):
        self._queries[snake_case(query.__name__)] = query

    def register_mutation(self, mutation):
        self._mutations[snake_case(mutation.__name__)] = mutation

    def register_subscription(self, subscription):
        self._subscriptions[snake_case(subscription.__name__)] = subscription

    def register_models(self, *models):
        for model in models:
            self.register_model(model)

    def register_queries(self, *queries):
        for query in queries:
            self.register_query(query)

    def register_mutations(self, *mutations):
        for mutation in mutations:
            self.register_mutation(mutation)

    def register_subscriptions(self, *subscriptions):
        for subscription in subscriptions:
            self.register_subscription(subscription)


class DateTime(Scalar):

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
        except TypeError:
            return None


class ID(Scalar):

    @staticmethod
    def serialize(value):
        try:
            return UUID(value).hex
        except ValueError:
            return None

    @classmethod
    def parse_literal(cls, node):
        if isinstance(node, ast.StringValue):
            return cls.parse_value(node.value)

    @staticmethod
    def parse_value(value):
        try:
            return UUID(value)
        except ValueError:
            return None


class Email(Scalar):
    """
    The `String` scalar type represents textual data, represented as UTF-8
    character sequences. The String type is most often used by GraphQL to
    represent free-form human-readable text.
    """

    @staticmethod
    def coerce_string(value):
        print('Email coercing value: ', value)
        return value

    serialize = coerce_string
    parse_value = coerce_string

    @staticmethod
    def parse_literal(ast):
        print('Email parsing literal: ', ast)
        if isinstance(ast, StringValue):
            return ast.value


class Password(Scalar):
    """
    The `String` scalar type represents textual data, represented as UTF-8
    character sequences. The String type is most often used by GraphQL to
    represent free-form human-readable text.
    """

    @staticmethod
    def coerce_string(value):
        print('Password coercing value: ', value)
        return value

    serialize = coerce_string
    parse_value = coerce_string

    @staticmethod
    def parse_literal(ast):
        print('Password parsing literal: ', ast)
        if isinstance(ast, StringValue):
            return ast.value


class DocumentInterface(Interface):
    _id = ID()
    _key = String()
    _rev = String()
    _created = DateTime()
    _updated = DateTime()


class EdgeInterface(Interface):
    _from = String()
    _to = String()


class _BaseModel(ObjectType):

    @classmethod
    def __init_subclass__(cls, **kwargs):
        interfaces = (DocumentInterface,)
        if hasattr(cls, '_interfaces_'):
            interfaces += getattr(cls, '_interfaces_', ())
            delattr(cls, '_interfaces_')
        cls.Meta = type(
            'Meta',
            (),
            {'interfaces': interfaces}
        )
        super().__init_subclass__(**kwargs)

    @property
    def _state(self) -> dict:
        return self.__dict__

    @property
    def collname(self):
        pass

    async def create(self, client):
        self._created = arrow.utcnow()
        obj = await client[self.collname].add(
            {**self._state, '_created': self._created.timestamp}
        )
        self.__dict__.update(**obj)

    async def get(self, client):
        obj = await client[self.collname].get(self._id)
        self.__dict__.update(**obj)

    async def update(self, client):
        if self._id in (None, ''):
            raise ClientError()
        self._updated = arrow.utcnow()
        obj = await client[self.collname].update(
            self._id,
            {**self._state, '_updated': self._updated.timestamp}
        )
        self.__dict__.update(**obj)


class Node(_BaseModel):

    @classmethod
    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)

    @property
    def collname(self):
        return ifl.plural(snake_case(self._meta.name))


class Edge(_BaseModel):

    def __init_subclass__(cls, **kwargs):
        cls._interfaces_ = (EdgeInterface, *getattr(cls, '_interfaces_', ()))
        super().__init_subclass__(**kwargs)

    @property
    def collname(self):
        return snake_case(self._meta.name)
