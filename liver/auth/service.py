"""
service
author: Tim "tjtimer" Jedro
created: 28.11.18
"""
from pprint import pprint

from aio_arango.db import ArangoDB
from sanic import Blueprint

from security.crypt import pwd_ctx

auth = Blueprint('auth', url_prefix='/auth')

db = None


async def setup_db(cfg):
    global db
    db = ArangoDB(*cfg['database'].split(':'), 'auth-db')
    await db.login()
    if 'accounts' not in db.get_collections():
        await db.create_collection('accounts')
        await db.accounts.add(
            [
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
        )


@auth.listener('before_server_start')
async def setup(app, loop):
    print('setup auth')
    cfg = app.config.COMPONENTS['auth']
    await setup_db(cfg)
    pprint(app)



