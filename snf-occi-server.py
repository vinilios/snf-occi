#!/usr/bin/env python

from registry import snfRegistry
from kamaki.clients.compute import ComputeClient
from kamaki.clients.cyclades import CycladesClient
from kamaki.config  import Config

from occi.core_model import Mixin,Entity,Resource
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
                
        entity.attributes['occi.compute.state'] = 'active'
        entity.actions = [STOP, SUSPEND, RESTART]

        #Registry identifier is the uuid key occi.handler assigns
        #attribute 'occi.core.id' will be the snf-server id

        conf = Config()
        conf.set('token',extras['token'])
        snf = ComputeClient(conf)

        vm_name = entity.attributes['occi.compute.hostname']
        info = snf.create_server(vm_name, flavor_id, image_id)
        entity.attributes['occi.core.id'] = str(info['id'])
        entity.attributes['occi.compute.cores'] = flavor.attributes['occi.compute.cores']
        entity.attributes['occi.compute.memory'] = flavor.attributes['occi.compute.memory']

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
            #TODO VM suspending
            print "Suspending VM"


class MyAPP(Application):
    '''
    An OCCI WSGI application.
    '''

    def __call__(self, environ, response):

        #TODO up-to-date compute instances                

        # token will be represented in self.extras
        return self._call_occi(environ, response, security = None, token = environ['HTTP_AUTH_TOKEN'])

if __name__ == '__main__':

    APP = MyAPP(registry = snfRegistry())


    COMPUTE_BACKEND = ComputeBackend()

    APP.register_backend(COMPUTE, COMPUTE_BACKEND)
    APP.register_backend(START, COMPUTE_BACKEND)
    APP.register_backend(STOP, COMPUTE_BACKEND)
    APP.register_backend(RESTART, COMPUTE_BACKEND)
    APP.register_backend(SUSPEND, COMPUTE_BACKEND)
    APP.register_backend(RESOURCE_TEMPLATE, MixinBackend())
    APP.register_backend(OS_TEMPLATE, MixinBackend())
    
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

 
    VALIDATOR_APP = validator(APP)
    HTTPD = make_server('', 8888, VALIDATOR_APP)
    HTTPD.serve_forever()

