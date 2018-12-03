"""
models
author: Tim "tjtimer" Jedro
created: 03.12.18
"""
from graphene import String


class Account(Node):
    password = String()
