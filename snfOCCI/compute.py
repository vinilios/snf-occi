from snfOCCI.config import SERVER_CONFIG

from kamaki.clients.compute import ComputeClient
from kamaki.clients.cyclades import CycladesClient
from kamaki.config  import Config

from occi.backend import ActionBackend, KindBackend
from occi.extensions.infrastructure import COMPUTE, START, STOP, SUSPEND, RESTART


#Compute Backend for snf-occi-server

class MyBackend(KindBackend, ActionBackend):
    '''
    An very simple abstract backend which handles update and replace for
    attributes. Support for links and mixins would need to added.
    '''

    def update(self, old, new, extras):
        raise AttributeError("This action is currently no applicable.")

    def replace(self, old, new, extras):
        raise AttributeError("This action is currently no applicable.")


class ComputeBackend(MyBackend):
    '''
    Backend for Cyclades/Openstack compute instances
    '''

    def create(self, entity, extras):
    
        for mixin in entity.mixins:
            if mixin.related[0].term == 'os_tpl':
                image = mixin
                image_id = mixin.attributes['occi.core.id']
            if mixin.related[0].term == 'resource_tpl':
                flavor = mixin
                flavor_id = mixin.attributes['occi.core.id']
                
        entity.attributes['occi.compute.state'] = 'inactive'
        entity.actions = [START]

        #Registry identifier is the uuid key occi.handler assigns
        #attribute 'occi.core.id' will be the snf-server id

        conf = Config()
        conf.set('token',extras['token'])
        snf = ComputeClient(conf)

        vm_name = entity.attributes['occi.compute.hostname']
        info = snf.create_server(vm_name, flavor_id, image_id)
        entity.attributes['occi.core.id'] = str(info['id'])
        entity.attributes['occi.compute.architecture'] = SERVER_CONFIG['compute_arch']
        entity.attributes['occi.compute.cores'] = flavor.attributes['occi.compute.cores']
        entity.attributes['occi.compute.memory'] = flavor.attributes['occi.compute.memory']
        entity.attributes['occi.compute.hostname'] = SERVER_CONFIG['hostname'] % {'id':info['id']}

    def retrieve(self, entity, extras):
        
        # triggering cyclades to retrieve up to date information
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

        if entity.attributes['occi.compute.state'] == 'inactive':
            entity.actions = [START]
        if entity.attributes['occi.compute.state'] == 'active': 
            entity.actions = [STOP, SUSPEND, RESTART]
        if entity.attributes['occi.compute.state'] == 'suspended':
            entity.actions = [START]


    def delete(self, entity, extras):

        # delete vm with vm_id = entity.attributes['occi.core.id']
        conf = Config()
        conf.set('token',extras['token'])
        snf = ComputeClient(conf)

        vm_id = int(entity.attributes['occi.core.id'])
        snf.delete_server(vm_id)


    def action(self, entity, action, extras):

        conf = Config()
        conf.set('token',extras['token'])
        client = CycladesClient(conf)

        vm_id = int(entity.attributes['occi.core.id'])

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
