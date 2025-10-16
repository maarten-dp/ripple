from ripple.utils.int_types import UInt8, UInt16


def test_uint8_initialization():
    u = UInt8(42)
    assert u.value == 42


def test_uint8_overflow_on_init():
    u = UInt8(256)
    assert u.value == 0


def test_uint8_wrapping():
    u = UInt8(255)
    assert u.value == 255


def test_uint8_negative_wrapping():
    u = UInt8(-1)
    assert u.value == 255


def test_uint8_from_uint8():
    u1 = UInt8(100)
    u2 = UInt8(u1)
    assert u2.value == 100


def test_uint16_initialization():
    u = UInt16(1000)
    assert u.value == 1000


def test_uint16_overflow_on_init():
    u = UInt16(65536)
    assert u.value == 0


def test_uint16_wrapping():
    u = UInt16(65535)
    assert u.value == 65535


def test_uint8_add():
    u1 = UInt8(100)
    u2 = UInt8(50)
    result = u1 + u2
    assert result.value == 150
    assert isinstance(result, UInt8)


def test_uint8_add_overflow():
    u1 = UInt8(200)
    u2 = UInt8(100)
    result = u1 + u2
    assert result.value == 44


def test_uint8_add_int():
    u = UInt8(100)
    result = u + 50
    assert result.value == 150


def test_uint8_radd():
    u = UInt8(100)
    result = 50 + u
    assert result.value == 150


def test_uint8_iadd():
    u = UInt8(100)
    u += 50
    assert u.value == 150


def test_uint8_iadd_overflow():
    u = UInt8(200)
    u += 100
    assert u.value == 44


def test_uint8_sub():
    u1 = UInt8(100)
    u2 = UInt8(50)
    result = u1 - u2
    assert result.value == 50


def test_uint8_sub_underflow():
    u1 = UInt8(50)
    u2 = UInt8(100)
    result = u1 - u2
    assert result.value == 206


def test_uint8_rsub():
    u = UInt8(50)
    result = 100 - u
    assert result.value == 50


def test_uint8_isub():
    u = UInt8(100)
    u -= 50
    assert u.value == 50


def test_uint8_mul():
    u1 = UInt8(10)
    u2 = UInt8(5)
    result = u1 * u2
    assert result.value == 50


def test_uint8_mul_overflow():
    u1 = UInt8(20)
    u2 = UInt8(20)
    result = u1 * u2
    assert result.value == 144


def test_uint8_rmul():
    u = UInt8(10)
    result = 5 * u
    assert result.value == 50


def test_uint8_imul():
    u = UInt8(10)
    u *= 5
    assert u.value == 50


def test_uint8_truediv():
    u1 = UInt8(100)
    u2 = UInt8(5)
    result = u1 / u2
    assert result.value == 20


def test_uint8_truediv_truncate():
    u1 = UInt8(100)
    u2 = UInt8(7)
    result = u1 / u2
    assert result.value == 14


def test_uint8_rtruediv():
    u = UInt8(5)
    result = 100 / u
    assert result.value == 20


def test_uint8_itruediv():
    u = UInt8(100)
    u /= 5
    assert u.value == 20


def test_uint8_floordiv():
    u1 = UInt8(100)
    u2 = UInt8(7)
    result = u1 // u2
    assert result.value == 14


def test_uint8_rfloordiv():
    u = UInt8(7)
    result = 100 // u
    assert result.value == 14


def test_uint8_ifloordiv():
    u = UInt8(100)
    u //= 7
    assert u.value == 14


def test_uint8_mod():
    u1 = UInt8(100)
    u2 = UInt8(7)
    result = u1 % u2
    assert result.value == 2


def test_uint8_rmod():
    u = UInt8(7)
    result = 100 % u
    assert result.value == 2


def test_uint8_imod():
    u = UInt8(100)
    u %= 7
    assert u.value == 2


def test_uint8_pow():
    u1 = UInt8(2)
    u2 = UInt8(3)
    result = u1**u2
    assert result.value == 8


def test_uint8_pow_overflow():
    u1 = UInt8(10)
    u2 = UInt8(3)
    result = u1**u2
    assert result.value == 232


def test_uint8_rpow():
    u = UInt8(3)
    result = 2**u
    assert result.value == 8


def test_uint8_ipow():
    u = UInt8(2)
    u **= 3
    assert u.value == 8


def test_uint8_and():
    u1 = UInt8(0b11110000)
    u2 = UInt8(0b10101010)
    result = u1 & u2
    assert result.value == 0b10100000


def test_uint8_rand():
    u = UInt8(0b10101010)
    result = 0b11110000 & u
    assert result.value == 0b10100000


def test_uint8_iand():
    u = UInt8(0b11110000)
    u &= 0b10101010
    assert u.value == 0b10100000


def test_uint8_or():
    u1 = UInt8(0b11110000)
    u2 = UInt8(0b10101010)
    result = u1 | u2
    assert result.value == 0b11111010


def test_uint8_ror():
    u = UInt8(0b10101010)
    result = 0b11110000 | u
    assert result.value == 0b11111010


def test_uint8_ior():
    u = UInt8(0b11110000)
    u |= 0b10101010
    assert u.value == 0b11111010


def test_uint8_xor():
    u1 = UInt8(0b11110000)
    u2 = UInt8(0b10101010)
    result = u1 ^ u2
    assert result.value == 0b01011010


def test_uint8_rxor():
    u = UInt8(0b10101010)
    result = 0b11110000 ^ u
    assert result.value == 0b01011010


def test_uint8_ixor():
    u = UInt8(0b11110000)
    u ^= 0b10101010
    assert u.value == 0b01011010


def test_uint8_lshift():
    u = UInt8(0b00001111)
    result = u << 2
    assert result.value == 0b00111100


def test_uint8_lshift_overflow():
    u = UInt8(0b11110000)
    result = u << 2
    assert result.value == 0b11000000


def test_uint8_rlshift():
    u = UInt8(2)
    result = 0b00001111 << u
    assert result.value == 0b00111100


def test_uint8_ilshift():
    u = UInt8(0b00001111)
    u <<= 2
    assert u.value == 0b00111100


def test_uint8_rshift():
    u = UInt8(0b11110000)
    result = u >> 2
    assert result.value == 0b00111100


def test_uint8_rrshift():
    u = UInt8(2)
    result = 0b11110000 >> u
    assert result.value == 0b00111100


def test_uint8_irshift():
    u = UInt8(0b11110000)
    u >>= 2
    assert u.value == 0b00111100


def test_uint8_invert():
    u = UInt8(0b11110000)
    result = ~u
    assert result.value == 0b00001111


def test_uint8_neg():
    u = UInt8(10)
    result = -u
    assert result.value == 246


def test_uint8_pos():
    u = UInt8(10)
    result = +u
    assert result.value == 10


def test_uint8_abs():
    u = UInt8(10)
    result = abs(u)
    assert result.value == 10


def test_uint8_eq_uint8():
    u1 = UInt8(100)
    u2 = UInt8(100)
    assert u1 == u2


def test_uint8_eq_int():
    u = UInt8(100)
    assert u == 100


def test_uint8_ne():
    u1 = UInt8(100)
    u2 = UInt8(50)
    assert u1 != u2


def test_uint8_lt():
    u1 = UInt8(50)
    u2 = UInt8(100)
    assert u1 < u2


def test_uint8_le():
    u1 = UInt8(50)
    u2 = UInt8(100)
    assert u1 <= u2
    assert UInt8(100) <= UInt8(100)


def test_uint8_gt():
    u1 = UInt8(100)
    u2 = UInt8(50)
    assert u1 > u2


def test_uint8_ge():
    u1 = UInt8(100)
    u2 = UInt8(50)
    assert u1 >= u2
    assert UInt8(100) >= UInt8(100)


def test_uint8_int():
    u = UInt8(100)
    assert int(u) == 100


def test_uint8_float():
    u = UInt8(100)
    assert float(u) == 100.0


def test_uint8_bool_true():
    u = UInt8(100)
    assert bool(u) is True


def test_uint8_bool_false():
    u = UInt8(0)
    assert bool(u) is False


def test_uint8_index():
    u = UInt8(5)
    lst = [0, 1, 2, 3, 4, 5, 6]
    assert lst[u] == 5


def test_uint8_repr():
    u = UInt8(100)
    assert repr(u) == "UInt8(100)"


def test_uint8_str():
    u = UInt8(100)
    assert str(u) == "100"


def test_uint8_format():
    u = UInt8(255)
    assert f"{u:02x}" == "ff"


def test_uint8_hash():
    u1 = UInt8(100)
    u2 = UInt8(100)
    assert hash(u1) == hash(u2)


def test_uint8_in_set():
    u1 = UInt8(100)
    u2 = UInt8(100)
    u3 = UInt8(50)
    s = {u1, u3}
    assert u2 in s
    assert len(s) == 2


def test_uint16_add():
    u1 = UInt16(30000)
    u2 = UInt16(20000)
    result = u1 + u2
    assert result.value == 50000
    assert isinstance(result, UInt16)


def test_uint16_add_overflow():
    u1 = UInt16(60000)
    u2 = UInt16(10000)
    result = u1 + u2
    assert result.value == 4464


def test_uint16_sub():
    u1 = UInt16(30000)
    u2 = UInt16(10000)
    result = u1 - u2
    assert result.value == 20000


def test_uint16_mul():
    u1 = UInt16(100)
    u2 = UInt16(200)
    result = u1 * u2
    assert result.value == 20000


def test_uint16_lshift():
    u = UInt16(0b0000000011111111)
    result = u << 8
    assert result.value == 0b1111111100000000


def test_uint16_lshift_overflow():
    u = UInt16(0b1111111100000000)
    result = u << 8
    assert result.value == 0


def test_uint16_rshift():
    u = UInt16(0b1111111100000000)
    result = u >> 8
    assert result.value == 0b0000000011111111


def test_uint16_and():
    u1 = UInt16(0b1111111100000000)
    u2 = UInt16(0b1010101010101010)
    result = u1 & u2
    assert result.value == 0b1010101000000000


def test_uint16_repr():
    u = UInt16(1000)
    assert repr(u) == "UInt16(1000)"


def test_uint8_comparison_with_int():
    u = UInt8(100)
    assert u < 200
    assert u > 50
    assert u == 100


def test_uint16_comparison_with_int():
    u = UInt16(1000)
    assert u < 2000
    assert u > 500
    assert u == 1000
