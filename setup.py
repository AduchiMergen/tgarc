from setuptools import setup

setup(
    name='tgarc',
    version='0.1.2',
    py_modules=['main'],
    install_requires=[
        'Click',
        'pyrogram @ git+https://github.com/AduchiMergen/pyrogram.git',
        'tgcrypto',
    ],
    entry_points={
        'console_scripts': [
            'tgarc = main:cli',
        ],
    },
)