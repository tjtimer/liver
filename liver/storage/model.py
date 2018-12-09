"""
model
author: Tim "tjtimer" Jedro
created: 04.12.18
"""

import arrow
from graphene import ID, ObjectType, Scalar, String
from graphql.language import ast

from utilities import ifl, snake_case


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


class ModelName:
    def __init__(self, cls):
        self.__value = cls.__name__

    @property
    def singular(self):
        return snake_case(self.__value)

    @property
    def plural(self):
        return '_'.join(
            [*self.singular.split('_')[:-1],
             ifl.plural(self.singular.split('_')[-1])]
        )


class BaseModel(ObjectType):
    @classmethod
    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        cls.__name = ModelName(cls)
        cls._id = ID()
        cls._key = String()
        cls._rev = String()
        cls._created = ArrowType()
        cls._updated = ArrowType()

    @property
    def _state(self) -> dict:
        return {k: v for k, v in self.__dict__.items()
                if not k.startswith('_') and v is not None}

    async def create(self, client):
        self._created = arrow.utcnow()
        obj = await client[self.__name.plural].add(
            {**self._state, '_created': self._created.timestamp}
        )
        self.__dict__.update(**obj)
        return self

    async def get(self, client):
        obj = await client[self.__name.plural].get(self._id)
        self.__dict__.update(**obj)
        return self

    async def update(self, client):
        self._updated = arrow.utcnow()
        obj = await client[self.__name.plural].update(
            self._id,
            {**self._state, '_updated': self._updated.timestamp}
        )
        self.__dict__.update(**obj)
        return self


class Node(BaseModel):

    @classmethod
    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)


class Edge(BaseModel):

    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        cls._from = String()
        cls._to = String()

