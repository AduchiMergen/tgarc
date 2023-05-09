from setuptools import setup

setup(
    name='tgarc',
    version='0.1.4',
    py_modules=['main'],
    install_requires=[
        'pick',
        'Click',
        'pyrogram',
        'tgcrypto',
    ],
    entry_points={
        'console_scripts': [
            'tgarc = main:cli',
        ],
    },
)