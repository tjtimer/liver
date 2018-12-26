"""
person
author: Tim "tjtimer" Jedro
created: 19.12.18
"""

import arrow
from graphene import String, Enum, Field

from auth.token import set_access_token
from gql.schema import LiverList, Idx
from storage.model import Node, Edge, Query

q_f_pending = Query('friends', direction='OUTBOUND').eq('e.status', 0)
q_f_waiting = Query('friends', direction='INBOUND').eq('e.status', 0)
q_f_accepted = Query('friends').eq('e.status', 1)
q_f_denied = Query('friends').eq('e.status', 2)


class Person(Node):
    name = String()
    email = String()
    friends = LiverList(lambda: Person, query=q_f_accepted)
    pending = LiverList(lambda: Person, query=q_f_pending)
    waiting = LiverList(lambda: Person, query=q_f_waiting)

    class Config:
        indexes = [Idx('email')]


class FriendshipStatus(Enum):
    REQUESTED = 0
    ACCEPTED = 1
    DENIED = 2


class Friendship(Edge):
    status = Field(FriendshipStatus)

    class Config:
        indexes = [Idx('_from', '_to'), Idx('status', unique=False)]
        _any = (Person,)


@set_access_token
async def create_person(_, info, name: String, email: String)->Person:
    p = Person(name=name, email=email)
    await p.create(info.context['db'])
    return p


async def update_person(_, info, _id: String, name: String = None, email: String = None)->Person:
    p = Person(_id=_id, name=name, email=email)
    await p.update(info.context['db'])
    return p


async def request_friendship(_, info, _id: String, o_id: String)->Friendship:
    f = Friendship(_from=_id, _to=o_id, status=0)
    await f.create(info.context['db'])
    return f


async def accept_friendship(_, info, _id: String, o_id: String)->Friendship:
    upd_str = '{ status: 1, _updated: ' + str(arrow.utcnow().timestamp) + '}'
    query = (f'FOR f in friendship '
             f'FILTER f.status == 0 && f._from == \"{o_id}\" && f._to == \"{_id}\" '
             f'UPDATE f WITH {upd_str} IN friendship '
             f'RETURN NEW')
    f = [obj async for obj in info.context['db'].query(query)]
    return Friendship(**f[0])


async def deny_friendship(_, info, _id: String)->Friendship:
    f = Friendship(_id=_id, status=2)
    await f.update(info.context['db'])
    return f
