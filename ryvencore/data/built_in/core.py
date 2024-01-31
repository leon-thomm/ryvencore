"""Defines common data types based on python standard types"""

from ..Data import Data, _BuiltInData
from typing import Iterable
from .collections.abc import SequenceData
 
class PayloadData(_BuiltInData):
    """
    Data container that checks if the appropriate payload type has been set
    on instantiation.
    """
    
    payload_type = None
    """
    Type used to assert that the value is a (sub)class of that type
    Not used for type-checking
    """  
    
    def __init__(self, value=None, load_from=None):
        super().__init__(value, load_from)
        
        # payload initialization if a type is given and the value is not of that type
        if (self.payload_type is not None and self._payload is not None):
            assert isinstance(self._payload, self.payload_type), f'Payload {self._payload} does not inherit from {self.payload_type}'
            

class StringData(SequenceData):
    collection_type = str


class BytesData(SequenceData):
    collection_type = bytes
 

def __get_all_subclasses(cls):
    subclasses = set(cls.__subclasses__())
    for subclass in cls.__subclasses__():
        subclasses.update(__get_all_subclasses(subclass))
    return subclasses 


def get_built_in_data_types() -> Iterable[Data]:
    """Retrieves all the built-in data types"""
    return __get_all_subclasses(_BuiltInData)