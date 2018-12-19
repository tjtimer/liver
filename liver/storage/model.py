"""
model
author: Tim "tjtimer" Jedro
created: 04.12.18
"""
from uuid import UUID

import arrow
from aio_arango.client import ClientError
from graphene import ObjectType, Scalar, String
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
        data = {**self._state}
        await self.get(client)
        self._updated = arrow.utcnow()
        obj = await client[self._collname_].update(
            str(self._id).split('/')[-1],
            {**data, '_updated': self._updated.timestamp}
        )
        self.__dict__.update(**data, **obj)


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
