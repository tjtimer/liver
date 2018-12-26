"""
app
author: Tim "tjtimer" Jedro
created: 28.11.18
"""
import asyncio
from uuid import uuid4

import arrow
import jinja2
import jinja2_sanic
from sanic import Sanic

from auth.service import auth
from gql.service import gql_setup

STATIC_DIR = '../public/static'
TEMPLATES_DIR = '../templates'

blueprints = (auth,)

app = Sanic('D!Liver')
app.on_close = []

app.blueprint(blueprints)

app.static('/static', STATIC_DIR)
loader = jinja2.FileSystemLoader(searchpath=[TEMPLATES_DIR])
jinja2_sanic.setup(app, loader=loader)
app.render = jinja2_sanic.render_template


@app.get('/')
async def index(request):
    ctx = {}
    return app.render('index.html', request, ctx)


@app.listener('before_server_start')
async def setup(app, loop):
    await gql_setup(app, loop)


@app.listener('after_server_stop')
async def close(app, loop):
    print('server stopping')
    await asyncio.gather(*(
        func() for func in app.on_close
    ))
    print('server stopped')


if __name__ == '__main__':
    app.run(port=3666)
