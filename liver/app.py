"""
app
author: Tim "tjtimer" Jedro
created: 28.11.18
"""
from pprint import pprint

import jinja2
import jinja2_sanic
import yaml
from sanic import Sanic, response

from auth.service import auth
from storage import db
from utilities import load_config

blueprints = [auth]

app = Sanic()
app.config.update(**load_config('./conf/'))

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
    pprint(app.__dict__)


@app.listener('after_server_stop')
async def close(app, loop):
    await app.db_admin.close()
    print("db admin closed")


app.blueprint(*blueprints)

if __name__ == '__main__':
    app.run(port=3666)
