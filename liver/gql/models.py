"""
models
author: Tim "tjtimer" Jedro
created: 15.12.18
"""

from graphene import String

from storage.model import Node, Edge, DateTime


class Category(Node):
    title = String()
    definition = String()


class Computer(Node):
    name = String()
    type = String()
    pw_key = String()


class Software(Node):
    title = String()
    version = String()
    license_key = String()
    description = String()


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


class Uses(Edge):
    pass
