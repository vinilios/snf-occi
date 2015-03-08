.. snf-occi documentation master file, created by
   sphinx-quickstart on Mon Mar 26 13:45:54 2012.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

snf-occi's documentation!
====================================

**snf-occi** implements the OCCI specification and maps it to the Synnefo
OpenStack API, so ti acts as a translation bridge between OCCI and Synnefo.
It is designed to be as independent as possible from the rest IaaS, providing
an OCCI compatibility layer.

**snf-occi** utilizes the API library for the components of the synnefo
ecosystem provided by `kamaki <http://www.synnefo.org/docs/kamaki/latest>`_ .
It is built on top of kamaki.clients lib in order to communicate with the
required Synnefo APIs.


.. toctree::
   :maxdepth: 2

About OCCI
----------
The current OCCI specification consists of the following three documents:

* `OCCI Core <http://ogf.org/documents/GFD.183.pdf>`_
* `OCCI Infrastructure <http://ogf.org/documents/GFD.184.pdf>`_
* `OCCI HTTP rendering <http://ogf.org/documents/GFD.185.pdf>`_

The master document for the OCCI specification is at `OCCI Specification <http://occi-wg.org/about/specification/>`_

OCCI and Synnefo
-----------------
The OCCI implementation for Synnefo is in accordance with the OCCI
Infrastructure specification, that describes common Cloud IaaS components. The
correspondence between OCCI and OpenStack/Synnefo is as follows:

+-------------------------+-------------------------+
|OCCI                     |OpenStack/Synnefo        |
+=========================+=========================+
|Compute                  |Compute/servers          |
+-------------------------+-------------------------+
|OS Template              |Image                    |
+-------------------------+-------------------------+
|Resource Template        |Compute/flavors          |
+-------------------------+-------------------------+
|Network                  |Networking               |
+-------------------------+-------------------------+
|Storage                  |Block Storage            |
+-------------------------+-------------------------+


 
**Note:** Metadata info in synnefo's servers cannot be represented (clearly) using OCCI's components.


OCCI operations
------------------

Below you can see the required procedures/operations for OCCI compatibility.
   
* Handling the query interface
   * Query interface must be found under path /-/
   * Retrieve all registered Kinds, Actions and Mixins
   * Add a Mixin definition
   * Remove a Mixin definition

* Operation on paths in the name-space 
   * Retrieving the state of the name-space hierarchy
   * Retrieving all Resource instances below a path
   * Deletion of all Resource instances below a path

* Operations on Mixins and Kinds
   * Retrieving all Resource instances belonging to Mixin or Kind
   * Triggering actions to all instances of a Mixin or a Kind
   * Associate resource instances with a Mixin or a Kind
   * Full update of a Mixin collection
   * Dissociate resource instances from a Mixin

* Operations on Resource instances
   * Creating a resource instance
   * Retrieving a resource instance
   * Partial update of a resource instance
   * Full update of a resource instance
   * Delete a resource instance
   * Triggering an action on a resource instance

* Handling Link instances
   * Inline creation of a Link instance
   * Retrieving Resource instances with defined Links
   * Creating of Link Resource instance


OCCI client/server library
---------------------------

**pyssf** is a collection of OCCI python modules. It aims at providing a high-level interface for the integration of OCCI to other new or existing applications. 

**Features:**


* It includes the implementation of a REST API service with the OCCI specifications already implemented
* It only requires a custom backend and registry to interact with synnefo main components (e.g., Cyclades, Astakos. etc.)

snf-occi Installation
======================

Requirements
-------------

First, you need to install the required dependencies which can be found here:

* `pyssf at pypi <https://pypi.python.org/pypi/pyssf>`_
* `Kamaki repository  <https://github.com/grnet/kamaki>`_  (Detailed description for installation of kamaki can be found in this `Guide <http://www.synnefo.org/docs/kamaki/latest/installation.html>`_).

Moreover, some additional packages need to be installed::

$ apt-get install python-pip
$ pip install webob
$ apt-get install python-dev
$ pip install eventlet
$ apt-get install python-m2crypto
$ apt-get install python-pastedeploy
$ apt-get install libvomsapi1
$ apt-get install python-ldap

Also, you need to setup an accessible LDAP directory on the same or a different
host. The LDAP setup details depend on the host OS e.g.,

$ sudo apt-get install slapd


Installation
-------------

First, create the configuration file. By convention, the configuration file is
located at the home directory of the user who runs the service and is named
"snf-occi.conf". To overide the default path, set it to the SNF_OCCI_CONFIG
environment variable

.. code-block:: console

    $ export SNF_OCCI_CONFIG="/some/other/path"

The configuration file contains settings for the various system components::

    # snf-occi configuration file
    [kamaki]
    default_cloud = <CLOUD ALIAS>

    [pastedeploy]
    auth_ini = /home/USER_WHO_RUNS_SERVICE/snf_voms_auth-paste.ini
    ini = /home/USER_WHO_RUNS_SERVICE/snf_voms-paste.ini

    [server]
    port = 8888
    hostname = <fqdn of this host>
    arch = x86

    [voms]
    enable = on

    [ldap]
    url = ldap://localhost
    base_dn = ou=users,dc=live,dc=synnefo,dc=org
    use_tls = off
    user = <LDAP ADMIN USER DN>
    password = <LDAP ADMIN USER PASSWORD>
    # ca_certs = /etc/ssl/certs/cacert

    [cloud "<CLOUD ALIAS>"]
    url = https://accounts.live.synnefo.org/identity/v2.0
    token = <OCCI ADMIN TOKEN>

**NOTE**: ca_certs is optional, but recommended - it may require some
    modifications on the LDAP directory setup, though

Upon the completion of the previous steps, you can install **snf-occi** API translation server by cloning our latest source code:

* `snf-occi Repository <https://github.com/grnet/snf-occi>`_ 

Finally, the installation of snf-occi is done with the following steps::

$ python setup.py build
$ python setup.py install

In case that VOMS authentication mode is disabled, then the snf-occi server can be started by typing **snf-occi**.


Install using debian packages
============================

* Add extra apt repositories::

    $ curl https://dist.eugridpma.info/distribution/igtf/current/GPG-KEY-EUGridPMA-RPM-3 | apt-key add -
    $ echo "deb http://repository.egi.eu/sw/production/cas/1/current egi-igtf core" > /etc/apt/sources.list.d/egi-cas.list
    $ curl https://dev.grnet.gr/files/apt-grnetdev.pub | apt-key add -
    $ echo "deb http://apt.dev.grnet.gr wheezy/" > /etc/apt/sources.list.d/grnet.dev.list
    $ apt-get update

* Install snf-occi package::

    $ apt-get install snf-occi

* Update `snf-occi` configuration files

`snf-occi` configuration files are placed in `/etc/snf-occi`. Check other sections of this document 
for detailed configuration infomration.

* Verify vhost configuration and enable apache occi vhost
   
A common vhost file is placed in `/etc/apache2/sites-available/snfocci`. You can edit it 
or copy it to match your deployment configuration. To enable the occi vhosts::

    $ a2ensite snfocci
    $ service apache2 restart


Enabling VOMS authentication
============================

VOMS Requirements
------------------

* Installation of **EUgridPMA** certificates, which must be located on the standard location **/etc/grid-security/certificates**: 

::

$ wget -q -O - https://dist.eugridpma.info/distribution/igtf/current/GPG-KEY-EUGridPMA-RPM-3 | sudo apt-key add -
$ echo "deb http://repository.egi.eu/sw/production/cas/1/current egi-igtf core" > /etc/apt/sources.list.d/egi-cas.list (as root)
$ sudo apt-get update
$ sudo apt-get install ca-policy-egi-core

* Installation of the **fetch-crl** package:

::

$ sudo apt-get install fetch-crl
$ sudo fetch-crl

Moreover, a valid certificate issued by a valid CA is required for the server hosting snf-occi. The certificates of valid CAs are located in **/etc/grid-security/certificates/**. The server certificate and key file need to be located in **/etc/ssl** (if the directories with the certificate and key files differ, then the paths to these directories must be appropriately set in the
configuration file). 

::

$ ls /etc/ssl/certs/server.crt
$ ls /etc/ssl/private/server.key


Apache Installation and Configuration
------------------------------------------------
To enable VOMS authentication in snf-occi, the existence of a working Apache installation is a prerequisite. The installation and configuration process is as follows:

* Installation of Apache WSGI with mod_ssl enabled::

	$ sudo apt-get install apache2 libapache2-mod-wsgi
	$ sudo a2enmod ssl
	$ sudo a2enmod headers

* Create a user synnefo and configure Apache::

	$ sudo adduser synnefo
	
Assuming that the snf-occi server has the FQDN nodeX.example.com, then the following configurations are required:


* In **/etc/apache2/sites-enabled/snf_VOMS** add (In Apache 2.4.6, name this file as /etc/apache2/sites-enabled/snf_VOMS.conf)::

	WSGIDaemonProcess snf_voms user=synnefo group=nogroup processes=3 threads=10
	Listen 8888
	<VirtualHost _default_:8888>
  	  LogLevel warn
  	  ErrorLog ${APACHE_LOG_DIR}/error.log
	  CustomLog ${APACHE_LOG_DIR}/ssl_access.log combined

	  RequestHeader set X-Forwarded-Protocol "https" 
  
	  SSLEngine on
	  SSLCertificateFile    /etc/ssl/certs/server.crt
	  SSLCertificateKeyFile /etc/ssl/private/server.key

	  SSLCACertificatePath /etc/grid-security/certificates
	  SSLCARevocationPath /etc/grid-security/certificates
	  SSLVerifyClient optional
	  SSLVerifyDepth 20
	  SSLProtocol all -SSLv2
	  SSLCipherSuite ALL:!ADH:!EXPORT:!SSLv2:RC4+RSA:+HIGH:+MEDIUM:+LOW
	  SSLOptions +StdEnvVars +ExportCertData
	  WSGIScriptAlias /main /usr/lib/cgi-bin/snf_voms/main
	  WSGIProcessGroup snf_voms
	  WSGIPassAuthorization On
	  WSGIScriptAlias / /usr/lib/cgi-bin/snf_voms/main
	</VirtualHost>

	Listen 5000 
	<VirtualHost _default_:5000>
	  LogLevel warn
	  ErrorLog ${APACHE_LOG_DIR}/error.log
	  CustomLog ${APACHE_LOG_DIR}/ssl_access.log combined

	  SSLEngine on
	  SSLCertificateFile    /etc/ssl/certs/server.crt
	  SSLCertificateKeyFile /etc/ssl/private/server.key

	  SSLCACertificatePath /etc/grid-security/certificates
	  SSLCARevocationPath /etc/grid-security/certificates
	  SSLVerifyClient optional
	  SSLVerifyDepth 20
	  SSLProtocol all -SSLv2
	  SSLCipherSuite ALL:!ADH:!EXPORT:!SSLv2:RC4+RSA:+HIGH:+MEDIUM:+LOW
	  SSLOptions +StdEnvVars +ExportCertData

	  WSGIScriptAlias /main /usr/lib/cgi-bin/snf_voms/main_auth
	  WSGIScriptAlias /main /usr/lib/cgi-bin/snf_voms/main_auth
	  WSGIProcessGroup snf_voms
	</VirtualHost>


* In **/etc/apache2/httpd.conf** add::
	ServerName nodeX.example.com

	Note: In Ubuntu 14.04, the ServerName needs to be set in /etc/apache2/conf-available/fqdn.conf, namely:
	echo "ServerName nodeX.example.com" | sudo tee /etc/apache2/conf-available/fqdn.conf
    sudo ln -s /etc/apache2/conf-available/fqdn.conf /etc/apache2/conf-enabled/fqdn.conf
    
 * In Apache 2.4.x, the following lines need to be added in /etc/apache2/apache2.conf::

   <Directory /usr/lib/cgi-bin/snf_voms/>
      Options FollowSymLinks
      AllowOverride None
      Require all granted
   </Directory>

* In **/etc/apache2/conf.d/wsgi-snf_voms.conf** add::

	WSGIScriptAlias /main /usr/lib/cgi-bin/snf_voms/main
	WSGIScriptAlias /main /usr/lib/cgi-bin/snf_voms/main_auth

	<Location "/main">
 	  SSLRequireSSL
 	  Authtype none
	</Location>

* To support VOMS authentication, snf-occi must be executed as a WSGI application. To achive this goal, the respective scripts included in the snf-occi repository need to be placed in the appropriate directories. In more detail, you have to copy the following scripts located in the **snfOCCI/httpd** directory in the appropriate directory and create the following links ::

	$ mkdir /usr/lib/cgi-bin/snf_voms
	$ cp snf-occi/snfOCCI/httpd/snf_voms.py /usr/lib/cgi-bin/snf_voms/snf_voms.py
	$ ln /usr/lib/cgi-bin/snf_voms/snf_voms.py /usr/lib/cgi-bin/snf_voms/main
	$ cp snf-occi/snfOCCI/httpd/snf_voms_auth.py /usr/lib/cgi-bin/snf_voms/snf_voms_auth.py
	$ ln /usr/lib/cgi-bin/snf_voms/snf_voms_auth.py /usr/lib/cgi-bin/snf_voms/main_auth
	$ cp snf-occi/snfOCCI/httpd/snf_voms_auth-paste.ini /home/synnefo/snf_voms_auth-paste.ini
	$ cp snf-occi/snfOCCI/httpd/snf_voms-paste.ini /home/synnefo/snf_voms-paste.ini 
	$ chown -R synnefo:synnefo /home/synnefo/snf_voms*



* In **/etc/apache2/envvars** add::

	export OPENSSL_ALLOW_PROXY_CERTS=1


Configure VO Membership Information
------------------------------------

In order to support VOMS authentication, some configuration information is required. This information is provided in the following files. For example, to allow the access for members of the fedcloud.egi.eu VO, the following configuration files need to be present in the directory **/etc/snf** :

* In **/etc/snf/voms.json** add::

	{
    	  "fedcloud.egi.eu": 
          {
            "tenant": "EGI_FCTF"
          }
        }

Moreover, the vomsdir information and the vomses file need to be created and altered respectively for each allowed VO (see also `Fedcloud-tf:CLI Environment <https://wiki.egi.eu/wiki/Fedcloud-tf:CLI_Environment>`_). For example, the respective folders and files for the **fedcloud.egi.eu** VO are created in the following two steps:

* Creation of the vomsdir information::

	$ mkdir -p /etc/grid-security/vomsdir/fedcloud.egi.eu
	$ cat > /etc/grid-security/vomsdir/fedcloud.egi.eu/voms1.egee.cesnet.cz.lsc <<EOF 
	/DC=org/DC=terena/DC=tcs/OU=Domain Control Validated/CN=voms1.egee.cesnet.cz 
	/C=NL/O=TERENA/CN=TERENA eScience SSL CA 
	EOF
	$ cat > /etc/grid-security/vomsdir/fedcloud.egi.eu/voms2.egee.cesnet.cz.lsc <<EOF 
	/DC=org/DC=terena/DC=tcs/OU=Domain Control Validated /CN=voms2.grid.cesnet.cz
	/C=NL/O=TERENA/CN=TERENA eScience SSL CA
	EOF


* Creation / Extension of the vomses file::

	$ cat >> /etc/vomses <<EOF
	"fedcloud.egi.eu" "voms1.egee.cesnet.cz" "15002" "/DC=org/DC=terena/DC=tcs/C=CZ/O=CESNET/CN=voms1.egee.cesnet.cz" "fedcloud.egi.eu" "24"
    "fedcloud.egi.eu" "voms2.grid.cesnet.cz" "15002" "/DC=org/DC=terena/DC=tcs/C=CZ/O=CESNET/CN=voms2.grid.cesnet.cz" "fedcloud.egi.eu" "24"
	EOF

Upon the completion of all configuration actions, start (or restart) the Apache server:

$  sudo service apache2 start


Usage Scenarios
================

For the examples below, we assume that the snf-occi server is running on  <snf-occi_host> (port 8888) and authentication token is $AUTH. For the HTTPS requests we are using **curl**.

The user must have a valid authentication token in order to interact with the snf-occi endpoint. In case that the VOMS authentication is enabled, then the user can provide his/her proxy certificate in order to obtain a valid authentication token. 

* A user participating in a specific VO must have a valid VOMS proxy. To obtain a proxy certificate type the command (More information about the setup of a FedCloud command-line environment in order to obtain a proxy certificate can be found at `Fedcloud-tf:CLI Environment <https://wiki.egi.eu/wiki/Fedcloud-tf:CLI_Environment>`_.)::
	
	$ voms-proxy-init -voms fedcloud.egi.eu -rfc


* Retrieve an authentication token (hence referring as $AUTH) from the snf-occi server, assuming that the proxy certificate is the file $X509_USER_PROXY (e.g., /tmp/x509up_u1000) and <snf-occi_host> is the hostname of server hosting snf-occi::

	$ curl --capath /etc/grid-security/certificates --cert $X509_USER_PROXY -d '{"auth":{"voms": true, "tenantName": "fedcloud.egi.eu"}}' -v -X GET https://<snf-occi_host>:5000/main/v2.0/tokens 

* Retrieve all registered Kinds, Actions and Mixins:

  ::

	$ curl --capath /etc/grid-security/certificates -X GET https://<snf-occi_host>:8888/-/ -H 'X-Auth-Token:$AUTH'


* List all VMs::

	$ curl --capath /etc/grid-security/certificates -X GET https://<snf-occi_host>:8888/compute/ -H 'X-Auth-Token:$AUTH'
	

* Create a new VM using the the flavor 'c1r1024d5rdb' and the image 'ubuntu_server'

  ::
 
	$ curl --capath /etc/grid-security/certificates -X POST https://<snf-occi_host>:8888/compute/ -H 'Category: compute; scheme=http://schemas.ogf.org/occi/infrastructure#;  class="kind";' -H 'X-OCCI-Attribute: occi.core.title = newVM' -H 'Category: c1r1024d5drbd; scheme=http://schemas.ogf.org/occi/resource_tpl#; ' -H 'Category: ubuntu_server; scheme=http://schemas.ogf.org/occi/os_tpl#;' -H 'X-Auth-Token:$AUTH'  -H 'Content-type: text/occi'


* Retrieve all the details of th VM with identifier $ID::

	$ curl --capath /etc/grid-security/certificates -X GET https://<snf-occi_host>:8888/compute/$ID -H 'X-Auth-Token: $AUTH'


* Perform a STOP action upon a VM::

	$ curl -X POST https://<snf-occi_host>:8888/compute/$ID?action=stop -H 'Content-type: text/occi' -H 'X-Auth-Token: $AUTH'  -H 'Category: stop; scheme="http://schemas.ogf.org/occi/infrastructure/compute/action#"; class="action"'

* Perform a START action upon a VM::

	$ curl -X POST https://<snf-occi_host>:8888/compute/$ID?action=start -H 'Content-type: text/occi' -H 'X-Auth-Token:$AUTH' -H 'Category: start; scheme="http://schemas.ogf.org/occi/infrastructure/compute/action#"; class="action"'


* Delete the VM with identifier $ID::
  
	$ curl --capath /etc/grid-security/certificates -X DELETE https://<snf-occi_host>:8888/compute/$ID -H 'X-Auth-Token: $AUTH'


Moreover, the `rOCCI cli <https://github.com/gwdg/rOCCI-cli>`_ can be used directly from shell defining the following parameters:

	* --endpoint https://<snf-occi_host>:8888 
	* --auth x509
	* --voms
	* --user-cred $X509_USER_PROXY

Administration tools
--------------------

Administration is assisted by the kamaki command line client. Kamaki is used to
query synnefo deployments and it is a requirement of the system.

The system automatically installs a kamaki plugin to access the user admin API.
This plugin is disabled by default. To enable it, ssh on the server and:

.. code-block:: console

    $ kamaki config set xuser_cli astavoms.cli

Also, make sure to set the correct URL and admin synnefo TOKEN:

.. code-block:: console

    $ kamaki config set cloud.default.url URL
    $ kamaki config set cloud.default.token TOKEN

This will allow the administration of synnefo users, with the "xuser" commands.


Future Directions
-----------------

The snf-occi server is constantly evolving and being enhanced with more new features in order to support more advanced functionalities. For instance, some upcoming features are:

* Network Management
 
Indices and tables
==================

* :ref:`genindex`
* :ref:`search`
