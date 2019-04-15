PyNetlify
=========

Python library and simple command line client to interact with Netlify REST API. Tested with Python versions 2.7, 3.5, 3.6, 3.7.

Requires Netlify account with an active authentication token. Visit https://www.netlify.com/docs/cli/#authentication for more information.


Install
-------

PyNetlify is available to install from PyPI::

   pip install pynetlify


Use as a command line client
----------------------------

Configure by setting your personal Netlify authentication token to pynetlify.ini file at current working directory. Example pynetlify.ini::

   [netlify]
   auth-token = <personal-authentication-token>

Create a new site

.. code-block:: bash

   python -m pynetlify create_site

Deploy folder to a site

.. code-block:: bash

   python -m pynetlify deploy_folder --site-id <site-id> <folder-to-deploy>

List sites

.. code-block:: bash

   python -m pynetlify list_sites

Delete site

.. code-block:: bash

   python -m pynetlify delete_site <site-id>

Print command line help

.. code-block:: bash

   python -m pynetlify --help

Print help for specific subcommand

.. code-block:: bash 

   python -m pynetlify <subcommand> --help


Use as a Python library
-----------------------

Import and create APIRequest object.

.. code-block:: python

   from pynetlify import pynetlify
   api_request = pynetlify.APIRequest('auth_token')

Create site.

.. code-block:: python

   newly_created_site = api_request.create_site({'name': 'newly-created-site'})

See pynetlify.py source for more.
