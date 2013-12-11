#!/usr/bin/env python

from snfOCCI.registry import snfRegistry
from snfOCCI.compute import ComputeBackend
from snfOCCI.network import NetworkBackend, IpNetworkBackend, IpNetworkInterfaceBackend, NetworkInterfaceBackend

from snfOCCI.config import SERVER_CONFIG, KAMAKI_CONFIG

from kamaki.clients.compute import ComputeClient
from kamaki.clients.cyclades import CycladesClient
from kamaki.clients import ClientError

from occi.core_model import Mixin, Resource
from occi.backend import MixinBackend, KindBackend
from occi.extensions.infrastructure import COMPUTE, START, STOP, SUSPEND, RESTART, RESOURCE_TEMPLATE, OS_TEMPLATE, NETWORK, IPNETWORK, NETWORKINTERFACE,IPNETWORKINTERFACE 
from occi.wsgi import Application
from occi.exceptions import HTTPError
from occi import core_model

from wsgiref.simple_server import make_server
from wsgiref.validate import validator
import uuid

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
        print "Retrieving details for each image id"
        for flavor in flavors:
            details = snf.get_flavor_details(flavor['id'])
            FLAVOR_ATTRIBUTES = {'occi.core.id': flavor['id'],
                                 'occi.compute.cores': str(details['vcpus']),
                                 'occi.compute.memory': str(details['ram']),
                                 'occi.storage.size': str(details['disk']),
                                 }
            FLAVOR = Mixin("http://schemas.ogf.org/occi/infrastructure#", str(flavor['name']), [RESOURCE_TEMPLATE], attributes = FLAVOR_ATTRIBUTES)
            self.register_backend(FLAVOR, MixinBackend())
            
    def refresh_flavors_norecursive(self, snf, client):
        flavors = snf.list_flavors(True)
        print "Retrieving details for each image id"
        for flavor in flavors:
            # details = snf.get_flavor_details(flavor['id'])
            FLAVOR_ATTRIBUTES = {'occi.core.id': flavor['id'],
                                 'occi.compute.cores': str(flavor['vcpus']),
                                 'occi.compute.memory': str(flavor['ram']),
                                 'occi.storage.size': str(flavor['disk']),
                                 }
             
            FLAVOR = Mixin("http://schemas.ogf.org/occi/infrastructure#", str(flavor['name']), [RESOURCE_TEMPLATE], attributes = FLAVOR_ATTRIBUTES)
            self.register_backend(FLAVOR, MixinBackend())
            
       
    def refresh_network_instances(self,client):
        networks =client.networks_get(command = 'detail')
        network_details = networks.json['networks']
        resources = self.registry.resources
        occi_keys = resources.keys()
         
        for network in network_details:
            if '/network/'+str(network['id']) not in occi_keys:
                netID = '/network/'+str(network['id'])   
                snf_net = core_model.Resource(netID,
                                           NETWORK,
                                           [IPNETWORK])
                
                snf_net.attributes['occi.core.id'] = str(network['id']) 
               
                #This info comes from the network details
                snf_net.attributes['occi.network.state'] = str(network['status'])
                snf_net.attributes['occi.network.gateway'] = str(network['gateway'])
               
                if network['public'] == True:
                    snf_net.attributes['occi.network.type'] = "Public = True"
                else:
                    snf_net.attributes['occi.network.type'] = "Public = False"
                    
                self.registry.add_resource(netID, snf_net, None)       
            
        
            
    def refresh_compute_instances(self, snf, client):
        '''Syncing registry with cyclades resources'''
        
        servers = snf.list_servers()
        snf_keys = []
        for server in servers:
            snf_keys.append(str(server['id']))

        resources = self.registry.resources
        occi_keys = resources.keys()
        
        print resources.keys()
        
        for serverID in occi_keys:
            if '/compute/' in serverID and resources[serverID].attributes['occi.compute.hostname'] == "":
                self.registry.delete_resource(serverID, None)
        
        occi_keys = resources.keys()
        
            
        #Compute instances in synnefo not available in registry
        diff = [x for x in snf_keys if '/compute/'+x not in occi_keys]
        for key in diff:

            details = snf.get_server_details(int(key))
            flavor = snf.get_flavor_details(details['flavor']['id'])
            
            try:
                print "line 65:Finished getting image details for VM with ID" + str(details['flavor']['id'])
                image = snf.get_image_details(details['image']['id'])
                
                for i in self.registry.backends:
                    if i.term == str(image['name']):
                        rel_image = i
                    if i.term == str(flavor['name']):
                        rel_flavor = i
                        
                resource = Resource(key, COMPUTE, [rel_flavor, rel_image])
                resource.actions = [START]
                resource.attributes['occi.core.id'] = key
                resource.attributes['occi.compute.state'] = 'inactive'
                resource.attributes['occi.compute.architecture'] = SERVER_CONFIG['compute_arch']
                resource.attributes['occi.compute.cores'] = str(flavor['vcpus'])
                resource.attributes['occi.compute.memory'] = str(flavor['ram'])
                resource.attributes['occi.core.title'] = str(details['name'])
                networkIDs = details['addresses'].keys()
                if len(networkIDs)>0: 
                    #resource.attributes['occi.compute.hostname'] = SERVER_CONFIG['hostname'] % {'id':int(key)}
                    resource.attributes['occi.compute.hostname'] =  str(details['addresses'][networkIDs[0]][0]['addr'])
                    #resource.attributes['occi.networkinterface.address'] = str(details['addresses'][networkIDs[0]][0]['addr'])
                else:
                    resource.attributes['occi.compute.hostname'] = ""
                    
                self.registry.add_resource(key, resource, None)  
                
                for netKey in networkIDs:
                    link_id = str(uuid.uuid4())
                    NET_LINK = core_model.Link("http://schemas.ogf.org/occi/infrastructure#networkinterface" + link_id,
                                               NETWORKINTERFACE,
                                               [IPNETWORKINTERFACE], resource,
                                               self.registry.resources['/network/'+str(netKey)])
                    
                    for version in details['addresses'][netKey]:
                        if version['version']==4:
                            ip4address = str(version['addr'])
                            allocheme = str(version['OS-EXT-IPS:type'])
                        elif version['version']==6:
                            ip6address = str(version['addr'])
                   
                    if 'attachments' in details.keys():
                        for item in details['attachments']:
                            NET_LINK.attributes ={'occi.core.id':link_id,
                                          'occi.networkinterface.allocation' : allocheme,
                                          'occi.networking.interface': str(item['id']),
                                          'occi.networkinterface.mac' : str(item['mac_address']),
                                          'occi.networkinterface.ip4' : ip4address,
                                          'occi.networkinterface.ip6' :  ip6address                      
                                      }
                    elif  len(details['addresses'][netKey])>0:
                        NET_LINK.attributes ={'occi.core.id':link_id,
                                          'occi.networkinterface.allocation' : allocheme,
                                          'occi.networking.interface': '',
                                          'occi.networkinterface.mac' : '',
                                          'occi.networkinterface.ip4' : ip4address,
                                          'occi.networkinterface.ip6' :  ip6address                      
                                      }
    
                    else:
                        NET_LINK.attributes ={'occi.core.id':link_id,
                                          'occi.networkinterface.allocation' : '',
                                          'occi.networking.interface': '',
                                          'occi.networkinterface.mac' : '',
                                          'occi.networkinterface.ip4' :'',
                                          'occi.networkinterface.ip6' : '' }
                                      
                    resource.links.append(NET_LINK)
                    self.registry.add_resource(link_id, NET_LINK, None)
                     
                
            except ClientError as ce:
                if ce.status == 404:
                    print('Image not found, sorry!!!')
                    continue
                else:
                    raise ce
                  
        #Compute instances in registry not available in synnefo
        diff = [x for x in occi_keys if x[9:] not in snf_keys]
        for key in diff:
            if '/network/' not in key:
                self.registry.delete_resource(key, None)

    
    def __call__(self, environ, response):
        
            compClient = ComputeClient(KAMAKI_CONFIG['compute_url'], environ['HTTP_AUTH_TOKEN'])
            cyclClient = CycladesClient(KAMAKI_CONFIG['compute_url'], environ['HTTP_AUTH_TOKEN'])

            #Up-to-date flavors and images
            print "@refresh_images"
            self.refresh_images(compClient,cyclClient)
            print "@refresh_flavors"
            self.refresh_flavors_norecursive(compClient,cyclClient)
            self.refresh_network_instances(cyclClient)
            print "@refresh_compute_instances"
            self.refresh_compute_instances(compClient,cyclClient)
           
            # token will be represented in self.extras
            return self._call_occi(environ, response, security = None, token = environ['HTTP_AUTH_TOKEN'], snf = compClient, client = cyclClient)


def main():

    APP = MyAPP(registry = snfRegistry())
    COMPUTE_BACKEND = ComputeBackend()
    NETWORK_BACKEND = NetworkBackend() 
    NETWORKINTERFACE_BACKEND = NetworkInterfaceBackend()
    IPNETWORK_BACKEND = IpNetworkBackend()
    IPNETWORKINTERFACE_BACKEND = IpNetworkInterfaceBackend()
      
    APP.register_backend(COMPUTE, COMPUTE_BACKEND)
    APP.register_backend(START, COMPUTE_BACKEND)
    APP.register_backend(STOP, COMPUTE_BACKEND)
    APP.register_backend(RESTART, COMPUTE_BACKEND)
    APP.register_backend(SUSPEND, COMPUTE_BACKEND)
    APP.register_backend(RESOURCE_TEMPLATE, MixinBackend())
    APP.register_backend(OS_TEMPLATE, MixinBackend())
 
    # Network related backends
    APP.register_backend(NETWORK, NETWORK_BACKEND)
    APP.register_backend(IPNETWORK, IPNETWORK_BACKEND)
    APP.register_backend(NETWORKINTERFACE,NETWORKINTERFACE_BACKEND)
    APP.register_backend(IPNETWORKINTERFACE, IPNETWORKINTERFACE_BACKEND)
     
    VALIDATOR_APP = validator(APP)
  
    HTTPD = make_server('', SERVER_CONFIG['port'], VALIDATOR_APP)
    HTTPD.serve_forever()
    
