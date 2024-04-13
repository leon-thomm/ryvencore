"""Defines basic numeric data types"""

from ..Data import _BuiltInData
from numbers import Number, Complex, Real, Rational, Integral
from fractions import Fraction

class NumberData(_BuiltInData):
    """Base data class for numbers"""
    
    number_type = Number
    """Type from numbers module that the payload must conform to"""
    
    fallback_type = None
    """Fallback type to attempt instantiation if the value is not of number_type"""
    
    def __init__(self, value: number_type, load_from=None):
        super().__init__(value, load_from)
    
    @property
    def payload(self) -> number_type:
        return self._payload
    
    @payload.setter
    def payload(self, value: number_type):
        assert isinstance(value, self.number_type), f'Payload of type {value.__class__} is not of (sub)type {self.number_type.__class__}'

        self._payload = value
        # Attempt to cast the given value to the fallback type
        if self.fallback_type is not None and self._payload.__class__ is not self.fallback_type:
            self._payload = self.fallback_type(self._payload)
                      
class ComplexData(NumberData):
    number_type = Complex
    fallback_type = complex
    
class RealData(ComplexData):
    number_type = Real
    fallback_type = float
    
class RationalData(RealData):
    number_type = Rational
    fallback_type = Fraction
    
class IntegerData(RationalData):
    number_type = Integral
    fallback_type = int 
