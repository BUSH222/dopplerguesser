from setuptools import setup, Extension
import pybind11

ext_modules = [
    Extension(
        'pll._dpll_ext',
        ['pll/_dpll_ext.cpp'],
        include_dirs=[pybind11.get_include()],
        language='c++'
    ),
]

setup(
    name='dopplerguesser_ext',
    ext_modules=ext_modules,
)
