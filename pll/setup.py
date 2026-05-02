from setuptools import setup, Extension
import pybind11

ext_modules = [
    Extension(
        '_dpll_ext',
        ['_dpll_ext.cpp'],
        include_dirs=[pybind11.get_include()],
        language='c++'
    ),
]

setup(
    name='dpll_ext',
    ext_modules=ext_modules,
)
