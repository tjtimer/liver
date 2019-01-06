"""
mutations
author: Tim "tjtimer" Jedro
created: 05.01.19
"""
import arrow
from graphene import String

from gql.store import Task
from gql.store.person import Person, Friendship


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
             f'FILTER f._from == \"{o_id}\" && f._to == \"{_id}\" '
             f'UPDATE f WITH {upd_str} IN friendship '
             f'RETURN NEW')
    f = [obj async for obj in info.context['db'].query(query)]
    return Friendship(**f[0])


async def deny_friendship(_, info, _id: String)->Friendship:
    f = Friendship(_id=_id, status=2)
    await f.update(info.context['db'])
    return f


async def create_task(_, info, title: String, description: String = None)->Task:
    t = Task(title=title, description=description)
    await t.create(info.context['db'])
    return t

__all__ = [create_person, update_person,
           request_friendship, accept_friendship, deny_friendship,
           create_task]
