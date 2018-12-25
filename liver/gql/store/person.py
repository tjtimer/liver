"""
person
author: Tim "tjtimer" Jedro
created: 19.12.18
"""

from graphene import String, Enum, Field

from gql.schema import LiverList, Idx
from storage.model import Node, Edge


class Person(Node):
    name = String()
    email = String()
    friends = LiverList(lambda: Person, query=friends_query)

    class Config:
        indexes = [Idx('email')]


class Status(Enum):
    REQUESTED = 0
    ACCEPTED = 1
    DENIED = 2


class Friendship(Edge):
    status = Field(Status)

    class Config:
        indexes = [Idx('_from', '_to')]
        _any = (Person,)


async def create_person(_, info, name: String, email: String)->Person:
    p = Person(name=name, email=email)
    await p.create(info.context['db'])
    return p


async def update_person(_, info, _id: String, name: String = None, email: String = None)->Person:
    p = Person(_id=_id)
    if name not in ('', None):
        p.name = name
    if email not in ('', None):
        p.email = email
    await p.update(info.context['db'])
    return p


async def request_friendship(_, info, _id: String, o_id: String)->Friendship:
    friendship = Friendship(_from=_id, _to=o_id, status=0)
    await friendship.create(info.context['db'])
    return friendship
