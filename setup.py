#!/usr/bin/env python

from setuptools import setup

with open("README.md") as readme:
    long_description = readme.read()

with open("requirements.txt") as f:
    install_requires = f.read().split()

setup(
    name='testnet',
    version='0.2',
    description='Docker based i2pd testnet',
    long_description=long_description,
    author='Darnet Villain',
    author_email='supervillain@riseup.net',
    url='https://github.com/l-n-s/i2pd-testnet-framework',
    keywords='i2p i2pd',
    license='MIT',
    classifiers=[
        'Development Status :: 4 - Beta',
        'License :: OSI Approved :: GNU General Public License v3 (GPLv3)',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
    ],
    packages=['testnet'],
    install_requires=install_requires,
    entry_points={
        'console_scripts': [
            'testnetctl=testnet.ctl:main',
        ],
    }
)
