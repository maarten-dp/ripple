from ripple.ecs.utils import IdGenerator
from ripple.utils import UInt16


def test_it_generates_sequential_ids():
    gen = IdGenerator()
    first = gen()
    second = gen()
    assert isinstance(first, UInt16)
    # sequential modulo 16-bit
    assert int(second) == (int(first) + 1) & 0xFFFF


def test_it_wraps_around():
    gen = IdGenerator()
    # move generator close to max
    gen.id = UInt16(0xFFFF)
    val = gen()
    assert int(val) == 0
