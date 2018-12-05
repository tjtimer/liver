"""
models
author: Tim "tjtimer" Jedro
created: 03.12.18
"""
from graphene import String

from storage.models import Node


class Account(Node):
    __password = String()


class RefreshToken(Node):
    account_id = String()
    token = String()
