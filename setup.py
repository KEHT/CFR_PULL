from distutils.core import setup
import py2exe

setup(console=['cfr_pull.py'], requires=['docopt', 'schema'])