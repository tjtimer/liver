"""
db
author: Tim "tjtimer" Jedro
created: 30.11.18
"""
from sanic import Sanic


async def setup(app: Sanic):
    cfg = app.config
