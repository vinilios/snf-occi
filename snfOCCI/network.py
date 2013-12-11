from snfOCCI.config import SERVER_CONFIG

from occi.backend import ActionBackend, KindBackend, MixinBackend
from occi.exceptions import HTTPError


#Network Backend for snf-occi-server

class NetworkBackend(KindBackend, ActionBackend):
    def create(self, entity, extras):
        raise HTTPError(501,"Currently not supported.")

    def action(self, entity, action, attributes, extras):
        raise HTTPError(501, "Currently not supported.")
    
class IpNetworkBackend(MixinBackend):
    def create(self, entity, extras):
        raise HTTPError(501,"Currently not supported.")

class IpNetworkInterfaceBackend(MixinBackend):
    
    pass

class NetworkInterfaceBackend(KindBackend):
    
    def create(self, entity, extras):
        raise HTTPError(501,"Currently not supported.")

    def action(self, entity, action, attributes, extras):
        raise HTTPError(501, "Currently not supported.")


    def update(self, old, new, extras):
        raise HTTPError(501, "Currently not supported.")

    def replace(self, old, new, extras):
        raise HTTPError(501, "Currently not supported.")

    
