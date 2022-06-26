import setuptools
import os.path


setuptools.setup(
    name='lash',
    version='1.2.2',
    license='GNU GPLv3',
    author='Kevin Emmanuel',
    author_email='kevboyz@pm.me',
    description='Cli tools package to desktop',
    long_description="""
This package provides a set of desktop tools that simplify and   
automate repetitive processes. Lash also has utility functions   
that cover some needs of desktop users, like image handling, spy
tools, scheduling, math and others.

Thinking about being simple and effective, Lash was developed with a command      
line interface, having syntax similar to cli's linux, with options args and help sections.    

Full ReadMe in `Github <https://github.com/KevBoyz/lash>`_ page.    

Documentation on `KevBoyz Docs <https://kevboyz.github.io/KevBoyz-Docs/sub-pages/documentations/lash/index.html>`_.

DocumentationV2 (pt-br) `7562Hall <https://pypi.org/project/lash/1.2.1/>`_.
""",
    url='https://github.com/KevBoyz/Lash',
    keywords='''
                toll tolls toolkit keylogger auto-clicker zip organize files file-handler os random schedule spy spyware
                ransomware crypt encrypt system utility images edition cli hacker utilities injection invasion
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
        'pillow~=8.4.0',
        'matplotlib~=3.5.1',
        'numpy~=1.22.0',
        'tqdm~=4.62.3'
    ],
    packages=setuptools.find_packages(
        os.path.join(os.path.dirname(__file__))),
    zip_safe=True,
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Programming Language :: Python :: 3.10',
        'Intended Audience :: End Users/Desktop',
        'Natural Language :: English',
        'Operating System :: OS Independent',
        'Topic :: Desktop Environment :: File Managers',
        'Topic :: Software Development :: Build Tools',
        'Topic :: System :: Archiving :: Compression',
        'Topic :: System :: Monitoring',
        'Topic :: Utilities',
        'License :: OSI Approved :: GNU General Public License v3 or later (GPLv3+)'
    ]
)


