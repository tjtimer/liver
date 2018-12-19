"""
app
author: Tim "tjtimer" Jedro
created: 28.11.18
"""
from pprint import pprint

import jinja2
import jinja2_sanic
from graphql.execution.executors.asyncio import AsyncioExecutor
from sanic import Sanic
from sanic_graphql import GraphQLView

#  from auth.service import auth
from gql.service import gql_schema

#  blueprints = [auth]
STATIC_DIR = '../public/static'
TEMPLATES_DIR = '../templates'

app = Sanic('D!Liver')

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
    print('setup server')

    app.add_route(
        GraphQLView.as_view(
            schema=await gql_schema.setup(),
            context={'db': gql_schema._db},
            executor=AsyncioExecutor(loop=loop),
            graphiql=True
        ),
        '/graphql'
    )


@app.listener('after_server_start')
async def setup(app, loop):
    print('server started')
    pprint(app.__dict__)


@app.listener('before_server_stop')
async def setup(app, loop):
    print('close server')
    pprint(app.__dict__)


@app.listener('after_server_stop')
async def close(app, loop):
    print("clean up server")
    pprint(app.__dict__)


if __name__ == '__main__':
    app.run(port=3666)
