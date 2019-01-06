"""
task
author: Tim "tjtimer" Jedro
created: 19.12.18
"""
from graphene import Field, String

from gql.schema import Idx, find_
from gql.store import Person
from gql.store.hardware import Hardware
from storage.model import Edge, LiverList, Node, QueryGraph

q_at_all = QueryGraph('tasksGraph', direction='OUTBOUND')


class Task(Node):
    title = String()
    description = String()
    assigned_to = LiverList(Person, query=q_at_all)

    class Config:
        indexes = (Idx('title'),)


class AssignedTo(Edge):
    by = Field(Person, _id=String(), resolver=find_(Person))

    class Config:
        _from = (Task,)
        _to = (Person, Hardware)
        indexes = (Idx('_to', unique=False),)


class PartOf(Edge):
    pass
