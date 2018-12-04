"""
service
author: Tim "tjtimer" Jedro
created: 28.11.18
"""
import asyncio
from pprint import pprint

from sanic import Blueprint

from security.service import pwd_ctx
from storage import db

auth = Blueprint('auth', url_prefix='/auth')
auth.db = None

init_accounts = [
                {'_key': 'tjtimer@mail.com',
                 'email': 'tjtimer@mail.com',
                 'passwd': pwd_ctx.hash('tjs-pass', category='admin')},
                {'_key': 'jane-doe@mail.com',
                 'email': 'jane-doe@mail.com',
                 'passwd': pwd_ctx.hash('jd-pass', category='user')},
                {'_key': 'anon@mail.com',
                 'email': 'anon@mail.com',
                 'passwd': pwd_ctx.hash('anon-pass', category='user')}
            ]


@auth.listener('before_server_start')
async def setup(app, loop):
    print('setup auth')
    cfg = app.config.COMPONENTS['auth']
    auth.db = await db.setup(app.db_admin, cfg['database'])
    print('app')
    pprint(app)
    print('auth')
    pprint(auth.__dict__)


@auth.listener('before_server_stop')
async def close(app, loop):
    print('close auth')
    await auth.db.close()

