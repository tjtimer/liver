"""
service
author: Tim "tjtimer" Jedro
created: 28.11.18
"""
from sanic import Blueprint, response
from sanic.request import Request

auth = Blueprint('auth', url_prefix='/auth')


@auth.post('registration', name='registration')
async def register(req: Request):
    cfg = req.app.config
    email = req.json.get('email', None)
    passwd = req.json.get('passwd', None)
    passwd_again = req.json.get('passwd2', None)
    if None in [email, passwd, passwd_again] or passwd_again != passwd:
        return response.json({'message': 'Invalid credentials!'}, status=400)
    if email not in 'data':
        return response.json({'message': 'Invalid credentials!'}, status=400)
