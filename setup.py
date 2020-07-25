#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
from setuptools import setup

setup(
    name='pytest-conquer',
    version=os.environ.get('RELEASE_VERSION', '1.0.0'),
    author='Stephan Behnke',
    author_email='hello@testandconquer.com',
    maintainer='Stephan Behnke',
    maintainer_email='hello@testandconquer.com',
    license='MIT',
    url='https://github.com/testandconquer/pytest-conquer',
    description='pytest plugin to parallize tests efficiently.',
    packages=[
        'testandconquer',
        'testandconquer.vendor',
        'testandconquer.vendor.janus',
        'testandconquer.vendor.websockets',
        'testandconquer.vendor.websockets.extensions',
    ],
    entry_points={
        'pytest11': [
            'pytest-conquer = testandconquer.plugin',
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
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'Operating System :: OS Independent',
        'License :: OSI Approved :: MIT License',
    ],
)
