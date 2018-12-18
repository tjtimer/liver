"""
utilities
author: Tim "tjtimer" Jedro
created: 06.12.18
"""
from pathlib import Path
from pprint import pprint
from typing import Iterator

import inflect
import yaml
from sanic import Sanic

ifl = inflect.engine()


def snake_case(word: str) -> str:
    snake_cased = word[0].lower()
    for letter in word[1:]:
        if ord(letter) <= 91:
            letter = f"_{letter.lower()}"
        snake_cased += letter
    return snake_cased


def flatten(key: str, obj: dict)->dict:
    to_check = [(key, obj)]
    level = 0

    while True:
        key, _obj = to_check.pop(0)
        for k, v in _obj.items():
            if isinstance(v, dict):

                prov_key = f'$${k}-{level}'
                to_check.append((prov_key, v))
                _obj[k] = prov_key
        obj[key] = _obj
        if len(to_check) < 1:
            break
    return obj


class LiverConfig:
    def __init__(self, app: Sanic, path: str):  # path
        self.__cfg = app.config
        self._dir = Path(path)
        self.load_config()

    def __getitem__(self, item):
        value = self.__cfg.get(item.upper(), None)
        if isinstance(value, str) and value.startswith('$$'):
            return self.__cfg.get(value, None)
        return value

    def load_config(self):
        for file in self._dir.glob('*.conf*'):
            key = file.name.split('.conf')[0].upper()
            with file.open() as conf:
                self.__cfg[key] = flatten(key, yaml.safe_load(conf.read()))
        print(f'{" loaded config ":*^80}')
        pprint(self.__dict__)
        pprint(self.__cfg)
