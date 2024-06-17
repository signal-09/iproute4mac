from setuptools import setup, find_packages
from pathlib import Path

THIS_DIRECTORY = Path(__file__).parent
VERSION = '0.1.0'
DESCRIPTION = 'iproute for Mac'
LONG_DESCRIPTION = (THIS_DIRECTORY / 'README.md').read_text()

setup(
    name = 'iproute4mac',
    version = VERSION,
    author = 'Ettore Simone',
    author_email = 'ettore.simone@gmail.com',
    description = DESCRIPTION,
    long_description = LONG_DESCRIPTION,
    long_description_content_type = 'text/markdown',
    license_files = ('LICENSE'),
    packages = find_packages('src'),
    install_requires = [],
    keywords = ['iproute2', 'ip', 'bridge'],
    url = 'https://github.com/signal-09/iproute4mac',
    project_urls = {
        'Source': 'https://github.com/signal-09/iproute4mac',
    },
    classifiers = [
        'Development Status :: 3 - Alpha',
        'Environment :: Console',
        'Intended Audience :: System Administrators',
        'License :: OSI Approved :: Apache Software License',
        'Operating System :: MacOS :: MacOS X',
        'Programming Language :: Python :: 3',
        'Topic :: System :: Networking',
    ],
    entry_points = {
        'console_scripts': [
            'ip = iproute4mac.ip:main',
            'bridge = iproute4mac.bridge:main',
        ],
    },
)
