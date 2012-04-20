#!/usr/bin/env python

from kamaki.clients.compute import ComputeClient
from kamaki.config  import Config

<<<<<<< HEAD
from occi.core_model import Mixin
=======
from occi.core_model import Mixin, Resource, Link, Entity
>>>>>>> 592e811729d5f061377c854f645311e560ec4faa
from occi.backend import ActionBackend, KindBackend, MixinBackend
from occi.extensions.infrastructure import COMPUTE, START, STOP, SUSPEND, RESTART, RESOURCE_TEMPLATE, OS_TEMPLATE

from occi.wsgi import Application

from wsgiref.simple_server import make_server
from wsgiref.validate import validator


class MyBackend(KindBackend, ActionBackend):
    '''
    An very simple abstract backend which handles update and replace for
    attributes. Support for links and mixins would need to added.
    '''

    def update(self, old, new, extras):
        # here you can check what information from new_entity you wanna bring
        # into old_entity

        # trigger your hypervisor and push most recent information
        print('Updating a resource with id: ' + old.identifier)
        for item in new.attributes.keys():
            old.attributes[item] = new.attributes[item]

    def replace(self, old, new, extras):
        print('Replacing a resource with id: ' + old.identifier)
        old.attributes = {}
        for item in new.attributes.keys():
            old.attributes[item] = new.attributes[item]
        old.attributes['occi.compute.state'] = 'inactive'


class ComputeBackend(MyBackend):
    '''
<<<<<<< HEAD
    A Backend for compute instances.
=======
    Backend for Cyclades/Openstack compute instances
>>>>>>> 592e811729d5f061377c854f645311e560ec4faa
    '''

    def create(self, entity, extras):
    
        for mixin in entity.mixins:
<<<<<<< HEAD
            print mixin.term
            print mixin.attributes
            if mixin.related[0].term == 'os_tpl':
                image = mixin.related[0]
                image_id = mixin.attributes['occi.core.id']
            if mixin.related[0].term == 'resource_tpl':
                flavor = mixin.related[0]
                flavor_id = mixin.attributes['occi.core.id']
                
        
        entity.attributes['occi.compute.state'] = 'active'
        entity.actions = [STOP, SUSPEND, RESTART]

        #TODO VM identifier
=======
            if mixin.related[0].term == 'os_tpl':
                image = mixin
                image_id = mixin.attributes['occi.core.id']
            if mixin.related[0].term == 'resource_tpl':
                flavor = mixin
                flavor_id = mixin.attributes['occi.core.id']
                
        entity.attributes['occi.compute.state'] = 'active'
        entity.actions = [STOP, SUSPEND, RESTART]

        #Registry identifier is the uuid key occi.handler assigns
        #attribute 'occi.core.id' will be the snf-server id
>>>>>>> 592e811729d5f061377c854f645311e560ec4faa

        snf = ComputeClient(Config())
        vm_name = entity.attributes['occi.compute.hostname']
        info = snf.create_server(vm_name, flavor_id, image_id)
        entity.attributes['occi.core.id'] = str(info['id'])
<<<<<<< HEAD

    def retrieve(self, entity, extras):
        # triggering cyclades to retrieve up to date information

=======
        entity.attributes['occi.compute.cores'] = flavor.attributes['occi.compute.cores']
        entity.attributes['occi.compute.memory'] = flavor.attributes['occi.compute.memory']

    def retrieve(self, entity, extras):
        
        # triggering cyclades to retrieve up to date information

        snf = ComputeClient(Config())

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

>>>>>>> 592e811729d5f061377c854f645311e560ec4faa
        if entity.attributes['occi.compute.state'] == 'inactive':
            entity.actions = [START]
        if entity.attributes['occi.compute.state'] == 'active': 
            entity.actions = [STOP, SUSPEND, RESTART]
        if entity.attributes['occi.compute.state'] == 'suspended':
            entity.actions = [START]

<<<<<<< HEAD
    def delete(self, entity, extras):
        # call the management framework to delete this compute instance...
        print('Removing representation of virtual machine with id: '
              + entity.identifier)
=======
        


    def delete(self, entity, extras):
        # delete vm with vm_id = entity.attributes['occi.core.id']
        snf = ComputeClient(Config())
        vm_id = int(entity.attributes['occi.core.id'])
        snf.delete_server(vm_id)

>>>>>>> 592e811729d5f061377c854f645311e560ec4faa

    def action(self, entity, action, extras):
        if action not in entity.actions:
            raise AttributeError("This action is currently no applicable.")
        elif action == START:
            entity.attributes['occi.compute.state'] = 'active'
            entity.actions = [STOP, SUSPEND, RESTART]
            # read attributes from action and do something with it :-)
            print('Starting virtual machine with id' + entity.identifier)
        elif action == STOP:
            entity.attributes['occi.compute.state'] = 'inactive'
            entity.actions = [START]
            # read attributes from action and do something with it :-)
            print('Stopping virtual machine with id' + entity.identifier)
        elif action == RESTART:
            entity.actions = [STOP, SUSPEND, RESTART]
            entity.attributes['occi.compute.state'] = 'active'
            # read attributes from action and do something with it :-)
            print('Restarting virtual machine with id' + entity.identifier)
        elif action == SUSPEND:
            entity.attributes['occi.compute.state'] = 'suspended'
            entity.actions = [START]
            # read attributes from action and do something with it :-)
            print('Suspending virtual machine with id' + entity.identifier)


class MyAPP(Application):
    '''
    An OCCI WSGI application.
    '''

    def __call__(self, environ, response):
        sec_obj = {'username': 'password'}

<<<<<<< HEAD

        #Refresh registry entries with current Cyclades state
        snf = ComputeClient(Config())

=======
        
        #Refresh registry entries with current Cyclades state
        snf = ComputeClient(Config())

        '''
>>>>>>> 592e811729d5f061377c854f645311e560ec4faa
        images = snf.list_images()
        for image in images:
            IMAGE_ATTRIBUTES = {'occi.core.id': str(image['id'])}
            IMAGE = Mixin("http://schemas.ogf.org/occi/infrastructure#", str(image['name']), [OS_TEMPLATE], attributes = IMAGE_ATTRIBUTES)
            self.register_backend(IMAGE, MixinBackend())

        flavors = snf.list_flavors()
        for flavor in flavors:
            FLAVOR_ATTRIBUTES = {'occi.core.id': flavor['id'],
                                 'occi.compute.cores': snf.get_flavor_details(flavor['id'])['cpu'],
                                 'occi.compute.memory': snf.get_flavor_details(flavor['id'])['ram'],
                                 'occi.storage.size': snf.get_flavor_details(flavor['id'])['disk'],
                                 }
            FLAVOR = Mixin("http://schemas.ogf.org/occi/infrastructure#", str(flavor['name']), [RESOURCE_TEMPLATE], attributes = FLAVOR_ATTRIBUTES)
            self.register_backend(FLAVOR, MixinBackend())
<<<<<<< HEAD
        
        #TODO show only current VM instances
                
=======
            '''       

        #TODO show only current VM instances
>>>>>>> 592e811729d5f061377c854f645311e560ec4faa
        
        return self._call_occi(environ, response, security=sec_obj, foo=None)

if __name__ == '__main__':

    APP = MyAPP()

    COMPUTE_BACKEND = ComputeBackend()

    APP.register_backend(COMPUTE, COMPUTE_BACKEND)
    APP.register_backend(START, COMPUTE_BACKEND)
    APP.register_backend(STOP, COMPUTE_BACKEND)
    APP.register_backend(RESTART, COMPUTE_BACKEND)
    APP.register_backend(SUSPEND, COMPUTE_BACKEND)
    APP.register_backend(RESOURCE_TEMPLATE, MixinBackend())
    APP.register_backend(OS_TEMPLATE, MixinBackend())
    
<<<<<<< HEAD
=======
    snf = ComputeClient(Config())
    
    images = snf.list_images()
    for image in images:
        IMAGE_ATTRIBUTES = {'occi.core.id': str(image['id'])}
        IMAGE = Mixin("http://schemas.ogf.org/occi/infrastructure#", str(image['name']), [OS_TEMPLATE], attributes = IMAGE_ATTRIBUTES)
        APP.register_backend(IMAGE, MixinBackend())

    flavors = snf.list_flavors()
    for flavor in flavors:
        FLAVOR_ATTRIBUTES = {'occi.core.id': flavor['id'],
                             'occi.compute.cores': snf.get_flavor_details(flavor['id'])['cpu'],
                             'occi.compute.memory': snf.get_flavor_details(flavor['id'])['ram'],
                             'occi.storage.size': snf.get_flavor_details(flavor['id'])['disk'],
                             }
        FLAVOR = Mixin("http://schemas.ogf.org/occi/infrastructure#", str(flavor['name']), [RESOURCE_TEMPLATE], attributes = FLAVOR_ATTRIBUTES)
        APP.register_backend(FLAVOR, MixinBackend())

>>>>>>> 592e811729d5f061377c854f645311e560ec4faa
 
    VALIDATOR_APP = validator(APP)
    HTTPD = make_server('', 8888, VALIDATOR_APP)
    HTTPD.serve_forever()

