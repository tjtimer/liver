"""
service
author: Tim "tjtimer" Jedro
created: 28.11.18
"""
from pprint import pprint

from aio_arango.db import ArangoDB
from sanic import Blueprint

from security.service import pwd_ctx

auth = Blueprint('auth', url_prefix='/auth')

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


async def setup_db(app, cfg):
    if 'auth-db' not in await app.db.get_dbs():
        await app.db.create_db('auth-db')
        await app.db.create_user('auth', cfg['pass'])
    db = ArangoDB('auth', cfg['pass'], 'auth-db')
    await db.login()
    if 'accounts' not in list(await db.get_collections()):
        await db.create_collection('accounts', )
        await db.accounts.add(init_accounts)


@auth.listener('before_server_start')
async def setup(app, loop):
    print('setup auth')
    cfg = app.config.COMPONENTS['auth']
    await setup_db(app, cfg['database'])
    pprint(app)


@auth.listener('before_server_stop')
async def close(app, loop):
    print('close auth')
    global db
    await db.close()
    pprint(app)

