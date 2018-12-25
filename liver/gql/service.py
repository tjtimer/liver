"""
service
author: Tim "tjtimer" Jedro
created: 15.12.18
"""
from aio_arango.db import ArangoDB

from gql.schema import LiverSchema
from gql.store.person import Friendship, create_person, request_friendship, update_person
from storage.model import Graph

gql_schema = LiverSchema(
    db=ArangoDB('gql-user', 'gql-pw', 'gql-db'),
    graphs=(
        Graph('friends', (Friendship,)),
    ),
    mutations=(create_person, update_person, request_friendship)
)
