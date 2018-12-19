"""
mutations
author: Tim "tjtimer" Jedro
created: 18.12.18
"""

from graphene import String

from gql.models import Person


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
    await p.get(info.context['db'])
    return p
