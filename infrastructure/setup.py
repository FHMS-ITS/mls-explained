"""
Setup-Datei für Auth-Server
"""

from setuptools import setup, find_packages

setup(
    name='mls-auth-server',
    packages=find_packages(),
    install_requires=[],
    entry_points={
        'console_scripts': [
            'mls-auth-server = authserver.server:main',
            'mls-dir-server = dirserver.server:main',
            'mls-chat-client-gui = chatclient.client_gui:main',
            'mls-chat-client-tui = chatclient.client_tui:main'
        ]
    },
    setup_requires=['pytest-runner'],
    tests_require=['pytest', 'pytest-pylint', 'pylint'],
)
