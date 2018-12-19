"""
model
author: Tim "tjtimer" Jedro
created: 04.12.18
"""
import asyncio
from pprint import pprint
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
    async def inner(slf, info, *args, **kwargs):
        print('_find inner')
        print(slf)
        print(args)
        obj = cls(**kwargs)
        db = info.context['db']
        await obj.get(db)
        return obj

    return inner


def _all(cls):
    async def inner(_, info, **kwargs):
        db = info.context['db']
        cls_query = f'FOR x in {cls._collname_} RETURN x'
        result = []
        async for obj in db.query(cls_query):
            result.append(cls(**obj))
        return result
    return inner


class LiverSchema:
    def __init__(self,
                 db: ArangoDB, *,
                 nodes: Optional[tuple]=None,
                 edges: Optional[tuple]=None,
                 queries: Optional[tuple]=None,
                 mutations: Optional[tuple] = None,
                 subscriptions: Optional[tuple] = None):

        self._db = db
        self._meta = None
        self._nodes = {}
        self._edges = {}
        self._queries = {}
        self._mutations = {}
        self._subscriptions = {}

        if isinstance(nodes, (list, tuple)):
            self.register_nodes(*nodes)
        if isinstance(edges, (list, tuple)):
            self.register_edges(*edges)
        if isinstance(queries, (list, tuple)):
            self.register_queries(*queries)
        if isinstance(mutations, (list, tuple)):
            self.register_mutations(*mutations)
        if isinstance(subscriptions, (list, tuple)):
            self.register_subscriptions(*subscriptions)

    async def setup(self):
        await self._db.login()
        await asyncio.gather(*(
            self._db.create_collection(name=name)
            for name in self._nodes.keys()
        ))
        await asyncio.gather(*(
            self._db.create_collection(name=name, doc_type=DocumentType.EDGE)
            for name in self._edges.keys()
        ))

        query_master = type(
            'QueryMaster',
            (*self._queries.values(), ObjectType),
            {}
        )
        mutation_master = type(
            'MutationMaster',
            (ObjectType,),
            {k: v.Field() for k, v in self._mutations.items()}
        )
        subscription_master = type(
            'SubscriptionMaster',
            (*self._subscriptions.values(), ObjectType),
            {}
        )
        self._meta = Schema(
            query=query_master,
            mutation=mutation_master
        )
        return self._meta

    def register_node(self, node):
        self._nodes[node._collname_] = node
        self.register_query(
            type(
                f'{node.__name__}Query',
                (ObjectType,),
                {snake_case(node.__name__): Field(node, _id=String(), resolver=_find(node)),
                 node._collname_: List(node, resolver=_all(node))})
        )

    def register_edge(self, edge):
        self._edges[edge._collname_] = edge

    def register_query(self, query):
        self._queries[snake_case(query.__name__)] = query

    def register_mutation(self, mutation):
        name = mutation.__name__
        class_name = ''.join([p.title() for p in name.split('_')])
        output = mutation.__annotations__.pop('return')
        args = {k: v() for k, v in mutation.__annotations__.items()}
        mutation_class = type(
            class_name,
            (Mutation,),
            {
                'Arguments': type('Arguments', (), args),
                'Output': output,
                'mutate': mutation
            })
        self._mutations[name] = mutation_class

    def register_subscription(self, subscription):
        self._subscriptions[snake_case(subscription.__name__)] = subscription

    def register_nodes(self, *nodes):
        for node in nodes:
            self.register_node(node)

    def register_edges(self, *edges):
        for edge in edges:
            self.register_edge(edge)

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


class _BaseModel(ObjectType):

    @classmethod
    def __init_subclass__(cls, **kwargs):
        cls._collname_ = ifl.plural(snake_case(cls.__name__))
        cls._id = String()
        cls._key = String()
        cls._rev = String()
        cls._created = DateTime()
        cls._updated = DateTime()
        super().__init_subclass__(**kwargs)

    @property
    def _state(self) -> dict:
        return {k: v
                for k, v in self.__dict__.items()
                if not k.startswith('_') and v is not None}

    async def create(self, client):
        self._created = arrow.utcnow()
        obj = await client[self._collname_].add(
            {**self._state, '_created': self._created.timestamp}
        )
        self.__dict__.update(**obj)

    async def get(self, client):
        obj = await client[self._collname_].get(
            str(self._id).split('/')[-1]
        )
        self.__dict__.update(**obj)

    async def update(self, client):
        if self._id in (None, ''):
            raise ClientError(
                f'Can not update instance of {self._meta.name}. '
                f'Attribute _id must be given.'
            )
        self._updated = arrow.utcnow()
        obj = await client[self._collname_].update(
            str(self._id).split('/')[-1],
            {**self._state, '_updated': self._updated.timestamp}
        )
        self.__dict__.update(**obj)


class Node(_BaseModel):

    @classmethod
    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)


class Edge(_BaseModel):

    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        cls._from = String()
        cls._to = String()
        cls._collname_ = snake_case(cls.__name__)
