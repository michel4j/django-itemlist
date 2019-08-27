import os
from setuptools import find_packages, setup

with open(os.path.join(os.path.dirname(__file__), 'README.rst')) as readme:
    README = readme.read()

# allow setup.py to be run from any path
os.chdir(os.path.normpath(os.path.join(os.path.abspath(__file__), os.pardir)))


setup(
    name='django-itemlist',
    version='0.2.0',
    packages=find_packages(),
    url='https://github.com/michel4j/django-itemlist',
    include_package_data=True,
    license='MIT License',
    author='Michel Fodje',
    author_email='michel4j@gmail.com',
    description='A customizable Django Admin ChangeList-like app for use outside of the admin.',
    long_description=README,
    long_description_content_type='text/x-rst',
    classifiers=[
        'Environment :: Web Environment',
        'Framework :: Django',
        'Framework :: Django :: 2.2',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3.7',
        'Topic :: Internet :: WWW/HTTP',
        'Topic :: Internet :: WWW/HTTP :: Dynamic Content',
    ],
)
