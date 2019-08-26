from setuptools import setup
from os import path

with open(path.join(path.abspath(path.dirname(__file__)), 'README.rst'), 'r') as f:
    long_description = f.read()

setup(
    name='django-itemlist',
    version='0.1.0',
    packages=['itemlist'],
    url='https://github.com/michel4j/django-itemlist',
    license='MIT License',
    author='Michel Fodje',
    author_email='michel4j@gmail.com',
    description='A customizable Django Admin ChangeList-like app for use outside of the admin.',
    long_description=long_description,
    long_description_content_type='text/x-rst'
)
