Organization of the Cassius package
===================================

The files and directories are listed below.  In this list, if submodule *B* depends on submodule *A*, then *B* is listed after *A*.

   * `cassius/`: main code directory
      * `mathtools.py`: mathematical objects and functions used to generate or label content
      * `utilities.py`: functions for specifying plot aspects, provided to the user for maximum flexibility
      * `color.py`: pre-defined colors and color manipulation functions
      * `containers.py`: objects that contain data, like histograms and scatter-plots
      * `_svgdraw.c`: optional module for viewing SVG interactively (compiled, see dependencies above)
      * `svgdraw.py`: the primary backend for drawing and viewing SVG
      * `__init__.py`: loads the user-level objects from all submodules into one namespace (see below)
      * `backends/`: directory for other backends, such as Ozone
   * `setup.py`: installation script
   * `applications/`: directory for command-line tools based on Cassius
   * `docs/`: source for this documentation

The following objects are loaded into the Cassius namespace by `import
cassius` or into the general namespace by `from cassius import *`.

.. include:: ../cassius/__init__.py
   :start-after: #STARTDOCUMENTATION
   :end-before: #ENDDOCUMENTATION

Code examples in the documentation all begin with `from cassius import *`.

