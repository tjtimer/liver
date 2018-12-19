"""
person
author: Tim "tjtimer" Jedro
created: 19.12.18
"""
from graphene import String, List, Int

from storage.model import Node


class Person(Node):
    name = String()
    email = String()
    friends = List(lambda: Person, first=Int())

    async def resolve_friends(self, info, first: Int=None):
        qs = f'FOR p IN people FILTER p._id != \"{self._id}\" RETURN p'
        return [Person(**obj) async for obj in info.context['db'].query(qs)]


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
