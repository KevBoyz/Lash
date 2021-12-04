import setuptools
import os.path


setuptools.setup(
    name='lash',
    version='1.2.0',
    author='Kevin Emmanuel',
    author_email='kevboyz@pm.me',
    description='Cli tools package to desktop',
    long_description="""
About lash
----------
This package provides a set of desktop tools that simplify and
automate repetitive processes. Lash also has utility functions
that cover some needs of desktop users.

Thought to be simple and effective, Lash was developed with a
command line interface that has self-help and semantic commands.

Access the full documentation on `KevBoyz Docs <https://kevboyz.github.io/KevBoyz-Docs/sub-pages/documentations/lash/index.html>`_
""",
    url='https://github.com/KevBoyz/Lash',
    keywords='''
                toll tolls toolkit keylogger auto-clicker zip organize files file-handler os random schedule spy spyware
                ransomware crypt encrypt system utility images edition cli hacker
             ''',
    python_requires=">=3.8",
    install_requires=[
        'click~=8.0.1',
        'pynput~=1.7.3',
        'keyboard~=0.13.5',
        'schedule~=1.1.0',
        'setuptools~=56.0.0',
        'pyaes~=1.6.1',
        'requests~=2.26.0',
        'bs4~=0.0.1',
    ],
    packages=setuptools.find_packages(
        os.path.join(os.path.dirname(__file__))),
    zip_safe=True,
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Programming Language :: Python :: 3.9',
        'Intended Audience :: End Users/Desktop',
        'Natural Language :: English',
        'Operating System :: OS Independent',
        'Topic :: Desktop Environment :: File Managers',
        'License :: OSI Approved :: GNU General Public License v3 or later (GPLv3+)'
    ]
)
