import setuptools
import os.path


setuptools.setup(
    name='lash',
    version='1.1.1',
    author='Kevin Emmanuel',
    author_email='kevinho_gameplays@hotmail.com',
    description='Tools package to desktop',
    long_description='Check the README in github page (url)',
    url='https://github.com/KevBoyz/Lash',
    license='GPL-3.0',
    keywords='toll tolls toolkit keylogger autoclick zip organize files file-handler os random',
    python_requires=">=3.8",
    install_requires=[
        'click~=8.0.1',
        'pynput~=1.7.3',
        'keyboard~=0.13.5',
        'schedule~=1.1.0',
        'setuptools~=56.0.0',
        'playsound2~=0.1',
        'pyaes~=1.6.1'
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
