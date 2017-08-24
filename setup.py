# -*- coding: utf-8 -*-
from setuptools import setup, find_packages

install_requires = [
  'ws4py==0.4.3.dev0',
  'soundfile>=0.9.0.post1',
  'pyaudio>=0.2.11',
]

dependency_links = [
  'git+https://github.com/hyperair/WebSocket-for-Python.git@fix-frame-spillover#egg=ws4py-0.4.3.dev0',
]

with open('README.md') as f:
    readme = f.read()

with open('LICENSE') as f:
    license = f.read()

tests_require = [
    'nose2',
    ]

setup(
    name='cpqdasr',
    version='0.1.0',
    description='CPqD ASR SDK implementation using websockets in Python',
    long_description=readme,
    install_requires=install_requires,
    dependency_links=dependency_links,
    tests_require=tests_require,
    test_suite='nose2.collector.collector',
    author='Akira Miasato',
    author_email='valterf@cpqd.com.br',
    url='https://github.com/CPqD/asr-sdk-python',
    license=license,
    packages=find_packages(exclude=('tests'))
)
