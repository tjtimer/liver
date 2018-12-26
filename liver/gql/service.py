"""
service
author: Tim "tjtimer" Jedro
created: 15.12.18
"""
from aio_arango.db import ArangoDB
from graphql.execution.executors.asyncio import AsyncioExecutor
from sanic_graphql import GraphQLView

from gql.schema import LiverSchema
from gql.store.person import Friendship, accept_friendship, create_person, deny_friendship, request_friendship, \
    update_person
from storage.model import Graph


schema = LiverSchema(
    graphs=(
        Graph('friends', (Friendship,)),
    ),
    mutations=(
        create_person, update_person,
        request_friendship, accept_friendship, deny_friendship
    )
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

