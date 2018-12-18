"""
mutations
author: Tim "tjtimer" Jedro
created: 18.12.18
"""
from graphene import String

from gql.models import Person


async def create_person(db, name: String, email: String)->Person:
    p = Person(name=name, email=email)
    obj = await p.create(db)
    p.__dict__.update(**obj)
    return p
