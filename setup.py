#!/usr/bin/env python3
from setuptools import find_packages
from setuptools import setup


setup(
    name='aorta',
    version='1.0.1',
    description='AMQP Durable Messaging Library',
    author='Cochise Ruhulessin',
    author_email='c.ruhulessin@ibrb.org',
    url='https://www.ibrb.org',
    install_requires=[
        'pytz',
        'python-qpid-proton',
	'PyYAML',
    ],
    packages=find_packages()
)
