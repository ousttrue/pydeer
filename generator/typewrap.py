from typing import NamedTuple, Optional, List
import logging
import re
from clang import cindex

logger = logging.getLogger(__name__)

TEMPLATE_PATTERN = re.compile(r'<[^>]+>')


def symbol_filter(src: str) -> str:
    '''
    fix python reserved word
    '''
    match src:
        case 'in' | 'id':
            return '_' + src
        case _:
            return src


def template_filter(src: str) -> str:
    '''
    replace Some<T> to Some[T]
    '''
    def rep_typearg(m):
        ret = f'[{m.group(0)[1:-1]}]'
        return ret
    dst = TEMPLATE_PATTERN.sub(rep_typearg, src)

    return dst


class TypeWrap(NamedTuple):
    '''
    function result_type
    function param type
    struct field type
    '''
    type: cindex.Type
    cursor: cindex.Cursor

    @staticmethod
    def from_function_result(cursor: cindex.Cursor):
        return TypeWrap(cursor.result_type, cursor)

    @staticmethod
    def from_function_param(cursor: cindex.Cursor):
        return TypeWrap(cursor.type, cursor)

    @staticmethod
    def get_function_params(cursor: cindex.Cursor):
        return [TypeWrap.from_function_param(child) for child in cursor.get_children() if child.kind == cindex.CursorKind.PARM_DECL]

    @staticmethod
    def from_struct_field(cursor: cindex.Cursor):
        return TypeWrap(cursor.type, cursor)

    @staticmethod
    def get_struct_fields(cursor: cindex.Cursor):
        return [TypeWrap.from_struct_field(child) for child in cursor.get_children(
        ) if child.kind == cindex.CursorKind.FIELD_DECL]

    @staticmethod
    def get_struct_methods(cursor: cindex.Cursor, *, excludes=(), includes=False):
        def method_filter(method: cindex.Cursor) -> bool:
            if method.spelling == 'GetStateStorage':
                pass
            if method.kind != cindex.CursorKind.CXX_METHOD:
                return False
            for param in method.get_children():
                if param.kind == cindex.CursorKind.PARM_DECL and param.type.spelling in excludes:
                    return False
            match includes:
                case True:
                    # return True
                    pass
                case False:
                    return False
                case (*methods,):
                    if method.spelling not in methods:
                        return False
                    else:
                        pass
            if method.result_type.spelling in excludes:
                return False
            return True
        return [child for child in cursor.get_children() if method_filter(child)]

    @staticmethod
    def get_constructors(cursor: cindex.Cursor) -> List[cindex.Cursor]:
        return [child for child in cursor.get_children() if child.kind == cindex.CursorKind.CONSTRUCTOR]

    @staticmethod
    def get_default_constructor(cursor: cindex.Cursor) -> Optional[cindex.Cursor]:
        for constructor in TypeWrap.get_constructors(cursor):
            params = TypeWrap.get_function_params(constructor)
            if len(params) == 0:
                return constructor

    @property
    def name(self) -> str:
        return symbol_filter(self.cursor.spelling)

    @property
    def is_void(self) -> bool:
        return self.type.kind == cindex.TypeKind.VOID

    @property
    def is_const(self) -> bool:
        if self.type.is_const_qualified():
            return True
        match self.type.kind:
            case cindex.TypeKind.POINTER | cindex.TypeKind.LVALUEREFERENCE:
                if self.type.get_pointee().is_const_qualified():
                    return True
        return False

    @property
    def c_type(self) -> str:
        '''
        pxd
        '''
        match self.type.spelling:
            case 'std::string':
                return 'string'
        return template_filter(self.type.spelling).replace('[]', '*')

    @property
    def c_type_with_name(self) -> str:
        '''
        pxd
        '''
        c_type = self.c_type
        name = self.name
        splitted = c_type.split('(*)', maxsplit=1)
        if len(splitted) == 2:
            return f"{splitted[0]}(*{name}){splitted[1]}"
        else:
            return f"{c_type} {name}"

    @property
    def _typedef_underlying_type(self) -> Optional['TypeWrap']:
        if self.type.spelling == 'size_t':
            return None
        match self.type.kind:
            case cindex.TypeKind.TYPEDEF:
                ref: cindex.Cursor = next(iter(
                    c for c in self.cursor.get_children() if c.kind == cindex.CursorKind.TYPE_REF))
                return TypeWrap(ref.referenced.underlying_typedef_type, ref.referenced)

            case _:
                return None

    @property
    def underlying_spelling(self) -> str:
        if self.type.kind == cindex.TypeKind.CONSTANTARRAY:
            tw = TypeWrap(self.type.get_array_element_type(), self.cursor)
            return f'{tw.underlying_spelling} [{self.type.get_array_size()}]'
        elif self.type.kind == cindex.TypeKind.POINTER:
            tw = TypeWrap(self.type.get_pointee(), self.cursor)
            if tw.underlying_spelling.endswith('*'):
                return f'{tw.underlying_spelling}*'
            else:
                return f'{tw.underlying_spelling} *'
        else:
            current = self
            while True:
                base = current._typedef_underlying_type
                if not base:
                    break
                current = base
            value = current.type.spelling
            if '(*)' in value:
                # fp
                return self.cursor.type.spelling
            return value

    @property
    def default_value(self) -> str:
        tokens = []
        for child in self.cursor.get_children():
            # logger.debug(child.spelling)
            match child.kind:
                case cindex.CursorKind.UNEXPOSED_EXPR | cindex.CursorKind.INTEGER_LITERAL | cindex.CursorKind.FLOATING_LITERAL | cindex.CursorKind.CXX_BOOL_LITERAL_EXPR | cindex.CursorKind.UNARY_OPERATOR | cindex.CursorKind.CALL_EXPR:
                    tokens = [
                        token.spelling for token in self.cursor.get_tokens()]
                    if '=' not in tokens:
                        tokens = []
                case cindex.CursorKind.TYPE_REF:
                    pass
                case _:
                    logger.debug(f'{self.cursor.spelling}: {child.kind}')

        if not tokens:
            return ''

        def token_filter(src: str) -> str:

            match src:
                case 'NULL':
                    return 'None'
                case 'true':
                    return 'True'
                case 'false':
                    return 'False'
                case 'FLT_MAX':
                    return '3.402823466e+38'
                case 'FLT_MIN':
                    return '1.175494351e-38'
                case _:
                    if src.startswith('"'):
                        # string literal
                        return 'b' + src
                    if re.search(r'[\d.]f$', src):
                        return src[:-1]

                    return src

        equal = tokens.index('=')
        value = ' '.join(token_filter(t) for t in tokens[equal+1:])
        return '= ' + value
