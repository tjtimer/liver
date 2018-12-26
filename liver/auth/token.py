"""
token
author: Tim "tjtimer" Jedro
created: 28.11.18
"""
from functools import wraps
from pprint import pprint


async def create(data, config):
    return


async def verify(token):
    pass


async def refresh(token):
    return


async def delete(token):
    return


def set_access_token(func):
    @wraps(func)
    async def wrapped(*args, **kwargs):
        result = await func(*args, **kwargs)
        print('set_access_token')
        pprint(result)
        return result
    return wrapped
