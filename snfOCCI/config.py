# Copyright (C) 2012-2014 GRNET S.A.
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


SERVER_CONFIG = {
    'port': 8888,
    'hostname': '$vm_hostname$',
    'compute_arch': 'x86'
    }

VOMS_CONFIG = {
    'enable_voms': 'True',
    'voms_policy': '/etc/snf/voms.json',
    'vomsdir_path': '/etc/grid-security/vomsdir/',
    'ca_path': '/etc/grid-security/certificates/',
    'cert_dir': '/etc/ssl/certs/',
    'key_dir': '/etc/ssl/private/'
}


from kamaki.cli import config
KAMAKI_CONFIG = config.Config()
SNF_CLOUD = KAMAKI_CONFIG.get('global', 'default_cloud')
SNF_AUTH_URL = KAMAKI_CONFIG.get_cloud(SNF_CLOUD, 'url')
SNF_AUTH_TOKEN = KAMAKI_CONFIG.get_cloud(SNF_CLOUD, 'token')

from kamaki.clients.astakos import CachedAstakosClient
SNF_AUTH = CachedAstakosClient(SNF_AUTH_URL, SNF_AUTH_TOKEN)
