#!/usr/bin/env python3
import functools
import pathlib
import re
import sys

from setuptools import find_packages, setup

try:  # for pip >= 10
    from pip._internal.req import parse_requirements
except ImportError:  # for pip <= 9.0.3
    from pip.req import parse_requirements

WORK_DIR = pathlib.Path(__file__).parent

# Check python version
MINIMAL_PY_VERSION = (3, 9)
if sys.version_info < MINIMAL_PY_VERSION:
    raise RuntimeError('eskiz-sms-client works only with Python 3.9+')


@functools.lru_cache()
def get_version():
    """
    Read version

    :return: str
    """
    txt = (WORK_DIR / 'eskiz' / '__init__.py').read_text('utf-8')
    try:
        return re.findall(r"^__version__ = '([^']+)'\r?$", txt, re.M)[0]
    except IndexError:
        raise RuntimeError('Unable to determine version.')


def get_description():
    """
    Read full description from 'README.md'

    :return: description
    :rtype: str
    """
    with open('README.md', 'r', encoding='utf-8') as f:
        return f.read()


@functools.lru_cache()
def get_requirements(filename=None):
    """
    Read requirements from 'requirements txt'

    :return: requirements
    :rtype: list
    """
    if filename is None:
        filename = 'requirements.txt'

    file = WORK_DIR / filename

    install_reqs = parse_requirements(str(file), session='hack')
    try:
        requirements = [str(ir.req) for ir in install_reqs]
    except:
        requirements = [str(ir.requirement) for ir in install_reqs]

    return requirements


setup(
    name='eskiz-sms-client',
    version=get_version(),
    packages=find_packages(exclude=('tests', 'tests.*', 'examples.*')),
    url='https://github.com/old-juniors/eskiz-sms',
    license='MIT',
    requires_python='>=3.9',
    author='Old Juniors',
    author_email='info@juniorlar.uz',
    maintainer=', '.join((
        'Old Juniors <info@juniorlar.uz>',
    )),
    maintainer_email='info@juniorlar.uz',
    description='Async/Sync Python Eskiz.uz SMS Gateway',
    long_description=get_description(),
    long_description_content_type='text/markdown',
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Environment :: Console',
        'Framework :: AsyncIO',
        'Intended Audience :: Developers',
        'Intended Audience :: System Administrators',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 3.9',
        'Topic :: Software Development :: Libraries :: Application Frameworks',
    ],
    install_requires=get_requirements(),

    # TODO
    # tests_require=get_requirements('dev-requirements.txt'),
    # extras_require={'dev': get_requirements('dev-requirements.txt')},
    # cmdclass={'test': PyTest}
)
