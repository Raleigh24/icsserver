import sys

from setuptools import setup

python_version = sys.version_info[:2]

if python_version < (2, 7):
    raise RuntimeError('ICS requires Python 2.7 or later')
elif (3, 0) < python_version:
    raise RuntimeError('ICS does not currently support Python 3')


setup(
    name='ICS',
    version='1.2.2',
    packages=[''],
    package_dir={'': 'ics'},
    url='',
    license='',
    author='waterr',
    author_email='Raleigh.Waters@intelsat.com',
    description=''
)
