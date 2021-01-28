try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup

setup(
    name='defectdojo_cli',
    version='0.1.1',
    description='CLI Wrapper for DefectDojo using APIv2',
    url='https://github.com/adiffpirate/defectdojo_cli',
    author='Luiz Paulo Souto Monteiro',
    author_email='lpsmonteiro2@gmail.com',
    license='MIT',
    packages=['defectdojo_cli'],
    install_requires=['requests'],
    entry_points = {
        'console_scripts': ['defectdojo = defectdojo_cli.__main__:DefectDojoCLI'],
    }
)
