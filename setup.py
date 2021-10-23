import setuptools
import os.path

# Load the read me ~ This code was taken from github.com/moses-palmer/pynput/blob/master/setup.py
try:
    with open(os.path.join(
            os.path.dirname(__file__),
            'README.rst'), 'rb') as f:
        README = f.read().decode('utf-8')
except IOError:
    README = ''
# End of code block


setuptools.setup(
    name='lash',
    version='1.1.3',
    author='Kevin Emmanuel',
    author_email='kevinho_gameplays@hotmail.com',
    description='Tools package to desktop',
    long_description='Please, check the README in the Homepage (url)',
    url='https://github.com/KevBoyz/Lash',
    keywords='''toll tolls toolkit keylogger autoclick zip organize files file-handler os random schedule spy spyware
             ransomware crypt encrypt system utility''',
    python_requires=">=3.8",
    install_requires=[
        'click~=8.0.1',
        'pynput~=1.7.3',
        'keyboard~=0.13.5',
        'schedule~=1.1.0',
        'setuptools~=56.0.0',
        'pyaes~=1.6.1'
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
