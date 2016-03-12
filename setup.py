try:
  from setuptools import setup
except ImportError:
  from distutils.core import setup


setup(
  name='RPiHTTPServer',
  author='Maurizio Manetti',
  author_email='maurizio@imanetti.net',
  version='0.0.1',
  url='http://github.com/mauntrelio/RPiHTTPServer',
  description='HTTP server eand request handler '
              'built on top of BaseHTTPServer '
              'intended for Raspberry Pi projects '
              'with a web interface',
  zip_safe=False,
  py_modules=['RPiHTTPServer'],
  license='MIT'
)
