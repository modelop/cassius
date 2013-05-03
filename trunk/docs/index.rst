.. cassius documentation master file, created by
   sphinx-quickstart on Wed Feb  9 13:52:57 2011.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

Cassius the Plotter
===================

Cassius is a plotting toolset for the `Augustus
<http://code.google.com/p/augustus/>`_ statistical modeling package.

The front-end (user) interface is designed to be intuitive: common
tasks should be easy and all tasks should be possible.  It follows the
brief syntactical style of Python and, unlike many plotting toolkits,
does not depend on a global state that would make copying script
segments unreliable.

The back-end (graphical output) interface is designed to be flexible:
the primary output format is scalable SVG, which can be converted to a
broad range of vector and raster formats, but other formats can
be added as plug-in modules.  Even interactive widgets can be
supported.

A PDF version of this document can be found at `<http://192.168.15.14/pivarski/cassius_latex/cassius.pdf>`_.

Table of contents
-----------------

.. toctree::
   :maxdepth: 4

   tutorial
   installation
   organization
   percolation
   reference
   backends
   applications
   todo_items
