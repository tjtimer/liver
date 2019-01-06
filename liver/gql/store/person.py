"""
person
author: Tim "tjtimer" Jedro
created: 19.12.18
"""

from graphene import Enum, Field, String

from gql.schema import Idx
from storage.model import Edge, LiverList, Node, QueryGraph

q_f_pending = QueryGraph('friendsGraph', direction='OUTBOUND').f('e.status').eq(0)
q_f_waiting = QueryGraph('friendsGraph', direction='INBOUND').f('e.status').eq(0)
q_f_accepted = QueryGraph('friendsGraph').f('e.status').eq(1)
q_f_denied = QueryGraph('friendsGraph').f('e.status').eq(2)

q_t_all = QueryGraph('tasksGraph', direction='INBOUND')


class Person(Node):
    class PersonalTask(Node):
        title = String()
        description = String()
    name = String()
    email = String()
    friends = LiverList(lambda: Person, query=q_f_accepted)
    pending = LiverList(lambda: Person, query=q_f_pending)
    waiting = LiverList(lambda: Person, query=q_f_waiting)
    tasks = LiverList(PersonalTask, query=q_t_all)

    class Config:
        indexes = [Idx('email')]


class FriendshipStatus(Enum):
    REQUESTED = 0
    ACCEPTED = 1
    DENIED = 2


class Friendship(Edge):
    status = Field(FriendshipStatus)

    class Config:
        indexes = [Idx('status', unique=False)]
        _any = (Person,)


