"""
app
author: Tim "tjtimer" Jedro
created: 28.11.18
"""
import asyncio
from getpass import getpass
from pprint import pprint

import jinja2
import jinja2_sanic
import yaml
from sanic import Sanic, response

import db
import security
from auth.service import auth

blueprints = [auth]

app = Sanic()

with open('./conf/app.conf.yaml', 'r') as conf:
    app.config.update(**yaml.safe_load(conf.read()))

app.static('/static', app.config.STATIC_DIR)

loader = jinja2.FileSystemLoader(searchpath=[app.config.TEMPLATES_DIR])
jinja2_sanic.setup(app, loader=loader)


@app.get('/')
@jinja2_sanic.template('index.html')
async def index(_):
    return response.html({})


@app.listener('before_server_start')
async def setup(app, loop):
    print('setup app')
    app.db = await db.setup(app.config)
    pprint(app)


@app.listener('after_server_stop')
async def close(app, loop):
    pass


app.blueprint(*blueprints)


if __name__ == '__main__':
    app.run(port=3666)
