"""
service
author: Tim "tjtimer" Jedro
created: 15.12.18
"""
from storage.model import LiverSchema

from .models import Category, MemberOf, Message, Person, WrittenBy, SentTo, Event

gql_schema = LiverSchema(
    models=(
        Category, Person, Message, Event,
        MemberOf, WrittenBy, SentTo
    )
)
