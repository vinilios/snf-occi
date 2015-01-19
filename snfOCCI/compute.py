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


from snfOCCI.config import CNF
# from snfOCCI.extensions import snf_addons

from occi.backend import ActionBackend, KindBackend, MixinBackend
# from occi.core_model import Mixin
from occi.extensions import infrastructure
from occi.exceptions import HTTPError
from base64 import b64encode, b64decode
import yaml

# Compute Backend for snf-occi-server


class MyBackend(KindBackend, ActionBackend):

    # Updating and Replacing compute instances not supported by Cyclades

    def update(self, old, new, extras):
        raise HTTPError(501, "Update is currently no applicable")

    def replace(self, old, new, extras):
        raise HTTPError(501, "Replace is currently no applicable")


class SNFBackend(MixinBackend, ActionBackend):
    """SNF Backend"""


class ComputeBackend(MyBackend):
    '''
    Backend for Cyclades/Openstack compute instances
    '''

    def create(self, entity, extras):

        # Creating new compute instance
        try:

            snf = extras['compute_client']

            for mixin in entity.mixins:
                if 'occi.core.id' in mixin.attributes:
                    if mixin.related[0].term == 'os_tpl':
                        image_id = mixin.attributes['occi.core.id']
                    elif mixin.related[0].term == 'resource_tpl':
                        flavor = mixin
                        flavor_id = mixin.attributes['occi.core.id']

            vm_name = entity.attributes['occi.core.title']

            user_data = None
            user_pub_key = None
            # meta_json = None
            personality = []

            if 'org.openstack.compute.user_data' in entity.attributes:
                user_data = b64decode(entity.attributes[
                    'org.openstack.compute.user_data'])

            if 'org.openstack.credentials.publickey.data' in entity.attributes:
                user_pub_key = entity.attributes[
                    'org.openstack.credentials.publickey.data']

            # Implementation for the meta.json file to use the respective
            # NoCloud cloudinit driver
            # if user_data and user_pub_key:
            #     meta_json = json.dumps(
            #       {
            #           'dsmode':'net',
            #           'public-keys':user_pub_key,
            #           'user-data': user_data},
            #       sort_keys=True,indent=4, separators=(',', ': ') )
            # elif user_data:
            #    meta_json = json.dumps(
            #       {'dsmode':'net','user-data': user_data},
            #       sort_keys=True,indent=4, separators=(',', ': ') )
            # elif user_pub_key:
            #    meta_json = json.dumps(
            #       {'dsmode':'net','public-keys':user_pub_key},
            #       sort_keys=True,indent=4, separators=(',', ': ') )

            # if meta_json:
            #   personality.append({
            #       'contents':b64encode(meta_json),
            #       'path':' /var/lib/cloud/seed/config_drive/meta.js'})
            #   info = snf.create_server(
            #       vm_name, flavor_id, image_id,personality=personality)
            # else:
            #   info = snf.create_server(vm_name, flavor_id, image_id)

            if user_data:
                userData = user_data
            if user_pub_key:
                pub_keyDict = dict([('public-keys', user_pub_key)])
                pub_key = yaml.dump(pub_keyDict)

            if user_data and user_pub_key:
                print "Info: Contextualization is performed with user data" + \
                      " and public key"
                personality.append({
                    'contents': b64encode(userData),
                    'path': '/var/lib/cloud/seed/nocloud-net/user-data'})
                personality.append({
                    'contents': b64encode(pub_key),
                    'path': '/var/lib/cloud/seed/nocloud-net/meta-data'})
                info = snf.create_server(
                    vm_name, flavor_id, image_id, personality=personality)
            elif user_data:
                print "Info: Contextualization is performed with user data"
                personality.append({
                    'contents': b64encode(userData),
                    'path': '/var/lib/cloud/seed/nocloud-net/user-data'})
                info = snf.create_server(
                    vm_name, flavor_id, image_id, personality=personality)
            elif user_pub_key:
                print "Info: Contextualization is performed with public key"
                personality.append({
                    'contents': b64encode(pub_key),
                    'path': '/var/lib/cloud/seed/nocloud-net/meta-data'})
                info = snf.create_server(
                    vm_name, flavor_id, image_id, personality=personality)
            else:
                info = snf.create_server(vm_name, flavor_id, image_id)

            entity.attributes['occi.compute.state'] = 'inactive'
            entity.attributes['occi.core.id'] = str(info['id'])
            entity.attributes['occi.compute.architecture'] = CNF.get(
                'server', 'arch')
            entity.attributes['occi.compute.cores'] = flavor.attributes[
                'occi.compute.cores']
            entity.attributes['occi.compute.memory'] = flavor.attributes[
                'occi.compute.memory']

            entity.actions = [
                infrastructure.STOP,
                infrastructure.SUSPEND,
                infrastructure.RESTART]

            info['adminPass'] = ""
            print info
            networkIDs = info['addresses'].keys()
            if len(networkIDs) > 0:
                entity.attributes['occi.compute.hostname'] = str(
                    info['addresses'][networkIDs[0]][0]['addr'])
            else:
                entity.attributes['occi.compute.hostname'] = ""

        except (UnboundLocalError, KeyError):
            raise HTTPError(406, 'Missing details about compute instance')

    def retrieve(self, entity, extras):
        """Triggering cyclades to retrieve up to date information"""

        snf = extras['compute_client']

        vm_id = int(entity.attributes['occi.core.id'])
        vm_info = snf.get_server_details(vm_id)
        vm_state = vm_info['status']

        status_dict = {
            'ACTIVE': 'active',
            'STOPPED': 'inactive',
            'REBOOT': 'inactive',
            'ERROR': 'inactive',
            'BUILD': 'inactive',
            'DELETED': 'inactive',
            'UNKNOWN': 'inactive'
        }

        entity.attributes['occi.compute.state'] = status_dict[vm_state]

        if vm_state == 'ERROR':
            raise HTTPError(500, 'ERROR building the compute instance')

        else:
            if entity.attributes['occi.compute.state'] == 'inactive':
                entity.actions = [infrastructure.START]
            if entity.attributes['occi.compute.state'] == 'active':
                entity.actions = [
                    infrastructure.STOP,
                    infrastructure.SUSPEND,
                    infrastructure.RESTART]

    def delete(self, entity, extras):
        """Deleting compute instance"""
        snf = extras['compute_client']
        vm_id = int(entity.attributes['occi.core.id'])
        print "Deleting VM" + str(vm_id)
        snf.delete_server(vm_id)

    def get_vm_actions(self, entity, vm_state):

        actions = []

        status_dict = {
            'ACTIVE': 'active',
            'STOPPED': 'inactive',
            'REBOOT': 'inactive',
            'ERROR': 'inactive',
            'BUILD': 'inactive',
            'DELETED': 'inactive',
            'UNKNOWN': 'inactive'
        }

        if vm_state in status_dict:
            entity.attributes['occi.compute.state'] = status_dict[vm_state]
            if vm_state == 'ACTIVE':
                actions.append(infrastructure.STOP)
                actions.append(infrastructure.RESTART)
            elif vm_state in ('STOPPED'):
                actions.append(infrastructure.START)
            return actions
        else:
            raise HTTPError(500, 'Undefined status of the VM')

    def action(self, entity, action, attributes, extras):
        """Triggering action to compute instances"""
        snf = extras['compute_client']

        vm_id = int(entity.attributes['occi.core.id'])
        vm_info = snf.get_server_details(vm_id)
        vm_state = vm_info['status']

        # Define the allowed actions depending on the state of the VM
        entity.actions = self.get_vm_actions(entity, vm_state)

        if vm_state == 'ERROR':
            raise HTTPError(500, 'ERROR building the compute instance')

        else:
            if action not in entity.actions:
                raise AttributeError(
                    "This action is currently no applicable in the current"
                    "status of the VM (CURRENT_STATE = %s )." % vm_state)

            elif action == infrastructure.START:
                print "Starting VM", vm_id
                snf.start_server(vm_id)

            elif action == infrastructure.STOP:
                print "Stopping VM", vm_id
                snf.shutdown_server(vm_id)

            elif action == infrastructure.RESTART:
                print "Restarting VM", vm_id
                snf.reboot_server(vm_id)

            elif action == infrastructure.SUSPEND:
                raise HTTPError(501, "This actions is currently no applicable")
