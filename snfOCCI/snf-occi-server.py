#!/usr/bin/env python

from snfOCCI.registry import snfRegistry
from snfOCCI.compute import ComputeBackend
from snfOCCI.config import SERVER_CONFIG

from kamaki.clients.compute import ComputeClient
from kamaki.clients.cyclades import CycladesClient
from kamaki.config  import Config

from occi.core_model import Mixin
from occi.backend import MixinBackend
from occi.extensions.infrastructure import COMPUTE, START, STOP, SUSPEND, RESTART, RESOURCE_TEMPLATE, OS_TEMPLATE
from occi.wsgi import Application

from wsgiref.simple_server import make_server
from wsgiref.validate import validator




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
    HTTPD = make_server('', SERVER_CONFIG['port'], VALIDATOR_APP)
    HTTPD.serve_forever()

