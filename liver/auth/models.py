"""
models
author: Tim "tjtimer" Jedro
created: 03.12.18
"""
from graphene import String

from storage.model import Node, Email, Password


class Account(Node):
    email = Email(read_only=True)
    password = Password()


class ActivationToken(Node):
    account_id = String()
    token = String()


class RefreshToken(Node):
    account_id = String()
    token = String()
