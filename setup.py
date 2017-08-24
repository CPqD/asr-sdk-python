# -*- coding: utf-8 -*-
from setuptools import setup, find_packages


with open('README.rst') as f:
    readme = f.read()

with open('LICENSE') as f:
    license = f.read()

setup(
    name='cpqdasr',
    version='0.1.0',
    description='CPqD ASR SDK implementation using websockets in Python',
    long_description=readme,
    author='Akira Miasato',
    author_email='valterf@cpqd.com.br',
    url='https://github.com/CPqD/asr-sdk-python',
    license=license,
    packages=find_packages(exclude=('tests'))
)
