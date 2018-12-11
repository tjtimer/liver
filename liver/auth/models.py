"""
models
author: Tim "tjtimer" Jedro
created: 03.12.18
"""
from storage.model import Node


class AccountStatus(Enum):
    DISABLED = 0
    ACTIVE = 1


class Account(Node):
    email = Email(read_only=True)
    password = Password()


class ActivationToken(Node):
    account_id = String()
    token = String()


class RefreshToken(Node):
    account_id = String()
    token = String()
