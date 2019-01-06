"""
model
author: Tim "tjtimer" Jedro
created: 04.12.18
"""
import asyncio
from pprint import pprint
from random import randint
from typing import Coroutine
from uuid import UUID, uuid4

import arrow
from aio_arango.client import ClientError
from graphene import ObjectType, Scalar, String, List, Int, Interface
from graphql.language import ast
from graphql.language.ast import StringValue

from utilities import ifl, snake_case


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


class EdgeConfig:
    def __init__(self, edge, _from=None, _to=None, _any=None):
        if _any is None:
            _any = []
        if _from is None:
            _from = []
        if _to is None:
            _to = []
        self._collection = edge
        self._any = list(_any)
        self._from = list(_from)
        self._to = list(_to)

    @property
    def __from(self):
        return [start._collname_ for start in [*self._any, *self._from]]

    @property
    def __to(self):
        return [target._collname_ for target in [*self._any, *self._to]]

    def to_dict(self):
        return {'collection': self._collection._collname_, 'from': self.__from, 'to': self.__to}


class _BaseModel(ObjectType):

    @classmethod
    def __init_subclass__(cls, **kwargs):
        cls._collname_ = snake_case(cls.__name__)
        cls._config_ = {}
        if hasattr(cls, 'Config'):
            cls._config_.update(**cls.Config.__dict__)
            delattr(cls, 'Config')

        cls._id = String()
        cls._key = String()
        cls._rev = String()
        cls._created = DateTime()
        cls._updated = DateTime()

        super().__init_subclass__(**kwargs)

    @property
    def id(self):
        return self._key if self._key else str(self._id).split('/')[-1]

    @property
    def indexes(self):
        return self._config_.get('indexes', [])

    @property
    def _state(self) -> dict:
        return {k: v
                for k, v in self.__dict__.items()
                if k in ['_from', '_to'] or
                not k.startswith('_') and v is not None}

    async def create(self, client):
        obj = await client[self._collname_].add(
            {**self._state, '_created': arrow.utcnow().timestamp},
            params={'returnNew': 'true'}
        )
        self.__dict__.update(**obj['new'])

    async def get(self, client):
        obj = await client[self._collname_].get(self.id)
        self.__dict__.update(**obj)

    async def update(self, client):
        no_id = self.id in (None, '')
        if no_id:
            raise ClientError(
                f'Can not update instance of {self._meta.name}. '
                f'Attribute _id must be given.'
            )
        obj = await client[self._collname_].update(
            self.id,
            {**self._state, '_updated': arrow.utcnow().timestamp},
            params={'returnNew': 'true'}
        )
        self.__dict__.update(**obj['new'])


class Node(_BaseModel):

    @classmethod
    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        cls._collname_ = ifl.plural(cls._collname_)


class Edge(_BaseModel):

    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        cls._from = String()
        cls._to = String()


class Graph:

    def __init__(self, name, edges):
        self.name = name
        self._edges = set()
        self._nodes = set()
        self._edge_definitions = []
        for e in edges:
            print('edge: ', e)
            self._update(e)
        print(self.edge_definitions)

    @property
    def edge_definitions(self):
        return self._edge_definitions

    def _update(self, e):
        cfg = EdgeConfig(
                e,
                **{k: v for k, v in e._config_.items()
                   if k in ['_any', '_from', '_to']}
            )
        d = cfg.to_dict()
        print('edge config: ', d)
        self._edge_definitions.append(d)
        self._nodes.update(cfg._any, cfg._from, cfg._to)
        self._edges.add(e)

    @property
    def nodes(self):
        return self._nodes

    @property
    def edges(self):
        return self._edges


class Query:

    def __init__(self):
        self._expressions = []
        self._identifiers = []

    @property
    def statement(self):
        return ' '.join(self._expressions)

    def fi(self, identifier, collection):
        self._expressions.append(f'FOR {identifier} IN {collection}')
        return self

    def f(self, field):
        self._expressions.append(f'FILTER {field}')
        return self

    def and_(self, field):
        self._expressions.append(f'AND {field}')
        return self

    def or_(self, field):
        self._expressions.append(f'OR {field}')
        return self

    def not_(self, field):
        self._expressions.append(f'NOT {field}')
        return self

    def in_(self, list):
        self._expressions.append(f'IN {list}')
        return self

    def lt(self, value):
        self._expressions.append(f'< {value}')
        return self

    def lte(self, value):
        self._expressions.append(f'<= {value}')
        return self

    def eq(self, value):
        self._expressions.append(f'== {value}')
        return self

    def neq(self, value):
        self._expressions.append(f'!= {value}')
        return self

    def like(self, value):
        self._expressions.append(f'LIKE "{value}"')
        return self

    def limit(self, size: int, offset: int = None):
        if offset is None:
            offset = 0
        self._expressions.append(f'LIMIT {abs(int(offset))}, {abs(int(size))}')
        return self

    def asc(self, field):
        self._expressions.append(f'SORT {field} ASC')
        return self

    def desc(self, field):
        self._expressions.append(f'SORT {field} DESC')
        return self

    def ret(self, ret_str):
        self._expressions.append(f'RETURN {ret_str}')
        return self


class QueryGraph(Query):

    def __init__(self,
                 graph_name: str, *,
                 depth: int or list = None,
                 direction: str = None,
                 ret: str = None):
        super().__init__()
        self._graph_name = graph_name

        if depth is None:
            depth = 1
        elif isinstance(depth, (list, tuple)):
            start, stop = sorted(depth)[:2]
            depth = f'{start}..{stop}'
        else:
            depth = abs(int(depth))
        self._depth = depth
        self._direction = 'ANY' if direction is None else direction.upper()
        self._ret = 'v' if ret is None else ret
        self.start_vertex = None

    @property
    def statement(self):
        return (f'FOR v, e, p IN {self._depth} {self._direction} \"{self.start_vertex}\" '
                f'GRAPH \"{self._graph_name}\" {" ".join(self._expressions)} RETURN {self._ret}')


i = 0


class LiverList(List):
    def __init__(self, cls: (Node, ObjectType), query: QueryGraph = None, resolver: Coroutine = None):
        self._cache = {}
        self._cls = cls
        if resolver is None:
            self._query = query
            resolver = self.resolve
        super().__init__(cls, first=Int(), skip=Int(), search=String(), resolver=resolver)

    async def resolve(self, inst, info, first: Int = None, skip: Int = None, search: String = None):
        #
        # uncomment to see that all resolvers run concurrently
        #
        # global i
        # i += 1
        # uid = i
        # delay = randint(2, 10)
        # print(uid, ' sleeping ', delay)
        # await asyncio.sleep(delay)
        # print(uid, ' woke up')
        self._query.start_vertex = _id = inst._id
        now = arrow.now()
        cached = self._cache.get(_id, None)
        if cached is not None:
            valid = (now - cached.get('since')).seconds < 5
            if valid is True:
                return cached.get('data')
        result = [self._cls(**obj)
                  async for obj in info.context['db'].query(self._query.statement)
                  if obj is not None]
        self._cache[_id] = dict(since=now, data=result)
        return result
