import setuptools
import os.path


# Load README
try:
    with open(os.path.join(
            os.path.dirname(__file__),
            'README.md'), 'rb') as f:
        README = f.read().decode('utf-8')
except IOError:
    README = ''

# Load the release notes
try:
    with open(os.path.join(
            os.path.dirname(__file__),
            'Release-notes.md'), 'rb') as f:
        CHANGES = f.read().decode('utf-8')
except IOError:
    CHANGES = ''

setuptools.setup(
    name='lash',
    version='1.1.0',
    author='Kevin Emmanuel',
    author_email='kevinho_gameplays@hotmail.com',
    description='Tools package to desktop',
    long_description=README + '\n\n' + CHANGES,
    long_description_content_type="text/markdown",
    url='https://github.com/KevBoyz/Lash',
    license='MIT',
    keywords='toll tolls toolkit keylogger autoclick zip organize files file-handler os random',
    python_requires=">=3.8",
    install_requires=[
        'click~=8.0.1',
        'pynput~=1.7.3',
        'keyboard~=0.13.5',
        'schedule~=1.1.0',
        'setuptools~=56.0.0',
        'playsound2~=0.1'
    ],
    packages=setuptools.find_packages(
        os.path.join(os.path.dirname(__file__))),
    zip_safe=True,
    data_files=[('additional_files', [r'lash\additional_files\beep.wav']),  # Non python files to pkg
                ('additional_files', [r'lash\additional_files\web_pkg.zip'])],
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
