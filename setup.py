# -*- coding: utf-8 -*-

# Learn more: https://github.com/kennethreitz/setup.py

from setuptools import setup, find_packages


with open('README.rst') as f:
    readme = f.read()

with open('LICENSE') as f:
    license = f.read()

setup(
    name='semodbus2domoticz',
    version='0.1.0',
    description='python port of https://github.com/tjko/sunspec-monitor',
    long_description=readme,
    author='Geert Kroone',
    author_email='geert@kroone.net',
    url='https://github.com/gkroone/semodbus2domoticz',
    license=license,
    packages=find_packages(exclude=('tests', 'docs'))
)

data_files=[
    ('/usr/local/bin', ['semodbus2domoticz/semodbus2domoticz.py'])
    ]

