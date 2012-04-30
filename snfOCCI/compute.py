from snfOCCI.config import SERVER_CONFIG

from kamaki.clients.compute import ComputeClient
from kamaki.clients.cyclades import CycladesClient
from kamaki.config  import Config

from occi.backend import ActionBackend, KindBackend
from occi.extensions.infrastructure import COMPUTE, START, STOP, SUSPEND, RESTART
from occi.exceptions import HTTPError


#Compute Backend for snf-occi-server

class MyBackend(KindBackend, ActionBackend):
    '''
    An very simple abstract backend which handles update and replace for
    attributes. Support for links and mixins would need to added.
    '''

    # Updating and Replacing compute instances not supported by Cyclades

    def update(self, old, new, extras):
        raise AttributeError("This action is currently no applicable.")

    def replace(self, old, new, extras):
        raise AttributeError("This action is currently no applicable.")


class ComputeBackend(MyBackend):
    '''
    Backend for Cyclades/Openstack compute instances
    '''

    def create(self, entity, extras):

        #Creating new compute instance
    
        for mixin in entity.mixins:
            if mixin.related[0].term == 'os_tpl':
                image = mixin
                image_id = mixin.attributes['occi.core.id']
            if mixin.related[0].term == 'resource_tpl':
                flavor = mixin
                flavor_id = mixin.attributes['occi.core.id']
                
        entity.attributes['occi.compute.state'] = 'inactive'
        entity.actions = [START]

        conf = Config()
        conf.set('token',extras['token'])
        snf = ComputeClient(conf)

        vm_name = entity.attributes['occi.core.title']
        info = snf.create_server(vm_name, flavor_id, image_id)
        entity.attributes['occi.core.id'] = str(info['id'])
        entity.attributes['occi.compute.architecture'] = SERVER_CONFIG['compute_arch']
        entity.attributes['occi.compute.cores'] = flavor.attributes['occi.compute.cores']
        entity.attributes['occi.compute.memory'] = flavor.attributes['occi.compute.memory']
        entity.attributes['occi.compute.hostname'] = SERVER_CONFIG['hostname'] % {'id':info['id']}

    def retrieve(self, entity, extras):
        
        #Triggering cyclades to retrieve up to date information

        conf = Config()
        conf.set('token',extras['token'])
        snf = ComputeClient(conf)

        vm_id = int(entity.attributes['occi.core.id'])
        vm_info = snf.get_server_details(vm_id)
        vm_state = vm_info['status']
        
        status_dict = {'ACTIVE' : 'active',
                       'STOPPED' : 'inactive',
                       'ERROR' : 'inactive',
                       'BUILD' : 'inactive',
                       'DELETED' : 'inactive',
                       }
        
        entity.attributes['occi.compute.state'] = status_dict[vm_state]
                
        if vm_state == 'ERROR':
            raise HTTPError(500, 'ERROR building the compute instance')

        else:
            if entity.attributes['occi.compute.state'] == 'inactive':
                entity.actions = [START]
            if entity.attributes['occi.compute.state'] == 'active': 
                entity.actions = [STOP, SUSPEND, RESTART]
            if entity.attributes['occi.compute.state'] == 'suspended':
                entity.actions = [START]


    def delete(self, entity, extras):

        #Deleting compute instance

        conf = Config()
        conf.set('token',extras['token'])
        snf = ComputeClient(conf)

        vm_id = int(entity.attributes['occi.core.id'])
        snf.delete_server(vm_id)


    def action(self, entity, action, extras):

        #Triggering action to compute instances

        conf = Config()
        conf.set('token',extras['token'])
        client = CycladesClient(conf)
        snf = ComputeClient(conf)

        vm_id = int(entity.attributes['occi.core.id'])
        vm_info = snf.get_server_details(vm_id)
        vm_state = vm_info['status']


        if vm_state == 'ERROR':
            raise HTTPError(500, 'ERROR building the compute instance')

        else:
            if action not in entity.actions:
                raise AttributeError("This action is currently no applicable.")
            
            elif action == START:
                print "Starting VM"
                client.start_server(vm_id)
                
            elif action == STOP:
                print "Stopping VM"
                client.shutdown_server(vm_id)
    
            elif action == RESTART:
                print "Restarting VM"
                snf.reboot_server(vm_id)

            elif action == SUSPEND:
                raise AttributeError("This actions is currently no applicable")
