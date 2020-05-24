from setuptools import setup, find_packages

setup(
    name='toybox-extras',
    version='0.1.0',
    description='A Library of Toybox agents.',
    packages=find_packages(exclude='analysis'),
    package_data={
        'agents' : ['*.model']
    }
)