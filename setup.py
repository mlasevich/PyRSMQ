"""
Note that bulk of the configuation is in the package.cfg file
"""
import os.path

from setuptools import setup, find_packages

import ConfigParser


BASEDIR = os.path.dirname(__file__)

requirements = []
with open(os.path.join(BASEDIR, 'requirements.txt'), "r") as f:
    requirements = f.readlines()

# Read Package info from a CONFIG file package.cfg
CONFIG = ConfigParser.SafeConfigParser({})
CONFIG.add_section("Package")
CONFIG.add_section("FindPackages")
CONFIG.read(os.path.join(BASEDIR, 'package.cfg'))
PKG_INFO = dict(CONFIG.items('Package'))

FIND_PKGS = dict(CONFIG.items('FindPackages'))

for item in ['include', 'exclude']:
    if item in FIND_PKGS:
        FIND_PKGS[item] = FIND_PKGS[item].split(',')

PKG_INFO['packages'] = find_packages(**(FIND_PKGS))
PKG_INFO['package_dir'] = {'': 'src'}
PKG_INFO['install_requires'] = requirements

setup(**PKG_INFO)
