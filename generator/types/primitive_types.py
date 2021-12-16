from typing import Iterable
from .basetype import BaseType


class VoidType(BaseType):
    def __init__(self):
        super().__init__('void')

    @property
    def py_typing(self) -> Iterable[str]:
        yield 'None'


class BoolType(BaseType):
    def __init__(self):
        super().__init__('bool')

    @property
    def py_typing(self) -> Iterable[str]:
        yield 'bool'

    @property
    def field_ctypes_type(self) -> str:
        return 'ctypes.c_bool'


class UInt8Type(BaseType):
    def __init__(self):
        super().__init__('unsigned char')

    @property
    def py_typing(self) -> Iterable[str]:
        yield 'int'

    @property
    def field_ctypes_type(self) -> str:
        return 'ctypes.c_uint8'


class UInt16Type(BaseType):
    def __init__(self):
        super().__init__('unsigned short')

    @property
    def py_typing(self) -> Iterable[str]:
        yield 'int'

    @property
    def field_ctypes_type(self) -> str:
        return 'ctypes.c_uint16'


class UInt32Type(BaseType):
    def __init__(self):
        super().__init__('unsigned int')

    @property
    def py_typing(self) -> Iterable[str]:
        yield 'int'

    @property
    def field_ctypes_type(self) -> str:
        return 'ctypes.c_uint32'


class UInt64Type(BaseType):
    def __init__(self):
        super().__init__('unsigned long long')

    def match(self, spelling: str) -> bool:
        '''
        process if True
        '''
        if spelling == 'size_t':
            # cython cannot: size_t * = unsigned long long *
            return True
        return spelling == self.c_type

    @property
    def py_typing(self) -> Iterable[str]:
        yield 'int'

    @property
    def field_ctypes_type(self) -> str:
        return 'ctypes.c_uint64'


class Int8Type(BaseType):
    def __init__(self):
        super().__init__('char')

    @property
    def py_typing(self) -> Iterable[str]:
        yield 'int'

    @property
    def field_ctypes_type(self) -> str:
        return 'ctypes.c_int8'


class Int16Type(BaseType):
    def __init__(self):
        super().__init__('short')

    @property
    def py_typing(self) -> Iterable[str]:
        yield 'int'

    @property
    def field_ctypes_type(self) -> str:
        return 'ctypes.c_int16'


class Int32Type(BaseType):
    def __init__(self):
        super().__init__('int')

    @property
    def py_typing(self) -> Iterable[str]:
        yield 'int'

    @property
    def field_ctypes_type(self) -> str:
        return 'ctypes.c_int32'


class FloatType(BaseType):
    def __init__(self):
        super().__init__('float')

    @property
    def py_typing(self) -> Iterable[str]:
        yield 'float'

    @property
    def field_ctypes_type(self) -> str:
        return 'ctypes.c_float'


class DoubleType(BaseType):
    def __init__(self):
        super().__init__('double')

    @property
    def py_typing(self) -> Iterable[str]:
        yield 'float'

    @property
    def field_ctypes_type(self) -> str:
        return 'ctypes.c_double'
