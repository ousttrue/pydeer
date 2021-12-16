from typing import NamedTuple, Tuple
import io
from clang import cindex
from .typewrap import TypeWrap
from .types.wrap_types import WrapFlags
from . import function
from generator import typeconv


def is_forward_declaration(cursor: cindex.Cursor) -> bool:
    '''
    https://joshpeterson.github.io/identifying-a-forward-declaration-with-libclang    
    '''
    definition = cursor.get_definition()

    # If the definition is null, then there is no definition in this translation
    # unit, so this cursor must be a forward declaration.
    if not definition:
        return True

    # If there is a definition, then the forward declaration and the definition
    # are in the same translation unit. This cursor is the forward declaration if
    # it is _not_ the definition.
    return cursor != definition


class StructDecl(NamedTuple):
    cursors: Tuple[cindex.Cursor, ...]

    @property
    def cursor(self) -> cindex.Cursor:
        return self.cursors[-1]

    def write_pxd(self, pxd: io.IOBase, *, excludes=()):
        cursor = self.cursors[-1]

        constructors = [child for child in cursor.get_children(
        ) if child.kind == cindex.CursorKind.CONSTRUCTOR]

        methods = TypeWrap.get_struct_methods(
            cursor, excludes=excludes, includes=True)
        if cursor.kind == cindex.CursorKind.CLASS_TEMPLATE:
            pxd.write(f'    cppclass {cursor.spelling}[T]')
        elif constructors or methods:
            pxd.write(f'    cppclass {cursor.spelling}')
        else:
            definition = cursor.get_definition()
            if definition and any(child for child in definition.get_children() if child.kind == cindex.CursorKind.CONSTRUCTOR):
                # forward decl
                pxd.write(f'    cppclass {cursor.spelling}')
            else:
                pxd.write(f'    struct {cursor.spelling}')

        fields = TypeWrap.get_struct_fields(cursor)
        if constructors or fields:
            pxd.write(':\n')

            for field in fields:
                pxd.write(f'        {field.c_type_with_name}\n')

            for child in constructors:
                function.write_pxd_constructor(pxd, cursor, child)

            for child in methods:
                function.write_pxd_method(pxd, child)

        pxd.write('\n')

    def write_pyx_ctypes(self, pyx: io.IOBase, *, flags: WrapFlags = WrapFlags('')):
        cursor = self.cursors[-1]

        definition = cursor.get_definition()
        if definition and definition != cursor:
            # skip forward decl
            return

        pyx.write(f'class {cursor.spelling}(ctypes.Structure):\n')
        fields = TypeWrap.get_struct_fields(cursor) if flags.fields else []
        if fields:
            pyx.write('    _fields_=[\n')
            for field in fields:
                pyx.write(
                    f'        ("{field.name}", {typeconv.get_field_type(field.underlying_spelling)}),\n')
            pyx.write('    ]\n\n')

        methods = TypeWrap.get_struct_methods(cursor, includes=flags.methods)
        if methods:
            for method in methods:
                function.write_pyx_method(pyx, cursor, method)

        for code in flags.custom_methods:
            for l in code.splitlines():
                pyx.write(f'    {l}\n')
            pyx.write('\n')

        if not fields and not methods and not flags.custom_methods:
            pyx.write('    pass\n\n')

    def write_pyi(self, pyi: io.IOBase, *, flags: WrapFlags = WrapFlags('')):
        cursor = self.cursors[-1]

        definition = cursor.get_definition()
        if definition and definition != cursor:
            # skip forward decl
            return

        pyi.write(f'class {cursor.spelling}(ctypes.Structure):\n')
        fields = TypeWrap.get_struct_fields(cursor) if flags.fields else []
        if fields:
            for field in fields:
                pyi.write(
                    f'    {field.name}: {typeconv.get_type(field.underlying_spelling).py_type}\n')
            pyi.write('\n')

        methods = TypeWrap.get_struct_methods(cursor, includes=flags.methods)
        if methods:
            for method in methods:
                function.write_pyx_method(pyi, cursor, method, pyi=True)

        for custom in flags.custom_methods:
            l = next(iter(custom.splitlines()))
            pyi.write(f'    {l} ...\n')

        if not fields and not methods:
            pyi.write('    pass\n\n')
