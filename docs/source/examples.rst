Examples
========

This section shows the application of ``calatrava`` to several open-source projects.


All the graphs are generated with the following command:

.. code-block:: bash

    calatrava uml <args> --config <config_file> -o <graph_name>


The configuration file `examples.json <https://raw.githubusercontent.com/lpereira95/calatrava/master/docs/examples/examples.json>`_ defines ``<args>>``, ``<config_file>``, and ``<graph_name>``:

* ``<args>`` is the union of ``package_folder`` and ``imports``. The package is cloned from remote to a temporary directory to be parsed.

* ``<config_file>`` is obtained from ``config``. The file should be located in ``docs/examples/config``. The configuration file associated with each image can be accessed by clicking on the image.

* ``<graph_name>`` comes from ``graph_name``. It has to be unique.



.. include:: _data.rst