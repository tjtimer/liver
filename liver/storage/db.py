"""
db
author: Tim "tjtimer" Jedro
created: 30.11.18
"""
import asyncio

from aio_arango.client import ArangoAdmin
from aio_arango.db import ArangoDB


async def setup(**cfg)->dict:
    async with ArangoAdmin(*cfg['admin'].split(':')) as admin:
        db_name = cfg['name']
        clients_cfg = [cred.split(':') for cred in cfg['clients']]
        if db_name not in await admin.get_dbs():
            await asyncio.gather(
                *(admin.create_user(cred[:2] for cred in clients_cfg)),
                admin.create_db(db_name)
            )

            await asyncio.gather(
                *(admin.set_access_level(usr[0], db_name, level=usr[2])
                  for usr in clients_cfg)
            )

    clients = {usr[0]: ArangoDB(*usr[:2], db_name) for usr in clients_cfg}
    await asyncio.gather(*(db.login() for db in clients.values()))
    return clients
