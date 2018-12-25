"""
schema
author: Tim "tjtimer" Jedro
created: 19.12.18
"""
import asyncio
from pprint import pprint
from typing import Coroutine, Iterator, Optional

from aio_arango.db import ArangoDB, DocumentType
from graphene import Field, Int, List, Mutation, ObjectType, Schema, String

from storage.model import Node
from utilities import snake_case


class LiverList(List):
    def __init__(self, cls: (Node, ObjectType), query: str = None, resolver: Coroutine = None):
        self._cls = cls
        self._query = query
        if resolver is None:
            resolver = self.resolve
        super().__init__(cls, first=Int(), skip=Int(), search=String(), resolver=resolver)

    async def resolve(self, inst, info, first: Int = None, skip: Int = None, search: String = None):
        print('inst: ', inst)
        print('first: ', first)
        print('skip: ', skip)
        print('search: ', search)
        self._query._start_vertex = inst._id
        return [self._cls(**obj) async for obj in info.context['db'].query(self._query.statement)]

class LiverSchema:
    def __init__(self,
                 db: ArangoDB, *,
                 nodes: Optional[tuple]=None,
                 edges: Optional[tuple]=None,
                 graphs: Optional[tuple]=None,
                 queries: Optional[tuple]=None,
                 mutations: Optional[tuple] = None,
                 subscriptions: Optional[tuple] = None):

        self._schema = None
        self._db = db
        self._nodes = {}
        self._edges = {}
        self._graphs = {}
        self._queries = {}
        self._mutations = {}
        self._subscriptions = {}

        if isinstance(nodes, (list, tuple)):
            self.register_nodes(*nodes)
        if isinstance(graphs, (list, tuple)):
            self.register_graphs(*graphs)
        if isinstance(queries, (list, tuple)):
            self.register_queries(*queries)
        if isinstance(mutations, (list, tuple)):
            self.register_mutations(*mutations)
        if isinstance(subscriptions, (list, tuple)):
            self.register_subscriptions(*subscriptions)

    def _find(self, cls):
        async def inner(_, info, **kwargs):
            obj = cls(**kwargs)
            await obj.get(self._db)
            return obj
        return inner

    def _all(self, cls):
        async def inner(_, info, first=None, skip=None, **kwargs):
            print('schema _all: ', cls)
            pprint(dir(info))
            pprint(info.field_asts)
            _q = f'FOR x in {cls._collname_}'
            if first:
                limit = f'LIMIT {first}'
                if skip:
                    limit = f'LIMIT {skip}, {first}'
                _q = f'{_q} {limit}'
            _q = f'{_q} RETURN x'
            return [cls(**obj) async for obj in self._db.query(_q)]
        return inner

    async def setup(self):
        print('schema setup')
        await self._db.login()

        await asyncio.gather(*(
            self._db.create_collection(name=name)
            for name in self._nodes.keys()
        ))
        await asyncio.gather(*(
            self._db.create_collection(name=name, doc_type=DocumentType.EDGE)
            for name in self._edges.keys()
        ))

        await asyncio.gather(*(
            asyncio.gather(*(
                self._db.create_index(
                    col._collname_, {k: idx.__dict__[k] for k in ['type', 'fields', 'unique', 'sparse']}
                )
                for idx in col._config_.get('indexes', [])
            ))
            for col in [*self._nodes.values(), *self._edges.values()]
        ))
        await asyncio.gather(*(
            self._db.create_graph(graph.name, graph.edge_definitions)
            for graph in self._graphs.values()
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

    def register_graph(self, graph):
        self._graphs[graph.name] = graph
        self.register_nodes(*graph.nodes)
        self.register_edges(*graph.edges)

    def register_node(self, node):
        name, collname = node.__name__, node._collname_
        if collname not in self._nodes.keys():
            self._nodes[collname] = node
            self.register_query(
                type(
                    f'{name}Query',
                    (ObjectType,),
                    {snake_case(name): Field(node, _id=String(), resolver=self._find(node)),
                     collname: LiverList(node, resolver=self._all(node))})
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

    def register_graphs(self, *graphs):
        for graph in graphs:
            self.register_graph(graph)

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


class Idx:
    def __init__(self, *fields: Iterator,
                 type: str = None, unique: bool = None, sparse: bool = None):
        self.fields = fields
        self.type = 'hash' if type is None else type
        self.unique = True if unique is None else unique
        self.sparse = True if sparse is None else sparse
