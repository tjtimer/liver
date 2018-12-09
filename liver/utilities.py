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

    def handle_nested(key, item):
        prov_key = f'$${key}_{level}'
        to_check.append((prov_key, item))
        return prov_key

    while True:
        key, _obj = to_check.pop(0)
        for k, v in _obj.items():
            if isinstance(v, dict):
                _obj[k] = handle_nested(k, v)
            elif isinstance(v, Iterator):
                _obj[k] = v
                for idx, item in enumerate(v):
                    if isinstance(item, dict):
                        _obj[k][idx] = handle_nested(f'{k}_{idx}', v)
        obj[key] = _obj
        if len(to_check) < 1:
            break
    return obj


class LiverConfig:
    def __init__(self, path: str):  # path
        self.__cfg = {}
        self._dir = Path(path)

    def __getattr__(self, item):
        if hasattr(self, item):
            return getattr(self, item)
        value = self.__cfg[item]
        if isinstance(value, str) and value.startswith('$$'):
            return self.__cfg[value]
        return value

    def __getitem__(self, item):
        if item in self.__dict__.keys():
            return self[item]
        value = self.__cfg[item]
        if isinstance(value, str) and value.startswith('$$'):
            return self.__cfg[value]
        return value

    def load_config(self):
        for file in self._dir.glob('*.conf*'):
            key = file.name.split('.conf')[0]
            with file.open() as conf:
                self.__cfg[key] = flatten(key, yaml.safe_load(conf.read()))
        print(f'{" loaded config ":^*80}')
        pprint(self.__dict__)
