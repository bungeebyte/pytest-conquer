#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
from setuptools import setup

setup(
    name='maketestsgofaster',
    version=os.environ.get('RELEASE_VERSION', '1.0.0'),
    author='Stephan Behnke',
    author_email='maketestsgofaster@stephanbehnke.com',
    maintainer='Stephan Behnke',
    maintainer_email='maketestsgofaster@stephanbehnke.com',
    license='MIT',
    url='https://github.com/maketestsgofaster/python',
    description='Test framework plugin to parallize tests efficiently.',
    packages=[
        'maketestsgofaster',
        'maketestsgofaster.env',
        'maketestsgofaster.vendor',
        'maketestsgofaster.vendor.httplib2',
    ],
    package_data={
        'maketestsgofaster.vendor.httplib2': ['*.txt'],
    },
    entry_points={
        'pytest11': [
            'maketestsgofaster = maketestsgofaster.plugin',
        ],
    },
    install_requires=[
        'psutil>=5',
    ],
    classifiers=[
        'Framework :: Pytest',
        'Intended Audience :: Developers',
        'Topic :: Software Development :: Testing',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Operating System :: OS Independent',
        'License :: OSI Approved :: MIT License',
    ],
)
