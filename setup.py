# Copyright (C) 2012-2015 GRNET S.A.
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.

from setuptools import setup

requires = ['kamaki>=0.13.1', 'webob', 'eventlet', 'python-ldap']

setup(
    name='snf-occi',
    version='0.3',
    description='OCCI to Openstack/Cyclades API bridge',
    url='https://github.com/grnet/snf-occi',
    license='GPLv3',
    packages=['snfOCCI', 'snfOCCI.snf_voms', 'snfOCCI.extensions', 'astavoms'],
    entry_points='''
        [paste.app_factory]
        snf_occi_app = snfOCCI:main
        ''',
    install_requires=requires,
    )
