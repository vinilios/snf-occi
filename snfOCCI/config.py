SERVER_CONFIG = {
    'port': 8888,
    'hostname': '$vm_hostname$',
    'compute_arch': 'x86'
    }

KAMAKI_CONFIG = {
    'compute_url': 'https://cyclades.okeanos.grnet.gr/compute/v2.0/',
    'astakos_url': 'https://accounts.okeanos.grnet.gr/identity/v2.0/'
}
        
VOMS_CONFIG = {
    'enable_voms' : 'True',           
    'voms_policy' : '/etc/snf/voms.json',
    'vomsdir_path' : '/etc/grid-security/vomsdir/',
    'ca_path': '/etc/grid-security/certificates/',
    'cert_dir' : '/etc/ssl/certs/',
    'key_dir' : '/etc/ssl/private/'               
}