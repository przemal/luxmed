from os import path
from typing import List

from setuptools import find_packages
from setuptools import setup


here = path.abspath(path.dirname(__file__))


def read_requirements(file_name: str) -> List:
    with open(path.join(here, file_name)) as f:
        return f.read().splitlines()


with open(path.join(here, 'docs', 'README.md')) as f:
    long_description = f.read()
install_requires = read_requirements('requirements.txt')
tests_require = read_requirements('requirements-test.txt')


setup(
    name='luxmed',
    version='0.0',
    author='Przemysław Palacz',
    author_email='pprzemal@gmail.com',
    description='LUX MED Group patient portal (unofficial) API client',
    long_description=long_description,
    long_description_content_type='text/markdown',
    keywords='luxmed api client',
    license='MIT',
    url='https://github.com/przemal/luxmed',
    packages=find_packages(exclude=['tests']),
    python_requires='>=3.6',
    install_requires=install_requires,
    tests_require=tests_require)
