"""
db
author: Tim "tjtimer" Jedro
created: 30.11.18
"""

from aio_arango.client import ArangoAdmin, AccessLevel
from aio_arango.db import ArangoDB
from sanic import Sanic


async def setup_admin(name, passwd)->ArangoAdmin:
    db = ArangoAdmin(name, passwd)
    await db.login()
    return db


async def setup(app: Sanic)->ArangoDB:
    conf = app.config.database
    admin = await setup_admin(*conf.ADMIN.split(':'))
    db_name = cfg['name']
    name, passwd = cfg['user'].split(':')
    if db_name not in await cli.get_dbs():
        await cli.create_user(name, passwd)
        await cli.create_db(db_name)
        await cli.set_access_level(name, db_name, level=AccessLevel.FULL)
    db = ArangoDB(name, passwd, db_name)
    await db.login()
    return db
