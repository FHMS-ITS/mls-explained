from setuptools import setup, find_packages

setup(
    name='mls-dir-dirserver',
    packages=find_packages(),
    install_requires=[],
    entry_points = {
        'console_scripts': [
            'mls-dir-dirserver = dirserver.server:main'
        ]
    }
)