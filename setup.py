#!/usr/bin/env python

import os
import sys
import re

try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup

if sys.argv[-1] == "publish":
    os.system("python3 setup.py sdist upload")
    sys.exit()

elif sys.argv[-1] == "test":
    os.system("./run_tests.py")
    sys.exit()

#elif sys.argv[-1] in ("docs", "doc"):
#    os.system("sphinx-build doc/ doc/_build")
#    sys.exit()

def readfile(*fname):
    """Read local file content."""
    return open(os.path.join(os.path.dirname(__file__), *fname)).read()

def getvalue(content, name):
    """Get value of simple assigment, e.g. var = 'val'."""
    r = re.search(r'''(?m)^\s*{}\s*=\s*(['"])(?P<val>.*?)\1'''.format(re.escape(name)), content)
    return r.group('val') if r else ''

# content of pdom/__init__.py
pdom_init = readfile('pdom', '__init__.py')

setup(
    name='pdom',
    version=getvalue(readfile('pdom', 'version.py'), 'version'),
    description='Simple DOM regex parser',
    long_description=readfile('README.md'),
    long_description_content_type="text/markdown",
    author=getvalue(pdom_init, '__author__'),
    author_email=getvalue(pdom_init, '__email__'),
    url=getvalue(pdom_init, '__url__'),
    package_data={'': ['LICENSE']},
    package_dir={'pdom': 'pdom'},
    packages = ['pdom'],
    include_package_data=True,
    zip_safe=True,
    platforms = "any",
    install_requires=[
        'arpeggio',
    ],
    license='MIT',
    #entry_points={
    #    "console_scripts": [
    #        "pdom = pdom.main:main"
    #    ]
    #},
    scripts = ["bin/pdom-run.sh"],
    classifiers=(
        'Development Status :: 5 - Production/Stable',
        'Intended Audience :: Developers',
        'Natural Language :: English',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3.5',
    ),
)
