from distutils.core import setup
import py2exe

setup(console=['pull.py'], requires=['docopt', 'schema', 'py2exe'])