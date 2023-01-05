import setuptools
import os.path


setuptools.setup(
    name='lash',
    version='1.2.6',
    license='GNU GPLv3',
    author='Kevin Pontes',
    author_email='kevboyz@pm.me',
    description='CLI tools package to desktop',
    long_description="""
This package provides a set of desktop tools that simplify and   
automate multiple processes. Lash also has utility functions   
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
                ransomware crypt encrypt system utility images edition cli hacker utilities injection invasion work
                management wikipedia youtube download music email github
             ''',
    python_requires=">=3.11",
    install_requires=[
        'setuptools>=65.5.0',
        'click>=8.1.3',
        'pynput>=1.7.6',
        'keyboard>=0.13.5',
        'schedule>=1.1.0',
        'bs4>=0.0.1',
        'Pillow>=9.3.0',
        'mss>=7.0.1',
        'opencv-python>=4.6.0.66',
        'pytube>=12.1.0',
        'moviepy>=1.0.3',
        'matplotlib>=3.6.1',
        'numpy>=1.23.4', 
        'tqdm>=4.64.1',
        'rich>=12.6.0',
        'py-dashing>=0.3.dev0',
        'pyaes>=1.6.1',
        'quick-mailer>=2022.2.22',
        'wikipedia>=1.4.0',
        'gnews>=0.2.7',
        'pyautogui>=0.9.53',
        'psutil>=5.9.3',
        'pandas>=1.5.1',
    ],
    packages=setuptools.find_packages(
        os.path.join(os.path.dirname(__file__))),
    zip_safe=True,
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Programming Language :: Python :: 3.11',
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
