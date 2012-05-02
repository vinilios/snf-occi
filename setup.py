from setuptools import setup

setup(
    name='snf-occi',
    version='0.1',
    description='OCCI to Openstack/Cyclades API bridge',
    url='http://code.grnet.gr/projects/snf-occi',
    license='BSD',
    packages = ['snfOCCI'],
    entry_points = {
        'console_scripts' : ['snf-occi = snfOCCI.APIserver:main']
        }

    )
