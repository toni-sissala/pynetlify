#!/usr/bin/env python3

from setuptools import setup, find_packages


setup(
    name='pynetlify',
    version='0.0.1',
    url='',
    description='Client and library to interact with Netlify API.',
    author='Toni Sissala',
    author_email='toni.sissala@gmail.com',
    packages=find_packages(),
    install_requires=[
        'requests'
    ]
)
