"""
service
author: Tim "tjtimer" Jedro
created: 28.11.18
"""
from pprint import pprint

from sanic import Blueprint

auth = Blueprint('auth', url_prefix='/auth')


@auth.listener('before_server_start')
async def setup(app, loop):
    print('setup auth')
    pprint(app)
