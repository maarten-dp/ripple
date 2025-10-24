from __future__ import annotations
from typing import Any
from dataclasses import field
from typing_extensions import Self


def uint_field(uint_class: type[UIntBase]) -> Any:
    return field(default_factory=lambda: uint_class(0))


class UIntBase(int):
    _mask: int

    def __new__(cls, value: float | int | Self | None = None) -> Self:
        if value:
            if isinstance(value, cls):
                return value
            if isinstance(value, float):
                value = int(value)
            value &= cls._mask
            return super().__new__(cls, value)
        return super().__new__(cls)

    # def __init__(self, value: int | Self):
    #     self.value = int(value) & self._mask

    # # Arithmetic operations
    def __add__(self, other: int | Self) -> Self:
        return self.__class__(super().__add__(other))

    # def __radd__(self, other: int | Self) -> Self:
    #     return self.__class__((int(other) + int(self)) & self._mask)

    # def __iadd__(self, other: int | Self) -> Self:
    #     self.value = (int(self) + int(other)) & self._mask
    #     return self

    def __sub__(self, other: int | Self) -> Self:
        return self.__class__(super().__sub__(other))

    # def __rsub__(self, other: int | Self) -> Self:
    #     return self.__class__((int(other) - int(self)) & self._mask)

    # def __isub__(self, other: int | Self) -> Self:
    #     self.value = (int(self) - int(other)) & self._mask
    #     return self

    def __mul__(self, other: int | Self) -> Self:
        return self.__class__(super().__mul__(other))

    # def __rmul__(self, other: int | Self) -> Self:
    #     return self.__class__((int(other) * int(self)) & self._mask)

    # def __imul__(self, other: int | Self) -> Self:
    #     self.value = (int(self) * int(other)) & self._mask
    #     return self

    def __truediv__(self, other: int | Self) -> Self:
        return self.__class__(int(super().__truediv__(other)))

    # def __rtruediv__(self, other: int | Self) -> Self:
    #     return self.__class__(int(int(other) / int(self)) & self._mask)

    # def __itruediv__(self, other: int | Self) -> Self:
    #     self.value = int(int(self) / int(other)) & self._mask
    #     return self

    # def __floordiv__(self, other: int | Self) -> Self:
    #     return self.__class__((int(self) // int(other)) & self._mask)

    # def __rfloordiv__(self, other: int | Self) -> Self:
    #     return self.__class__((int(other) // int(self)) & self._mask)

    # def __ifloordiv__(self, other: int | Self) -> Self:
    #     self.value = int((self) // int(other)) & self._mask
    #     return self

    # def __mod__(self, other: int | Self) -> Self:
    #     return self.__class__((int(self) % int(other)) & self._mask)

    # def __rmod__(self, other: int | Self) -> Self:
    #     return self.__class__((int(other) % int(self)) & self._mask)

    # def __imod__(self, other: int | Self) -> Self:
    #     self.value = (int(self) % int(other)) & self._mask
    #     return self

    def __pow__(self, other: int | Self) -> Self:
        return self.__class__(super().__pow__(other))

    # def __rpow__(self, other: int | Self) -> Self:
    #     return self.__class__((int(other) ** int(self)) & self._mask)

    # def __ipow__(self, other: int | Self) -> Self:
    #     self.value = (self.value ** int(other)) & self._mask
    #     return self

    # # Bitwise operations
    def __and__(self, other: int | Self) -> Self:
        return self.__class__(super().__and__(other))

    # def __rand__(self, other: int | Self) -> Self:
    #     return self.__class__(int(other) & int(self))

    def __iand__(self, other: int | Self) -> Self:
        return self.__class__(super().__and__(other))

    def __or__(self, other: int | Self) -> Self:
        return self.__class__(super().__or__(other))

    # def __ror__(self, other: int | Self) -> Self:
    #     return self.__class__(int(other) | int(self))

    def __ior__(self, other: int | Self) -> Self:
        return self.__class__(super().__or__(other))

    # def __xor__(self, other: int | Self) -> Self:
    #     return self.__class__(int(self) ^ int(other))

    # def __rxor__(self, other: int | Self) -> Self:
    #     return self.__class__(int(other) ^ int(self))

    # def __ixor__(self, other: int | Self) -> Self:
    #     self.value = int(self) ^ int(other)
    #     return self

    def __lshift__(self, other: int | Self) -> Self:
        return self.__class__(super().__lshift__(other))

    def __rlshift__(self, other: int | Self) -> Self:
        return self.__class__(super().__rlshift__(other))

    # def __ilshift__(self, other: int | Self) -> Self:
    #     self.value = (int(self) << int(other)) & self._mask
    #     return self

    def __rshift__(self, other: int | Self) -> Self:
        return self.__class__(super().__rshift__(other))

    # def __rrshift__(self, other: int | Self) -> Self:
    #     return self.__class__((int(other) >> int(self)) & self._mask)

    def __irshift__(self, other: int | Self) -> Self:
        return self.__class__(super().__rshift__(other))

    def __invert__(self) -> Self:
        return self.__class__(super().__invert__())

    # # Unary operations
    def __neg__(self) -> Self:
        return self.__class__(super().__neg__())

    # def __pos__(self) -> Self:
    #     return self.__class__(int(self))

    # def __abs__(self) -> Self:
    #     return self.__class__(abs(int(self)))

    # # Comparison operations
    # def __eq__(self, other: object) -> bool:
    #     if not isinstance(other, (int, type(self))):
    #         return False
    #     return int(self) == int(other)

    # def __ne__(self, other: object) -> bool:
    #     if not isinstance(other, (int, type(self))):
    #         return False
    #     return not self.__eq__(other)

    # def __lt__(self, other: int | Self) -> bool:
    #     return int(self) < int(other)

    # def __le__(self, other: int | Self) -> bool:
    #     return int(self) <= int(other)

    # def __gt__(self, other: int | Self) -> bool:
    #     return int(self) > int(other)

    # def __ge__(self, other: int | Self) -> bool:
    #     return int(self) >= int(other)

    # # Type conversion
    # def __int__(self) -> int:
    #     return self.value

    # def __float__(self) -> float:
    #     return float(int(self))

    # def __bool__(self) -> bool:
    #     return bool(self.value)

    # def __index__(self) -> int:
    #     return self.value

    # String representation
    def __repr__(self) -> str:
        val = super().__repr__()
        return f"{self.__class__.__name__}({val})"

    def __str__(self) -> str:
        return str(int(self))


class UInt8(UIntBase):
    _mask = 0xFF


class UInt16(UIntBase):
    _mask = 0xFFFF


class UInt32(UIntBase):
    _mask = 0xFFFFFFFF
