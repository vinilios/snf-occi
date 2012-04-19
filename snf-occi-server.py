#!/usr/bin/env python

from kamaki.clients.compute import ComputeClient
from kamaki.config  import Config

from occi.core_model import Mixin, Resource, Link, Entity
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
    A Backend for compute instances.
    '''

    def create(self, entity, extras):
        entity.attributes['occi.compute.state'] = 'active'
        entity.actions = [STOP, SUSPEND, RESTART]
        
        for mixin in entity.mixins:
            print mixin.term
            print mixin.attributes

        print('Creating the virtual machine with id: ' + entity.identifier)
        

    def retrieve(self, entity, extras):
        # triggering cyclades to retrieve up to date information

        if entity.attributes['occi.compute.state'] == 'inactive':
            entity.actions = [START]
        if entity.attributes['occi.compute.state'] == 'active': 
            entity.actions = [STOP, SUSPEND, RESTART]
        if entity.attributes['occi.compute.state'] == 'suspended':
            entity.actions = [START]

    def delete(self, entity, extras):
        # call the management framework to delete this compute instance...
        print('Removing representation of virtual machine with id: '
              + entity.identifier)

    def action(self, entity, action, extras):
        if action not in entity.actions:
            raise AttributeError("This action is currently no applicable.")
        elif action == START:
            entity.attributes['occi.compute.state'] = 'active'
            # read attributes from action and do something with it :-)
            print('Starting virtual machine with id' + entity.identifier)
        elif action == STOP:
            entity.attributes['occi.compute.state'] = 'inactive'
            # read attributes from action and do something with it :-)
            print('Stopping virtual machine with id' + entity.identifier)
        elif action == RESTART:
            entity.attributes['occi.compute.state'] = 'active'
            # read attributes from action and do something with it :-)
            print('Restarting virtual machine with id' + entity.identifier)
        elif action == SUSPEND:
            entity.attributes['occi.compute.state'] = 'suspended'
            # read attributes from action and do something with it :-)
            print('Suspending virtual machine with id' + entity.identifier)


class MyAPP(Application):
    '''
    An OCCI WSGI application.
    '''

    def __call__(self, environ, response):
        sec_obj = {'username': 'password'}

        snf = ComputeClient(Config())
        images = snf.list_images()
        for image in images:
            IMAGE = Mixin("http://schemas.ogf.org/occi/infrastructure#", str(image['name']), [OS_TEMPLATE])
            self.register_backend(IMAGE, MixinBackend())

        flavors = snf.list_flavors()
        for flavor in flavors:
            FLAVOR_ATTRIBUTES = {'occi.compute.cores': snf.get_flavor_details(flavor['id'])['cpu'],
                                 'occi.compute.memory': snf.get_flavor_details(flavor['id'])['ram'],
                                 'occi.storage.size': snf.get_flavor_details(flavor['id'])['disk'],
                                 }
            FLAVOR = Mixin("http://schemas.ogf.org/occi/infrastructure#", str(flavor['name']), [RESOURCE_TEMPLATE], attributes = FLAVOR_ATTRIBUTES)
            self.register_backend(FLAVOR, MixinBackend())
   
        
        
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
    
 
    VALIDATOR_APP = validator(APP)
    HTTPD = make_server('', 8888, VALIDATOR_APP)
    HTTPD.serve_forever()

