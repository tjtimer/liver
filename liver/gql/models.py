"""
models
author: Tim "tjtimer" Jedro
created: 15.12.18
"""
from graphene import String, Boolean

from storage.model import Node, Edge, DateTime


class Category(Node):
    title = String()
    definition = String()


class Person(Node):
    name = String()
    email = String()


class Message(Node):
    title = String()
    body = String()


class Event(Node):
    title = String()
    start = DateTime()
    end = DateTime()


class Media(Node):
    title = String()
    path = String()


# Edges


class MemberOf(Edge):
    pass


class WrittenBy(Edge):
    pass


class SentTo(Edge):
    pass


class AttachedTo(Edge):
    pass
