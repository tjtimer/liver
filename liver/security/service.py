"""
service
author: Tim "tjtimer" Jedro
created: 01.12.18
"""
from pathlib import Path

from passlib.context import CryptContext


ctx_path = (Path(__file__).parent / 'ctx.ini').absolute()
pwd_ctx = CryptContext.from_path(ctx_path)
