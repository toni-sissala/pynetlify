#!/usr/bin/env python3
#
# PyNetlify - Python client and library to interact with Netlify API.
# Copyright (C) 2019  Toni Sissala
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.

from setuptools import setup, find_packages


with open('README.rst') as fh:
    long_description = fh.read()


setup(
    name='pynetlify',
    version='0.1.1',
    url='https://github.com/toni-sissala/pynetlify',
    description='Client and library to interact with Netlify API.',
    long_description=long_description,
    long_description_content_type='text/x-rst',
    author='Toni Sissala',
    author_email='toni.sissala@gmail.com',
    packages=find_packages(),
    install_requires=[
        'requests'
    ],
    license='GPL v3',
    classifiers=(
        "Development Status :: 3 - Alpha",
        "Environment :: Console",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: GNU General Public License v3 (GPLv3)",
        "Programming Language :: Python",
        "Topic :: Internet :: WWW/HTTP :: Site Management",
        "Topic :: Software Development :: Libraries :: Python Modules"
    )
)
