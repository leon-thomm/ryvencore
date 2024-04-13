"""Defines implemented structure data types found in Python's Standard Library"""

from .abc import (
    MutableSequenceData,
    SequenceData,
    MappingData,
    MutableMappingData,
    MutableSetData,
    SetData_ABC,
)
from collections import OrderedDict, deque

class ListData(MutableSequenceData):
    collection_type = list

class TupleData(SequenceData):
    collection_type = tuple

class DictData(MutableMappingData):
    collection_type = dict

class OrderedDictData(MutableMappingData):
    collection_type = OrderedDict

class SetData(MutableSetData):
    collection_type = set

class FrozenSetData(SetData_ABC):
    collection_type = frozenset

class QueueData(MutableSequenceData):
    collection_type = deque




