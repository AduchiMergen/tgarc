from setuptools import setup

setup(
    name='tgarc',
    version='0.1.3',
    py_modules=['main'],
    install_requires=[
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