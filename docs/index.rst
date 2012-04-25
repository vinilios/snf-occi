.. snf-occi documentation master file, created by
   sphinx-quickstart on Mon Mar 26 13:45:54 2012.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

snf-occi's documentation!
====================================

**snf-occi** implements OCCI specifications to synnefo's API in order to achieve greater interoperability in common tasks refering cyclades management. This module is a translation bridge between OCCI and Openstack API and is designed to be as independent as possible from the rest IaaS, providing an OCCI compatibility layer to other services using Openstack API. 

**snf-occi** is based in modules provided by kamaki cli-tool when dealing with REST API calls to Openstack.

.. toctree::
   :maxdepth: 2

About OCCI
----------
Current OCCI specification consists of the following three documents:

* `OCCI Core <http://ogf.org/documents/GFD.183.pdf>`_
* `OCCI Infrastructure <http://ogf.org/documents/GFD.184.pdf>`_
* `OCCI HTTP rendering <http://ogf.org/documents/GFD.185.pdf>`_

OCCI and Cyclades
-----------------
OCCI implementation in Cyclades is going to be based in the **OCCI Infrastructure** specifications, in which common Cloud IaaS components are described. Below you can see the matching components between OCCI and Cyclades:

+-------------------------+-------------------------+
|OCCI                     |Cyclades                 |
+=========================+=========================+
|Compute                  |Synnefo servers          |
+-------------------------+-------------------------+
|OS Template              |Synnefo images           |
+-------------------------+-------------------------+
|Resource Template        |Synnefo flavors          |
+-------------------------+-------------------------+
|Networking               |NA                       |
+-------------------------+-------------------------+
|Storage                  |NA                       |
+-------------------------+-------------------------+


 
**Note:** Metadata info in synnefo's servers cannot be represented (clearly) using OCCI's components.


OCCI requirements
------------------
Due to OCCI's structure there cannot be straightforward mapping to Cyclades/OpenStack API. The missing elements are networking and storage capabilities using current Cyclades API.

**Note:** Quantum API support is being planned.

OCCI operations list
***********************

Below you can see the required procedures/operations for OCCI compatibility.
   
* Handling the query interface
   * Query interface must be found under path /-/
   * Retrieve all registered Kinds, Actions and Mixins
   * Add a mixin definition
   * Remove a mixin definition

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
==========================

occi-py is a generic library implementation of the Open Cloud Computing Interface (OCCI). It aims to provide a high-level interface for the integration of OCCI to other new or existing applications. 

Features:
---------

* It includes a REST API service with the OCCI specifications already implemented
* It only requires a custom backend and registry to interact with Cyclades
* Implements a simple web frontend server with support for Tornado WSGI

Package on pypi: `OCCI 0.6 <http://pypi.python.org/pypi/occi/0.6>`_


Indices and tables
==================

* :ref:`genindex`
* :ref:`search`

