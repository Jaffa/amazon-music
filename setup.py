import sys
import platform
from setuptools import setup, find_packages
from distutils.errors import DistutilsPlatformError
from amazonmusic import VERSION

install_requires = [
    'beautifulsoup4>=4.6.3',
    'requests>=2.21.0',
]

setup(
    name='amazonmusic',
    version=VERSION,
    description='A reversed engineered python API for amazon music',
    long_description=open('README.md', 'r').read(),
    author='Dmitry Petrov',
    author_email='',
    download_url='https://www.github.com/Jaffa/amazon-music',
    license='Apache License 2.0',
    install_requires=install_requires,
    keywords='',
    classifiers=[
    ],
    packages=find_packages(exclude=['tests', 'examples']),
    include_package_data=True,
    url='https://www.github.com/Jaffa/amazon-music'
)
