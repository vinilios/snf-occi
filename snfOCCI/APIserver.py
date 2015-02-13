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

import json
import uuid

from snfOCCI.registry import snfRegistry
from snfOCCI.compute import ComputeBackend, SNFBackend
from snfOCCI.config import CNF
import snf_voms
from snfOCCI.network import (
    NetworkBackend, IpNetworkBackend, IpNetworkInterfaceBackend,
    NetworkInterfaceBackend)
from snfOCCI.extensions import snf_addons

from kamaki.clients import ClientError
from kamaki.clients.cyclades import CycladesComputeClient
from kamaki.clients.cyclades import CycladesNetworkClient

from occi.core_model import Mixin, Resource
from occi.backend import MixinBackend
from occi.extensions.infrastructure import (
    COMPUTE, START, STOP, SUSPEND, RESTART, RESOURCE_TEMPLATE, OS_TEMPLATE,
    NETWORK, IPNETWORK, NETWORKINTERFACE, IPNETWORKINTERFACE)
from occi import wsgi
from occi.exceptions import HTTPError
from occi import core_model

from wsgiref.validate import validator
from webob import Request

from astavoms import SnfOcciUsers

SNF_CLOUD = CNF.get('kamaki', 'default_cloud')
SNF_ADMIN_URL = CNF.get_cloud(SNF_CLOUD, 'url')
SNF_ADMIN_TOKEN = CNF.get_cloud(SNF_CLOUD, 'token')
USERS = SnfOcciUsers(
    SNF_ADMIN_URL, SNF_ADMIN_TOKEN, CNF.get('ldap', 'url'),
    CNF.get('ldap', 'user'), CNF.get('ldap', 'password'),
    CNF.get('ldap', 'base_dn'), CNF.get('ldap', 'ca_certs') or None)


class MyAPP(wsgi.Application):
    '''
    An OCCI WSGI application.
    '''

    def __init__(self):
        """
        Initialization of the WSGI OCCI application for synnefo
        """
        self.enable_voms = CNF.get('voms', 'enable') == 'on'
        super(MyAPP, self).__init__(registry=snfRegistry())
        self._register_backends()
        VALIDATOR_APP = validator(self)

    def _register_backends(self):
        COMPUTE_BACKEND = ComputeBackend()
        NETWORK_BACKEND = NetworkBackend()
        NETWORKINTERFACE_BACKEND = NetworkInterfaceBackend()
        IPNETWORK_BACKEND = IpNetworkBackend()
        IPNETWORKINTERFACE_BACKEND = IpNetworkInterfaceBackend()

        self.register_backend(COMPUTE, COMPUTE_BACKEND)
        self.register_backend(START, COMPUTE_BACKEND)
        self.register_backend(STOP, COMPUTE_BACKEND)
        self.register_backend(RESTART, COMPUTE_BACKEND)
        self.register_backend(SUSPEND, COMPUTE_BACKEND)
        self.register_backend(RESOURCE_TEMPLATE, MixinBackend())
        self.register_backend(OS_TEMPLATE, MixinBackend())

        # Network related backends
        self.register_backend(NETWORK, NETWORK_BACKEND)
        self.register_backend(IPNETWORK, IPNETWORK_BACKEND)
        self.register_backend(NETWORKINTERFACE, NETWORKINTERFACE_BACKEND)
        self.register_backend(IPNETWORKINTERFACE, IPNETWORKINTERFACE_BACKEND)

        self.register_backend(snf_addons.SNF_USER_DATA_EXT, SNFBackend())
        self.register_backend(snf_addons.SNF_KEY_PAIR_EXT,  SNFBackend())

    def refresh_images(self, compute_client):
        try:
            images = compute_client.list_images()
            for image in images:
                IMAGE_ATTRIBUTES = {'occi.core.id': str(image['id'])}
                IMAGE = Mixin(
                    "http://schemas.ogf.org/occi/os_tpl#",
                    occify_terms(str(image['name'])),
                    [OS_TEMPLATE],
                    title='IMAGE',
                    attributes=IMAGE_ATTRIBUTES)
                self.register_backend(IMAGE, MixinBackend())
        except:
            raise HTTPError(404, "Unauthorized access")

    def refresh_flavors(self, compute_client):
        flavors = compute_client.list_flavors()
        for flavor in flavors:
            details = compute_client.get_flavor_details(flavor['id'])
            FLAVOR_ATTRIBUTES = {
                'occi.core.id': flavor['id'],
                'occi.compute.cores': str(details['vcpus']),
                'occi.compute.memory': str(details['ram']),
                'occi.storage.size': str(details['disk']),
            }
            FLAVOR = Mixin(
                "http://schemas.ogf.org/occi/resource_tpl#",
                str(flavor['name']),
                [RESOURCE_TEMPLATE],
                attributes=FLAVOR_ATTRIBUTES)
            self.register_backend(FLAVOR, MixinBackend())

    def refresh_flavors_norecursive(self, compute_client):
        flavors = compute_client.list_flavors(True)
        print "Retrieving details for flavors"
        for flavor in flavors:
            FLAVOR_ATTRIBUTES = {
                'occi.core.id': flavor['id'],
                'occi.compute.cores': str(flavor['vcpus']),
                'occi.compute.memory': str(flavor['ram']),
                'occi.storage.size': str(flavor['disk']),
            }

            FLAVOR = Mixin(
                "http://schemas.ogf.org/occi/resource_tpl#",
                occify_terms(str(flavor['name'])),
                [RESOURCE_TEMPLATE],
                title='FLAVOR',
                attributes=FLAVOR_ATTRIBUTES)
            self.register_backend(FLAVOR, MixinBackend())

    def refresh_network_instances(self, network_client):
        network_details = network_client.list_networks(detail='True')
        resources = self.registry.resources
        occi_keys = resources.keys()

        for network in network_details:
            if '/network/'+str(network['id']) not in occi_keys:
                netID = '/network/'+str(network['id'])
                snf_net = core_model.Resource(netID, NETWORK, [IPNETWORK])
                snf_net.attributes['occi.core.id'] = str(network['id'])

                # This info comes from the network details
                snf_net.attributes['occi.network.state'] = str(
                    network['status'])
                snf_net.attributes['occi.network.gateway'] = ''

                snf_net.attributes['occi.network.type'] = "Public = %s" % (
                    "True" if network['public'] else "False")

                self.registry.add_resource(netID, snf_net, None)

    def refresh_compute_instances(self, compute_client):
        '''Syncing registry with cyclades resources'''

        servers = compute_client.list_servers()
        snf_keys = []
        for server in servers:
            snf_keys.append(str(server['id']))

        resources = self.registry.resources
        occi_keys = resources.keys()

        print occi_keys
        for serverID in occi_keys:
            if '/compute/' in serverID and resources[serverID].attributes[
                    'occi.compute.hostname'] == "":
                self.registry.delete_resource(serverID, None)
        occi_keys = resources.keys()

        # Compute instances in synnefo not available in registry
        diff = [x for x in snf_keys if ('/compute/' + x) not in occi_keys]

        for key in diff:

            details = compute_client.get_server_details(int(key))
            flavor = compute_client.get_flavor_details(details['flavor']['id'])

            try:
                print "line 65:Finished getting image details for VM " + \
                      key + " with ID %s" % details['flavor']['id']
                image = compute_client.get_image_details(
                    details['image']['id'])

                for i in self.registry.backends:
                    if i.term == occify_terms(str(image['name'])):
                        rel_image = i
                    if i.term == occify_terms(str(flavor['name'])):
                        rel_flavor = i

                resource = Resource(key, COMPUTE, [rel_flavor, rel_image])
                resource.actions = [START]
                resource.attributes['occi.core.id'] = key
                resource.attributes['occi.compute.state'] = 'inactive'
                resource.attributes['occi.compute.architecture'] = CNF.get(
                    'server', 'arch')
                resource.attributes['occi.compute.cores'] = str(
                    flavor['vcpus'])
                resource.attributes['occi.compute.memory'] = str(
                    flavor['ram'])
                resource.attributes['occi.core.title'] = str(details['name'])
                networkIDs = details['addresses'].keys()
                if len(networkIDs) > 0:
                    resource.attributes['occi.compute.hostname'] = str(
                        details['addresses'][networkIDs[0]][0]['addr'])
                else:
                    resource.attributes['occi.compute.hostname'] = ""

                self.registry.add_resource(key, resource, None)

                for netKey in networkIDs:
                    link_id = str(uuid.uuid4())
                    infra_url = "http://schemas.ogf.org/occi/infrastructure"
                    NET_LINK = core_model.Link(
                        infra_url + "#networkinterface" + link_id,
                        NETWORKINTERFACE,
                        [IPNETWORKINTERFACE],
                        resource,
                        self.registry.resources['/network/'+str(netKey)])

                    for version in details['addresses'][netKey]:
                        ip4address = ''
                        ip6address = ''

                        if version['version'] == 4:
                            ip4address = str(version['addr'])
                            allocheme = str(version['OS-EXT-IPS:type'])
                        elif version['version'] == 6:
                            ip6address = str(version['addr'])
                            allocheme = str(version['OS-EXT-IPS:type'])

                    if 'attachments' in details.keys():
                        for item in details['attachments']:
                            NET_LINK.attributes = {
                                'occi.core.id': link_id,
                                'occi.networkinterface.allocation': allocheme,
                                'occi.networking.interface': str(item['id']),
                                'occi.networkinterface.mac': str(
                                    item['mac_address']),
                                'occi.networkinterface.address': ip4address,
                                'occi.networkinterface.ip6':  ip6address
                            }
                    elif len(details['addresses'][netKey]):
                        NET_LINK.attributes = {
                            'occi.core.id': link_id,
                            'occi.networkinterface.allocation': allocheme,
                            'occi.networking.interface': '',
                            'occi.networkinterface.mac': '',
                            'occi.networkinterface.address': ip4address,
                            'occi.networkinterface.ip6':  ip6address
                        }

                    else:
                        NET_LINK.attributes = {
                            'occi.core.id': link_id,
                            'occi.networkinterface.allocation': '',
                            'occi.networking.interface': '',
                            'occi.networkinterface.mac': '',
                            'occi.networkinterface.address': '',
                            'occi.networkinterface.ip6': ''
                        }

                    resource.links.append(NET_LINK)
                    self.registry.add_resource(link_id, NET_LINK, None)

            except ClientError as ce:
                if ce.status == 404:
                    print('Image not found (probably older version')
                    continue
                else:
                    raise ce

        # Compute instances in registry not available in synnefo
        diff = [x for x in occi_keys if x[9:] not in snf_keys]
        for key in diff:
            if '/network/' not in key:
                self.registry.delete_resource(key, None)

    def __call__(self, environ, response):
        """Enable VOMS Authorization"""
        print "snf-occi application has been called!"
        req = Request(environ)
        auth_uri = 'https://%s:5000/main' % CNF.get('server', 'hostname')
        auth_endpoint = 'snf-auth uri=\'%s\'' % auth_uri

        if 'HTTP_X_AUTH_TOKEN' not in req.environ:
                msg = 'An authentication token has not been provided!'
                print msg
                status = '401 Not Authorized'
                headers = [
                    ('Content-Type', 'text/html'),
                    ('Www-Authenticate', str(auth_endpoint))]
                response(status, headers)
                return [msg, ]

        environ['HTTP_AUTH_TOKEN'] = req.environ['HTTP_X_AUTH_TOKEN']
        token = environ['HTTP_X_AUTH_TOKEN']

        try:
            user_id = USERS.uuid_from_token(token)
        except KeyError:
            msg = "ERROR: Authentication token does not match any LDAP users"
            print msg
            status = '401 Not Authorized'
            headers = [
                ('Content-Type', 'text/html'),
                ('Www-Authenticate', auth_endpoint)]
            response(status, headers)
            return [msg, ]

        cycl_url = USERS.snf_admin.get_endpoint_url(
            CycladesComputeClient.service_type)
        cyclClient = USERS.add_renew_token(
            CycladesComputeClient(cycl_url, token), user_id)

        net_url = USERS.snf_admin.get_endpoint_url(
            CycladesNetworkClient.service_type)
        netClient = USERS.add_renew_token(
            CycladesNetworkClient(net_url, token), user_id)

        # Up-to-date flavors and images
        self.refresh_images(cyclClient)
        self.refresh_flavors_norecursive(cyclClient)
        self.refresh_network_instances(netClient)
        self.refresh_compute_instances(cyclClient)
        # token will be represented in self.extras
        return self._call_occi(
            environ, response,
            security=None, token=token, compute_client=cyclClient)


def application(env, start_response):
    """snf-occi will execute voms authentication"""
    print "snf-occi will execute voms authentication"
    t = snf_voms.VomsAuthN()
    (user_dn, user_vo, user_fqans) = t.process_request(env)
    print (user_dn, user_vo, user_fqans)

    try:
        user = USERS.get_user_info(user_dn, user_vo)
    except ClientError as ce:
            print ce
            status = '%s ClientError' % ce.status
            headers = [('Content-Type', 'text/html'), ('Www-Authenticate', str(
                'snf-auth uri=\'%s\'' % SNF_ADMIN_URL))]
            start_response(status, headers)
            return ['%s' % ce, ]

    env['HTTP_AUTH_TOKEN'], user_id = user['userPassword'][0], user['uid'][0]
    user_details = USERS.snf_users.get_user_details(user_id)

    response = {
        'access': {
            'token': {
                'issued_at': '',
                'expires': user_details['auth_token_expires'],
                'id': env['HTTP_AUTH_TOKEN']},
            'serviceCatalog': [],
            'user': {
                'username': user_dn,
                'roles_links': [],
                'id': user_id,
                'roles': [],
                'name': user_dn
            },
            'metadata': {
                'is_admin': 0,
                'roles': user_details['roles']
            }
        }
    }

    status = '200 OK'
    headers = [('Content-Type', 'application/json')]
    start_response(status, headers)

    body = json.dumps(response)
    print body
    return [body, ]


def app_factory(global_config, **local_config):
    """This function wraps our simple WSGI app so it
    can be used with paste.deploy"""
    return application


def tenant_application(env, start_response):
    """snf-occi will return tenant information"""
    print "snf-occi will return tenant information"
    if 'SSL_CLIENT_S_DN_ENV' in env:
        print env['SSL_CLIENT_S_DN_ENV'], env['SSL_CLIENT_CERT_ENV']

    req = Request(env)
    if 'HTTP_X_AUTH_TOKEN' in req.environ:
        env['HTTP_AUTH_TOKEN'] = req.environ['HTTP_X_AUTH_TOKEN']
    else:
        raise HTTPError(404, "Unauthorized access")
    # Get user authentication details
    print "@ get user id"
    user_id = USERS.uuid_from_token(env['HTTP_AUTH_TOKEN'])

    response = {
        'tenants_links': [],
        'tenants': [
            {
                'description': 'Instances of EGI Federated Clouds TF',
                'enabled': True,
                'id': user_id,
                'name': 'EGI_FCTF'
            }
        ]
    }

    status = '200 OK'
    headers = [('Content-Type', 'application/json')]
    start_response(status, headers)

    body = json.dumps(response)
    print body
    return [body, ]


def tenant_app_factory(global_config, **local_config):
    """This function wraps our simple WSGI app so it
    can be used with paste.deploy"""
    return tenant_application


def occify_terms(term_name):
    """
    Occifies a term_name so that it is compliant with GFD 185.
    """
    term = term_name.strip().replace(' ', '_').replace('.', '-').lower()
    return term.replace('(', '_').replace(')', '_').replace('@', '_').replace(
        '+', '-_')
