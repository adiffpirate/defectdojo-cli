try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup

setup(
    packages=['defectdojo_cli'],
    install_requires=['requests', 'tabulate'],
    entry_points = {
        'console_scripts': ['defectdojo = defectdojo_cli.__main__:main'],
    }
)
