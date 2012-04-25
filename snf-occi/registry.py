from occi import registry

class snfRegistry(registry.NonePersistentRegistry):

    def add_resource(self, key, resource, extras):

        key = resource.kind.location + resource.attributes['occi.core.id']
        resource.identifier = key

        super(snfRegistry, self).add_resource(key, resource, extras)

    
