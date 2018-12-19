"""
schema
author: Tim "tjtimer" Jedro
created: 19.12.18
"""
import asyncio
from pprint import pprint
from typing import Optional

from aio_arango.db import ArangoDB, DocumentType
from graphene import ObjectType, Schema, Field, String, List, Mutation

from utilities import snake_case


def _find(cls):
    async def inner(_, info, **kwargs):
        obj = cls(**kwargs)
        db = info.context['db']
        await obj.get(db)
        return obj

    return inner


def _all(cls):
    async def inner(_, info, **kwargs):
        pprint(info.context['schema'].__dict__)
        db = info.context['db']
        cls_query = f'FOR x in {cls._collname_} RETURN x'
        return [cls(**obj) async for obj in db.query(cls_query)]
    return inner


class LiverSchema:
    def __init__(self,
                 db: ArangoDB, *,
                 nodes: Optional[tuple]=None,
                 edges: Optional[tuple]=None,
                 queries: Optional[tuple]=None,
                 mutations: Optional[tuple] = None,
                 subscriptions: Optional[tuple] = None):

        self._schema = None
        self._db = db
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
        self._schema = Schema(
            query=query_master,
            mutation=mutation_master
        )
        return self._schema

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
