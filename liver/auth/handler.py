"""
handler
author: Tim "tjtimer" Jedro
created: 28.11.18
"""
from sanic import response
from sanic.request import Request

from liver.auth.service import auth


@auth.post('registration', name='registration')
async def register(req: Request):
    if not req.json:
        return response.json({'message': 'No data!'}, status=400)
    cfg = req.app.config
    email = req.json.get('email', None)
    passwd = req.json.get('passwd', None)
    passwd_again = req.json.get('passwd2', None)
    if None in [email, passwd, passwd_again] or passwd_again != passwd:
        return response.json({'message': 'Invalid credentials!'}, status=400)
