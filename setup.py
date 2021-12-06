from setuptools import setup

setup(
    name='tgarc',
    version='0.1.1',
    py_modules=['main'],
    install_requires=[
        'Click',
        'Pyrogram',
        'tgcrypto',
    ],
    entry_points={
        'console_scripts': [
            'tgarc = main:cli',
        ],
    },
)