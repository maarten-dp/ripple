from __future__ import annotations
from typing_extensions import Self


class UIntBase:
    _mask: int

    def __init__(self, value: int | Self):
        self.value = int(value) & self._mask

    # Arithmetic operations
    def __add__(self, other: int | Self) -> Self:
        return self.__class__((int(self) + int(other)) & self._mask)

    def __radd__(self, other: int | Self) -> Self:
        return self.__class__((int(other) + int(self)) & self._mask)

    def __iadd__(self, other: int | Self) -> Self:
        self.value = (int(self) + int(other)) & self._mask
        return self

    def __sub__(self, other: int | Self) -> Self:
        return self.__class__((int(self) - int(other)) & self._mask)

    def __rsub__(self, other: int | Self) -> Self:
        return self.__class__((int(other) - int(self)) & self._mask)

    def __isub__(self, other: int | Self) -> Self:
        self.value = (int(self) - int(other)) & self._mask
        return self

    def __mul__(self, other: int | Self) -> Self:
        return self.__class__((int(self) * int(other)) & self._mask)

    def __rmul__(self, other: int | Self) -> Self:
        return self.__class__((int(other) * int(self)) & self._mask)

    def __imul__(self, other: int | Self) -> Self:
        self.value = (int(self) * int(other)) & self._mask
        return self

    def __truediv__(self, other: int | Self) -> Self:
        return self.__class__(int(int(self) / int(other)) & self._mask)

    def __rtruediv__(self, other: int | Self) -> Self:
        return self.__class__(int(int(other) / int(self)) & self._mask)

    def __itruediv__(self, other: int | Self) -> Self:
        self.value = int(int(self) / int(other)) & self._mask
        return self

    def __floordiv__(self, other: int | Self) -> Self:
        return self.__class__((int(self) // int(other)) & self._mask)

    def __rfloordiv__(self, other: int | Self) -> Self:
        return self.__class__((int(other) // int(self)) & self._mask)

    def __ifloordiv__(self, other: int | Self) -> Self:
        self.value = int((self) // int(other)) & self._mask
        return self

    def __mod__(self, other: int | Self) -> Self:
        return self.__class__((int(self) % int(other)) & self._mask)

    def __rmod__(self, other: int | Self) -> Self:
        return self.__class__((int(other) % int(self)) & self._mask)

    def __imod__(self, other: int | Self) -> Self:
        self.value = (int(self) % int(other)) & self._mask
        return self

    def __pow__(self, other: int | Self) -> Self:
        return self.__class__((self.value ** int(other)) & self._mask)

    def __rpow__(self, other: int | Self) -> Self:
        return self.__class__((int(other) ** int(self)) & self._mask)

    def __ipow__(self, other: int | Self) -> Self:
        self.value = (self.value ** int(other)) & self._mask
        return self

    # Bitwise operations
    def __and__(self, other: int | Self) -> Self:
        return self.__class__(int(self) & int(other))

    def __rand__(self, other: int | Self) -> Self:
        return self.__class__(int(other) & int(self))

    def __iand__(self, other: int | Self) -> Self:
        self.value = int(self) & int(other)
        return self

    def __or__(self, other: int | Self) -> Self:
        return self.__class__(int(self) | int(other))

    def __ror__(self, other: int | Self) -> Self:
        return self.__class__(int(other) | int(self))

    def __ior__(self, other: int | Self) -> Self:
        self.value = int(self) | int(other)
        return self

    def __xor__(self, other: int | Self) -> Self:
        return self.__class__(int(self) ^ int(other))

    def __rxor__(self, other: int | Self) -> Self:
        return self.__class__(int(other) ^ int(self))

    def __ixor__(self, other: int | Self) -> Self:
        self.value = int(self) ^ int(other)
        return self

    def __lshift__(self, other: int | Self) -> Self:
        return self.__class__((int(self) << int(other)) & self._mask)

    def __rlshift__(self, other: int | Self) -> Self:
        return self.__class__((int(other) << int(self)) & self._mask)

    def __ilshift__(self, other: int | Self) -> Self:
        self.value = (int(self) << int(other)) & self._mask
        return self

    def __rshift__(self, other: int | Self) -> Self:
        return self.__class__((int(self) >> int(other)) & self._mask)

    def __rrshift__(self, other: int | Self) -> Self:
        return self.__class__((int(other) >> int(self)) & self._mask)

    def __irshift__(self, other: int | Self) -> Self:
        self.value = (int(self) >> int(other)) & self._mask
        return self

    def __invert__(self) -> Self:
        return self.__class__((~int(self)) & self._mask)

    # Unary operations
    def __neg__(self) -> Self:
        return self.__class__((-int(self)) & self._mask)

    def __pos__(self) -> Self:
        return self.__class__(int(self))

    def __abs__(self) -> Self:
        return self.__class__(abs(int(self)))

    # Comparison operations
    def __eq__(self, other: object) -> bool:
        if not isinstance(other, (int, type(self))):
            return False
        return int(self) == int(other)

    def __ne__(self, other: object) -> bool:
        if not isinstance(other, (int, type(self))):
            return False
        return not self.__eq__(other)

    def __lt__(self, other: int | Self) -> bool:
        return int(self) < int(other)

    def __le__(self, other: int | Self) -> bool:
        return int(self) <= int(other)

    def __gt__(self, other: int | Self) -> bool:
        return int(self) > int(other)

    def __ge__(self, other: int | Self) -> bool:
        return int(self) >= int(other)

    # Type conversion
    def __int__(self) -> int:
        return self.value

    def __float__(self) -> float:
        return float(int(self))

    def __bool__(self) -> bool:
        return bool(self.value)

    def __index__(self) -> int:
        return self.value

    # String representation
    def __repr__(self) -> str:
        return f"{self.__class__.__name__}({self.value})"

    def __str__(self) -> str:
        return str(int(self))

    def __format__(self, format_spec: str) -> str:
        return format(self.value, format_spec)

    def __hash__(self) -> int:
        return hash(int(self))


class UInt8(UIntBase):
    _mask = 0xFF


class UInt16(UIntBase):
    _mask = 0xFFFF
