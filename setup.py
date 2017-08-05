import os

long_description = """HTTP server and request handler built on top of BaseHTTPServer
intended for Raspberry Pi projects with a web interface"""

if os.path.exists('README.rst'):
    long_description = open('README.rst').read()
try:
  from setuptools import setup
except ImportError:
  from distutils.core import setup


setup(
  name='RPiHTTPServer',
  author='Maurizio Manetti',
  author_email='maurizio@imanetti.net',
  version='0.4.1',
  url='http://github.com/mauntrelio/RPiHTTPServer',
  long_description=long_description,
  description='HTTP server and request handler '
              'built on top of BaseHTTPServer '
              'intended for Raspberry Pi projects '
              'with a web interface',
  zip_safe=False,
  py_modules=['RPiHTTPServer'],
  license='MIT'
)
