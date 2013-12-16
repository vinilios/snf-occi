import os

from paste import deploy

import logging 

LOG = logging.getLogger(__name__)

# NOTE(ldbragst): 'application' is required in this context by WSGI spec.
# The following is a reference to Python Paste Deploy documentation
# http://pythonpaste.org/deploy/
application = deploy.loadapp('config:/home/synnefo/snf_voms-paste.ini')
