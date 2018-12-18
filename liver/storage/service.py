"""
service
author: Tim "tjtimer" Jedro
created: 04.12.18
"""
from sanic import Sanic


async def setup(app: Sanic):
    cfg = app.config.DATABASE
