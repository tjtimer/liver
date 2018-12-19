"""
task
author: Tim "tjtimer" Jedro
created: 19.12.18
"""
from graphene import String

from storage.model import Node


class Task(Node):
    title = String()
    description = String()
