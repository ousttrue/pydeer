import sys
import pathlib
from typing import List
import setuptools
from enum import Enum
import logging
import subprocess


class ExtType(Enum):
    CYTHON = 'cython'
    RAWTYPES = 'rawtypes'


def generate(EXTERNAL_DIR: pathlib.Path, PACKAGE_DIR: pathlib.Path, EXT_TYPE: ExtType):
    #
    # init clang.cindex
    #
    # generate pyd, pyx, pyi from imgui.h
    try:
        from clang import cindex
    except:
        # get clang
        import _external.pycindex.setup

    from generator.header import Header  # nopep8
    #
    logging.basicConfig(level=logging.DEBUG,
                        format='[%(levelname)s]%(name)s:%(lineno)s:%(message)s')

    headers: List[Header] = [
        # Header(
        #     EXTERNAL_DIR, 'tinygizmo/tinygizmo/tiny-gizmo.hpp',
        #     include_dirs=[EXTERNAL_DIR / 'tinygizmo/tinygizmo'], prefix='tinygizmo_'),
        Header(
            EXTERNAL_DIR, 'imgui/imgui.h',
            include_dirs=[EXTERNAL_DIR / 'imgui']),
        Header(
            EXTERNAL_DIR, 'ImFileDialogWrap.h',
            include_dirs=[EXTERNAL_DIR]),
        # Header(
        #     EXTERNAL_DIR, 'ImGuizmo/ImGuizmo.h',
        #     include_dirs=[EXTERNAL_DIR / 'ImGuizmo'], prefix='ImGuizmo_'),
    ]

    import generator  # noqa

    if EXT_TYPE == ExtType.RAWTYPES:
        from generator.rawtypes_writer import write
    elif EXT_TYPE == ExtType.CYTHON:
        from generator.cython_writer import write
    else:
        raise RuntimeError()

    generator.generate(headers, PACKAGE_DIR, write)

    return headers


def build_static(build_type: str):
    # build imgui to build/Release/lib/imgui.lib
    import vcenv  # search setup vc path
    subprocess.run(
        f'cmake -S . -B build -G Ninja -DCMAKE_BUILD_TYPE={build_type}')
    subprocess.run(f'cmake --build build --config {build_type}')


def get_extensions(
        HERE: pathlib.Path,
        EXTERNAL_DIR: pathlib.Path,
        PACKAGE_DIR: pathlib.Path,
        CMAKE_BUILD: pathlib.Path,
        EXT_TYPE: ExtType) -> List[setuptools.Extension]:

    headers = generate(EXTERNAL_DIR, PACKAGE_DIR, EXT_TYPE)

    def rel_path(src: pathlib.Path) -> str:
        return str(src.relative_to(HERE)).replace('\\', '/')

    build_type = "Release"
    if '--debug' in sys.argv:
        build_type = "Debug"

    try:
        build_static(build_type)
    except:
        pass

    extensions: List[setuptools.Extension] = []
    if EXT_TYPE == ExtType.RAWTYPES:
        extensions = [setuptools.Extension(
            'pydeer.impl',
            sources=[
                # generated
                rel_path(PACKAGE_DIR / 'rawtypes/implmodule.cpp'),
            ],
            include_dirs=[
                str(include_dir) for header in headers for include_dir in header.include_dirs],
            language='c++',
            extra_compile_args=['/wd4244', '/std:c++17'],
            # cmake built
            libraries=["imgui", "Advapi32", "Gdi32"],
            library_dirs=[
                str(CMAKE_BUILD / f'{build_type}/lib')],
        )]

    elif EXT_TYPE == ExtType.CYTHON:
        extensions = [setuptools.Extension(
            'pydeer.impl',
            sources=[
                # generated
                rel_path(PACKAGE_DIR / 'impl/impl.pyx'),
            ],
            include_dirs=[
                str(include_dir) for header in headers for include_dir in header.include_dirs],
            language='c++',
            extra_compile_args=['/wd4244', '/std:c++17'],
            # cmake built
            libraries=["imgui", "Advapi32", "Gdi32"],
            library_dirs=[
                str(CMAKE_BUILD / 'Release/lib')],
        )]
        from Cython.Build import cythonize
        extensions = cythonize(extensions, compiler_directives={
            'language_level': '3'})

    else:
        raise RuntimeError()

    return extensions
