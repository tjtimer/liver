"""
models
author: Tim "tjtimer" Jedro
created: 04.12.18
"""
from pprint import pprint

import arrow
import inflect as inflect
from graphene import Scalar, ObjectType, ID, String, Mutation
from graphql.language import ast

ifl = inflect.engine()


class Schema:
    _queries = []
    _mutations = []

    @staticmethod
    def mutation_factory(cls, key)->type:
        m_name = f'{key.title()}{cls.__name__.title()}'
        mutate = getattr(cls, key)
        output = mutate.__annotions__.pop('return', cls)
        args = {k: v() for k, v in mutate.__annotations__.items()}
        arguments = type('Arguments', (), dict(args))
        attrs = dict(mutate=mutate, Arguments=arguments, Output=output)
        mut_cls = type(m_name, (Mutation,), attrs)
        return mut_cls


    def register_mutations(cls):
        mutation_classes = (
            mutation_factory(cls, key)
            for key in ['create', 'update', 'delete']
            if hasattr(cls, key)
        )

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
        cls._id = ID()
        cls._key = String()
        cls._rev = String()
        cls._created = ArrowType()
        cls._updated = ArrowType()

    @property
    def _name(self)->str:
        return ifl.plural(self.__class__.__name__.lower())

    @property
    def _state(self) -> dict:
        return {k: v for k, v in self.__dict__.items() if not k.startswith('_')}

    async def create(self, client):
        data = dict(self._state)
        self._created = arrow.utcnow()
        data['_created'] = self._created.timestamp
        obj = await client[self._name].add(data)
        self.__dict__.update(**obj)
        return self

    async def get(self, client):
        obj = await client[self._name].get(self._id)
        self.__dict__.update(**obj)
        return self

    async def update(self, client):
        obj = await client[self._name].update(self._id, self.data)
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
