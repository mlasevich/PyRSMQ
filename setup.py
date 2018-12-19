"""
Note that bulk of the configuation is in the package.cfg file
"""
try:
    import ConfigParser as configparser
except ImportError:
    import configparser

import os.path
from pprint import pprint

from setuptools import setup, find_packages


BASEDIR = os.path.dirname(__file__)

requirements = []
with open(os.path.join(BASEDIR, 'requirements.txt'), "r") as f:
    requirements = f.readlines()

with open("README.md", "r") as fh:
    long_description = fh.read()


# Read Package info from a CONFIG file package.cfg
CONFIG = configparser.ConfigParser({})
CONFIG.add_section("Package")
CONFIG.add_section("FindPackages")
CONFIG.read(os.path.join(BASEDIR, 'package.cfg'))
PKG_INFO = dict(CONFIG.items('Package'))

FIND_PKGS = dict(CONFIG.items('FindPackages'))

for item in ['include', 'exclude']:
    if item in FIND_PKGS:
        FIND_PKGS[item] = FIND_PKGS[item].split(',')

PKG_INFO.update({
    'packages': find_packages(**(FIND_PKGS)),
    'package_dir': {'': 'src'},
    'package_data': {'': ['/package.cfg*']},
    'install_requires': [req.strip() for req in requirements if not req.startswith('#')],
    'long_description': long_description,
    'long_description_content_type': "text/markdown",
    'classifiers': [
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: Apache Software License",
        "Operating System :: OS Independent",
    ]
})

setup(**PKG_INFO)
