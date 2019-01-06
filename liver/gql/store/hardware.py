"""
hardware
author: Tim "tjtimer" Jedro
created: 06.01.19
"""
from graphene import String, Enum, Field

from gql.schema import Idx
from storage.model import Node


class HardwareType(Enum):
    PC = 0
    Laptop = 1
    Tablet = 2
    Monitor = 3
    Printer = 4
    Phone = 5


class Hardware(Node):
    type = Field(HardwareType)
    title = String()
    serial_nr = String()

    class Config:
        indexes = (Idx('title'), Idx('serial_nr'), Idx('type', unique=False))

