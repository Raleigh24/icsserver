from setuptools import setup, find_packages


def readme():
    with open('README.rst', 'r') as f:
        return f.read()


ics_version = open('ics/version.txt').read().strip()

setup(
    name='ICS',
    version=ics_version,
    description='Intelligent Cluster Server',
    long_description=readme(),
    author='Raleigh Waters',
    author_email='RaleighWaters@gmail.com',
    python_requires='>=3.5',
    packages=find_packages(),
    classifiers=[
        'Programming Language :: Python :: 3',
        'Operating System :: POSIX :: Linux',
    ],
    install_requires=[
        'Pyro4'
    ],
    install_package_data=True,
    package_data={
        "": ['templates/*.html', '*.conf', "version.txt"]
    },
    entry_points={
        'console_scripts': [
            'icsd = ics.icsd:main',
            'icsstart = ics.command_line:icsstart',
            'icsstop = ics.command_line:icsstop',
            'icssys = ics.command_line:icssys',
            'icsgrp = ics.command_line:icsgrp',
            'icsres = ics.command_line:icsres',
            'icsalert = ics.command_line:icsalert',
        ]
    }
)
