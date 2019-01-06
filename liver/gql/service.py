"""
service
author: Tim "tjtimer" Jedro
created: 15.12.18
"""
from aio_arango.db import ArangoDB
from graphql.execution.executors.asyncio import AsyncioExecutor
from sanic_graphql import GraphQLView

from gql import mutations
from gql.schema import LiverSchema
from gql.store.person import Friendship
from gql.store.task import AssignedTo
from storage.model import Graph

schema = LiverSchema(
    graphs=(
        Graph('friendsGraph', (Friendship,)),
        Graph('tasksGraph', (AssignedTo,))
    ),
    mutations=mutations.__all__
)


async def gql_setup(app, loop):
    db = ArangoDB('gql-user', 'gql-pw', 'gql-db')
    await db.login()
    app.add_route(
        GraphQLView.as_view(
            schema=await schema.setup(db),
            context={'db': db, 'schema': schema},
            executor=AsyncioExecutor(loop=loop),
            graphiql=True
        ), 'graphql'
    )
    app.on_close.append(db.close)

