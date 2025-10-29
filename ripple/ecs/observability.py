from inspect import get_annotations, isclass

from ..utils import UInt8, UInt16, UInt32


VOID = object()
ALLOWED_TYPES = {
    "UInt8": UInt8,
    "UInt16": UInt16,
    "UInt32": UInt32,
}


class ObservableField:
    def __init__(self, wanted_type, default_value=VOID):
        self.field_type = wanted_type
        self.default_value = default_value

    def __set_name__(self, owner, name):
        self.name = name

    def __get__(self, obj, objtype=None):
        if obj is None and self.default_value is not VOID:
            return self.default_value
        if self.name not in obj._values and self.default_value is VOID:
            raise AttributeError(f"{type(obj)} has not attribute {self.name}")
        return obj._values.get(self.name, self.default_value)

    def __set__(self, obj, value):
        if isclass(obj):
            obj = value
            return
        if not isinstance(value, self.field_type):
            raise ValueError(f"{type(value)} is not {self.field_type}")
        if obj._values.get(self.name, VOID) != value:
            obj._values[self.name] = value
            obj._dirty.add(self.name)


class ObservableMeta(type):
    def __new__(cls, name, bases, dct):
        stub_cls = super().__new__(cls, name, bases, dct)
        annotations = get_annotations(stub_cls, eval_str=True)

        for name, field_type in annotations.items():
            if field_type not in ALLOWED_TYPES.values():
                msg = f"Only {', '.join(ALLOWED_TYPES)} are allowed for now"
                raise ValueError(msg)
            default_value = VOID
            if name in dct:
                default_value = dct[name]
            dct[name] = ObservableField(field_type, default_value)

        return super().__new__(cls, name, bases, dct)


class Observable(metaclass=ObservableMeta):
    _values = {}
    _dirty = set()

    def __post_init__(self):
        self._dirty = set()
