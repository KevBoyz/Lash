from setuptools import setup

setup(
    name='lash',
    version='1.0.0',
    author='Kevin Emmanuel',
    author_email='kevinho_gameplays@hotmail.com',
    packages=['lash'],
    description='Tools package to desktop',
    url='https://github.com/KevBoyz/Lash',
    license='MIT',
    keywords='toll tolls toolkit keylogger autoclick zip organize files file-handler os random',
    install_requires=[
        'click~=8.0.1',
        'pynput~=1.7.3',
        'keyboard~=0.13.5',
        'schedule~=1.1.0',
        'setuptools~=56.0.0'
    ],
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Programming Language :: Python :: 3.9',
        'Intended Audience :: End Users/Desktop',
        'License :: OSI Approved :: MIT License',
        'Natural Language :: English',
        'Operating System :: OS Independent',
        'Topic :: Desktop Environment :: File Managers'
    ]
)
