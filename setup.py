import setuptools


def readme():
    with open('README.rst', 'r') as f:
        return f.read()


setuptools.setup(
    name='ICS',
    version='2.0.0.dev1',
    description='Intelsat Cluster Server',
    long_description=readme(),
    author='Raleigh Waters',
    author_email='Raleigh.Waters@intelsat.com',
    python_requires='>=3.0',
    packages=setuptools.find_packages(),
    classifiers=[
        'Programming Language :: Python :: 3',
        'Operating System :: POSIX :: Linux',
    ],
    install_requires=[
        'Pyro4'
    ],
    entry_points={
        'console_scripts': [
            'icsstart = ics.command_line:icsstart',
            'icsstop = ics.command_line:icsstop',
            'icssys = ics.command_line:icssys',
            'icsgrp = ics.command_line:icsgrp',
            'icsres = ics.command_line:icsres',
        ]
    }
)
