#!/usr/bin/env python

from snfOCCI.registry import snfRegistry
from snfOCCI.compute import ComputeBackend
from snfOCCI.config import SERVER_CONFIG

from kamaki.clients.compute import ComputeClient
from kamaki.clients.cyclades import CycladesClient
from kamaki.config  import Config

from occi.core_model import Mixin, Resource
from occi.backend import MixinBackend
from occi.extensions.infrastructure import COMPUTE, START, STOP, SUSPEND, RESTART, RESOURCE_TEMPLATE, OS_TEMPLATE
from occi.wsgi import Application

from wsgiref.simple_server import make_server
from wsgiref.validate import validator




class MyAPP(Application):
    '''
    An OCCI WSGI application.
    '''

    def refresh_images(self, snf, client):

        images = snf.list_images()
        for image in images:
            IMAGE_ATTRIBUTES = {'occi.core.id': str(image['id'])}
            IMAGE = Mixin("http://schemas.ogf.org/occi/infrastructure#", str(image['name']), [OS_TEMPLATE], attributes = IMAGE_ATTRIBUTES)
            self.register_backend(IMAGE, MixinBackend())

    def refresh_flavors(self, snf, client):
        
        flavors = snf.list_flavors()
        for flavor in flavors:
            details = snf.get_flavor_details(flavor['id'])
            FLAVOR_ATTRIBUTES = {'occi.core.id': flavor['id'],
                                 'occi.compute.cores': details['cpu'],
                                 'occi.compute.memory': details['ram'],
                                 'occi.storage.size': details['disk'],
                                 }
            FLAVOR = Mixin("http://schemas.ogf.org/occi/infrastructure#", str(flavor['name']), [RESOURCE_TEMPLATE], attributes = FLAVOR_ATTRIBUTES)
            self.register_backend(FLAVOR, MixinBackend())


    def refresh_compute_instances(self, snf):
        
        servers = snf.list_servers()
        snf_keys = []
        for server in servers:
            snf_keys.append(str(server['id']))

        resources = self.registry.resources
        occi_keys = resources.keys()
        
        diff = [x for x in snf_keys if '/compute/'+x not in occi_keys]

        for key in diff:

            details = snf.get_server_details(int(key))
            flavor = snf.get_flavor_details(details['flavorRef'])

            resource = Resource(key, COMPUTE, [])

            resource.actions = [START]
            resource.attribute = {}
            resource.attributes['occi.core.id'] = key
            resource.attributes['occi.compute.state'] = 'inactive'
            resource.attributes['occi.compute.architecture'] = SERVER_CONFIG['compute_arch']
            resource.attributes['occi.compute.cores'] = flavor['cpu']
            resource.attributes['occi.compute.memory'] = flavor['ram']
            resource.attributes['occi.compute.hostname'] = SERVER_CONFIG['hostname'] % {'id':int(key)}
  
            self.registry.add_resource(key, resource, None)

    def __call__(self, environ, response):

        conf = Config()
        conf.set('compute_token',environ['HTTP_AUTH_TOKEN'])
        compClient = ComputeClient(conf)
        cyclClient = CycladesClient(conf)

        #Up-to-date flavors and images
        self.refresh_compute_instances(compClient)
        self.refresh_images(compClient, cyclClient)
        self.refresh_flavors(compClient, cyclClient)

        # token will be represented in self.extras
        return self._call_occi(environ, response, security = None, token = environ['HTTP_AUTH_TOKEN'], snf = compClient, client = cyclClient)


def main():

    APP = MyAPP(registry = snfRegistry())
    COMPUTE_BACKEND = ComputeBackend()

    APP.register_backend(COMPUTE, COMPUTE_BACKEND)
    APP.register_backend(START, COMPUTE_BACKEND)
    APP.register_backend(STOP, COMPUTE_BACKEND)
    APP.register_backend(RESTART, COMPUTE_BACKEND)
    APP.register_backend(SUSPEND, COMPUTE_BACKEND)
    APP.register_backend(RESOURCE_TEMPLATE, MixinBackend())
    APP.register_backend(OS_TEMPLATE, MixinBackend())
 
    VALIDATOR_APP = validator(APP)
    HTTPD = make_server('', SERVER_CONFIG['port'], VALIDATOR_APP)
    HTTPD.serve_forever()
    
