from __future__ import annotations
from typing import Any
from dataclasses import field
from typing_extensions import Self


Q16_16_SCALE = 1 << 16


def uint_field(uint_class: type[UIntBase]) -> Any:
    return field(default_factory=lambda: uint_class(0))


class UIntBase(int):
    _mask: int
    _struct_format: str

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
    _struct_format = "B"


class UInt16(UIntBase):
    _mask = 0xFFFF
    _struct_format = "H"


class UInt32(UIntBase):
    _mask = 0xFFFFFFFF
    _struct_format = "I"

    def to_q16_16(self) -> Q16_16:
        return Q16_16(self / Q16_16_SCALE)


class Q16_16(float):
    def to_uint32(self) -> UInt32:
        return UInt32(self * Q16_16_SCALE)


# # ==========================================================
# # quant.py — Float quantization helpers
# # ==========================================================
# # Big-endian struct format helper
# BE = ">"  # network byte order


# def clamp(x: float, lo: float, hi: float) -> float:
#     return hi if x > hi else lo if x < lo else x


# # --- Linear quantizers -------------------------------------------------------
# # q16.16: store as signed 32-bit fixed point (int32)
# SCALE_Q16_16 = float(1 << 16)


# def f_to_q16_16(x: float) -> int:
#     xi = int(
#         round(
#             clamp(x, -2147483648.0 / SCALE_Q16_16, 2147483647.0 / SCALE_Q16_16)
#             * SCALE_Q16_16
#         )
#     )
#     # two's complement range already enforced by clamp
#     return xi


# def q16_16_to_f(i: int) -> float:
#     return float(i) / SCALE_Q16_16


# # q meters within range [-max_m, max_m] into signed 16 bits (s16)
# # Example: 0.01 m precision with max_m = 327.67 -> maps to [-327.67, 327.67]


# def f_to_s16(x: float, max_m: float, step: float) -> int:
#     # steps per meter -> scale
#     scale = 1.0 / step
#     lo, hi = -max_m, max_m
#     x = clamp(x, lo, hi)
#     v = int(round(x * scale))
#     return max(-32768, min(32767, v))


# def s16_to_f(v: int, step: float) -> float:
#     return float(v) * step


# # Unsigned 16-bit for angles (0..360) using wraparound mapping
# def angle_deg_to_u16(deg: float) -> int:
#     # Map degrees to [0, 65535], where 65536 corresponds to 360
#     turns = (deg / 360.0) % 1.0
#     return int(round(turns * 65535.0)) & 0xFFFF


# def u16_to_angle_deg(v: int) -> float:
#     return (float(v) / 65535.0) * 360.0


# # Velocity quantization: meters/sec into s16 with selectable step
# def vel_to_s16(v_ms: float, max_ms: float, step: float) -> int:
#     return f_to_s16(v_ms, max_ms, step)


# def s16_to_vel(v: int, step: float) -> float:
#     return s16_to_f(v, step)
