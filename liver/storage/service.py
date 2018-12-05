"""
service
author: Tim "tjtimer" Jedro
created: 04.12.18
"""
from aio_arango.client import ArangoAdmin
from sanic import Sanic


class Storage:
    __admin: ArangoAdmin
    __databases: {}


async def setup(app: Sanic):
    cfg = app.config.DATABASE
