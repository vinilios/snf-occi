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


from snfOCCI.config import SERVER_CONFIG

from occi.backend import ActionBackend, KindBackend
from occi.extensions import infrastructure
from occi.exceptions import HTTPError


#Compute Backend for snf-occi-server

class MyBackend(KindBackend, ActionBackend):

    # Updating and Replacing compute instances not supported by Cyclades

    def update(self, old, new, extras):
        raise HTTPError(501, "Update is currently no applicable")

    def replace(self, old, new, extras):
        raise HTTPError(501, "Replace is currently no applicable")


class ComputeBackend(MyBackend):
    '''
    Backend for Cyclades/Openstack compute instances
    '''

    def create(self, entity, extras):

        #Creating new compute instance
        
        try:

            snf = extras['snf']

            for mixin in entity.mixins:
                if mixin.related[0].term == 'os_tpl':
                    image_id = mixin.attributes['occi.core.id']
                if mixin.related[0].term == 'resource_tpl':
                    flavor = mixin
                    flavor_id = mixin.attributes['occi.core.id']

            vm_name = entity.attributes['occi.core.title']
            info = snf.create_server(vm_name, flavor_id, image_id)
           
            entity.attributes['occi.compute.state'] = 'inactive'
            entity.attributes['occi.core.id'] = str(info['id'])
            entity.attributes['occi.compute.architecture'] = SERVER_CONFIG['compute_arch']
            entity.attributes['occi.compute.cores'] = flavor.attributes['occi.compute.cores']
            entity.attributes['occi.compute.memory'] = flavor.attributes['occi.compute.memory']
           
            entity.actions = [infrastructure.STOP,
                               infrastructure.SUSPEND,
                               infrastructure.RESTART]

            # entity.attributes['occi.compute.hostname'] = SERVER_CONFIG['hostname'] % {'id':info['id']}
            info['adminPass']= ""
            print info
            networkIDs = info['addresses'].keys()
                #resource.attributes['occi.compute.hostname'] = SERVER_CONFIG['hostname'] % {'id':int(key)}
            if len(networkIDs)>0:    
                entity.attributes['occi.compute.hostname'] =  str(info['addresses'][networkIDs[0]][0]['addr'])
            else:
                entity.attributes['occi.compute.hostname'] = ""
               
        except (UnboundLocalError, KeyError) as e:
            raise HTTPError(406, 'Missing details about compute instance')
            

    def retrieve(self, entity, extras):
        
        #Triggering cyclades to retrieve up to date information

        snf = extras['snf']

        vm_id = int(entity.attributes['occi.core.id'])
        vm_info = snf.get_server_details(vm_id)
        vm_state = vm_info['status']
        
        status_dict = {'ACTIVE' : 'active',
                       'STOPPED' : 'inactive',
                       'REBOOT' : 'inactive',
                       'ERROR' : 'inactive',
                       'BUILD' : 'inactive',
                       'DELETED' : 'inactive',
                       'UNKNOWN' : 'inactive'
                       }
        
        entity.attributes['occi.compute.state'] = status_dict[vm_state]
                
        if vm_state == 'ERROR':
            raise HTTPError(500, 'ERROR building the compute instance')

        else:
            if entity.attributes['occi.compute.state'] == 'inactive':
                entity.actions = [infrastructure.START]
            if entity.attributes['occi.compute.state'] == 'active': 
                entity.actions = [infrastructure.STOP, infrastructure.SUSPEND, infrastructure.RESTART]


    def delete(self, entity, extras):

        #Deleting compute instance
        print "Deleting VM" + str(vm_id)
        snf = extras['snf']
        vm_id = int(entity.attributes['occi.core.id'])
        snf.delete_server(vm_id)


    def get_vm_actions(self, entity ,vm_state):
        
        actions = []
        
        status_dict = {'ACTIVE' : 'active',
                       'STOPPED' : 'inactive',
                       'REBOOT' : 'inactive',
                       'ERROR' : 'inactive',
                       'BUILD' : 'inactive',
                       'DELETED' : 'inactive',
                       'UNKNOWN' : 'inactive'
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

        #Triggering action to compute instances

        client = extras['client']
        snf = extras['snf']

        vm_id = int(entity.attributes['occi.core.id'])
        vm_info = snf.get_server_details(vm_id)
        vm_state = vm_info['status']
        
        # Define the allowed actions depending on the state of the VM
        entity.actions = self.get_vm_actions(entity,vm_state)
        

        if vm_state == 'ERROR':
            raise HTTPError(500, 'ERROR building the compute instance')

        else:
            if action not in entity.actions:
                raise AttributeError("This action is currently no applicable in the current status of the VM (CURRENT_STATE = " + str(vm_state)+ ").")
            
            elif action == infrastructure.START:
                print "Starting VM" + str(vm_id)
                client.start_server(vm_id)
                
            elif action == infrastructure.STOP:
                print "Stopping VM"  + str(vm_id)
                client.shutdown_server(vm_id)
    
            elif action == infrastructure.RESTART:
                print "Restarting VM" + str(vm_id)
                snf.reboot_server(vm_id)

            elif action == infrastructure.SUSPEND:
                raise HTTPError(501, "This actions is currently no applicable")
            
            

