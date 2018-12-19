"""
service
author: Tim "tjtimer" Jedro
created: 15.12.18
"""
from aio_arango.db import ArangoDB

from gql.mutations import create_person, update_person
from storage.model import LiverSchema
from .models import Category, Event, MemberOf, Message, Person, SentTo, WrittenBy

gql_schema = LiverSchema(
    db=ArangoDB('gql-user', 'gql-pw', 'gql-db'),
    nodes=(
        Category, Person, Message, Event
    ),
    edges=(
        MemberOf, WrittenBy, SentTo
    ),
    mutations=(create_person, update_person)
)
