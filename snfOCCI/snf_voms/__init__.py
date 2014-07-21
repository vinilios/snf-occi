# Copyright 2012 Spanish National Research Council
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.

import json
import M2Crypto
import ast

from logging import getLogger
import voms_helper
from kamaki.clients import ClientError

LOG =  getLogger(__name__)

# Environment variable used to pass the request context
CONTEXT_ENV = 'snf.context'


SSL_CLIENT_S_DN_ENV = "SSL_CLIENT_S_DN"
SSL_CLIENT_CERT_ENV = "SSL_CLIENT_CERT"
SSL_CLIENT_CERT_CHAIN_ENV_PREFIX = "SSL_CLIENT_CERT_CHAIN_"

"""Global variables that contain VOMS related paths
"""
VOMS_POLICY = "/etc/snf/voms.json"
VOMSDIR_PATH = "/etc/grid-security/vomsdir/"
CA_PATH = "/etc/grid-security/certificates/"
VOMSAPI_LIB = "/usr/lib/libvomsapi.so.1"
PARAMS_ENV = 'snf_voms.params'

class VomsError():
    """Voms credential management error"""

    errors = {
        0: ('none', None),
        1: ('nosocket', 'Socket problem'),
        2: ('noident', 'Cannot identify itself (certificate problem)'),
        3: ('comm', 'Server problem'),
        4: ('param', 'Wrong parameters'),
        5: ('noext', 'VOMS extension missing'),
        6: ('noinit', 'Initialization error'),
        7: ('time', 'Error in time checking'),
        8: ('idcheck', 'User data in extension different from the real'),
        9: ('extrainfo', 'VO name and URI missing'),
        10: ('format', 'Wrong data format'),
        11: ('nodata', 'Empty extension'),
        12: ('parse', 'Parse error'),
        13: ('dir', 'Directory error'),
        14: ('sign', 'Signature error'),
        15: ('server', 'Unidentifiable VOMS server'),
        16: ('mem', 'Memory problems'),
        17: ('verify', 'Generic verification error'),
        18: ('type', 'Returned data of unknown type'),
        19: ('order', 'Ordering different than required'),
        20: ('servercode', 'Error from the server'),
        21: ('notavail', 'Method not available'),
    }

    http_codes = {
        5: (400, "Bad Request"),
        11: (400, "Bad Request"),
        14: (401, "Not Authorized"),
    }

    def __init__(self, code):
        short, message = self.errors.get(code, ('oops',
                                                'Unknown error %d' % code))
        message = "(%s, %s)" % (code, message)
        super(VomsError, self).__init__(message=message)

        code, title = self.http_codes.get(code, (500, "Unexpected Error"))
        self.code = code
        self.title = title


class VomsAuthN():
    """Filter that checks for the SSL data in the reqest.

    Sets 'ssl' in the context as a dictionary containing this data.
    """
    
    def __init__(self, *args, **kwargs):
        
       
        # VOMS stuff
        try:
            self.voms_json = json.loads(
                open(VOMS_POLICY).read())
        except ValueError:
            raise ClientError(
                'Bad Formatted VOMS json',
                details='The VOMS json data was not corectly formatted in file %s' % VOMS_POLICY)
        except:
            raise ClientError(
                              'No loading of VOMS json file',
                details='The VOMS json file located in %s was not loaded' % VOMS_POLICY)
            return ClientError
        
        self._no_verify = False

        #super(VomsAuthN, self).__init__(*args, **kwargs)

    @staticmethod
    def _get_cert_chain(ssl_info):
        """Return certificate and chain from the ssl info in M2Crypto format"""

        cert = M2Crypto.X509.load_cert_string(ssl_info.get("cert", ""))
        chain = M2Crypto.X509.X509_Stack()
        for c in ssl_info.get("chain", []):
            aux = M2Crypto.X509.load_cert_string(c)
            chain.push(aux)
        return cert, chain

    def _get_voms_info(self, ssl_info):
        """Extract voms info from ssl_info and return dict with it."""

        try:
            cert, chain = self._get_cert_chain(ssl_info)
        except M2Crypto.X509.X509Error:
            raise ClientError(
                              'SSL data not verified',
                              details=CONTEXT_ENV)
       
        with voms_helper.VOMS(VOMSDIR_PATH,
                              CA_PATH, VOMSAPI_LIB) as v:
            if self._no_verify:
                v.set_no_verify()
               
            voms_data = v.retrieve(cert, chain)
            
            if not voms_data:
                raise VomsError(v.error.value)

            d = {}
            for attr in ('user', 'userca', 'server', 'serverca',
                         'voname',  'uri', 'version', 'serial',
                         ('not_before', 'date1'), ('not_after', 'date2')):
                if isinstance(attr, basestring):
                    d[attr] = getattr(voms_data, attr)
                else:
                    d[attr[0]] = getattr(voms_data, attr[1])

            d["fqans"] = []
            for fqan in iter(voms_data.fqan):
                if fqan is None:
                    break
                d["fqans"].append(fqan)

        return d

    @staticmethod
    def _split_fqan(fqan):
        """
        gets a fqan and returns a tuple containing
        (vo/groups, role, capability)
        """
        l = fqan.split("/")
        capability = l.pop().split("=")[-1]
        role = l.pop().split("=")[-1]
        vogroup = "/".join(l)
        return (vogroup, role, capability)
    
    def _process_environ(self, environ):
        
        LOG.warning("Getting the environment parameters...")
        # the environment variable CONTENT_LENGTH may be empty or missing
        try:
            request_body_size = int(environ.get('CONTENT_LENGTH', 0))
        except (ValueError):
            request_body_size = 0
            raise ClientError(
                'Not auth method provided',
                details='The request body is empty, while it should contain the authentication method')
            
        request_body = environ['wsgi.input'].read(request_body_size)
        
        print request_body
        
        request_body = request_body.replace("true","\"true\"")
        request_body = request_body.replace('"','\'' )  
        
        params_parsed = ast.literal_eval(request_body)
        
        
        params = {}
        for k, v in params_parsed.iteritems():
            if k in ('self', 'context'):
                continue
            if k.startswith('_'):
                continue
            params[k] = v
            
        
        environ[PARAMS_ENV] = params
        print environ[PARAMS_ENV]

    def is_applicable(self, environ):
        """Check if the request is applicable for this handler or not"""
        print "Checking if the request is applicable for this handler or not..."
        self._process_environ(environ)
        params = environ.get(PARAMS_ENV, {})
        auth = params.get("auth", {})
        if "voms" in auth:
            if "true" in auth["voms"]:
                return True
            else:
                raise ClientError(
                'Error in json',
                details='Error in JSON, voms must be set to true')
            
        return False


    def authenticate(self,ssl_data):
        
        try:
            voms_info = self._get_voms_info(ssl_data)
        except VomsError as e:
            raise e
        user_dn = voms_info["user"]
        user_vo = voms_info["voname"]
        user_fqans = voms_info["fqans"] 
        
        return user_dn, user_vo, user_fqans 

          
    def process_request(self, environ):
        
        print "Inside process_Request at last!!!!"
        if not self.is_applicable(environ):
            return self.application

        ssl_dict = {
            "dn": environ.get(SSL_CLIENT_S_DN_ENV, None),
            "cert": environ.get(SSL_CLIENT_CERT_ENV, None),
            "chain": [],
        }
        for k, v in environ.iteritems():
            if k.startswith(SSL_CLIENT_CERT_CHAIN_ENV_PREFIX):
                ssl_dict["chain"].append(v)

        voms_info = self._get_voms_info(ssl_dict)

        params  = environ[PARAMS_ENV]
        
        tenant_from_req = params["auth"].get("tenantName", None)
        
        print voms_info, tenant_from_req
        user_dn = voms_info["user"]
        user_vo = voms_info["voname"]
        user_fqans = voms_info["fqans"] 
        environ['REMOTE_USER'] = user_dn
        
        return user_dn, user_vo, user_fqans
