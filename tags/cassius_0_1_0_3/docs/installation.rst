Installation
============

Summary
-------

The essential part of Cassius is pure Python with a standard setup.py script; thus, installation will usually be straight-forward. Most of the content of this page covers contingencies that may exist on your system.

These instructions are also available on the `Cassius wiki <http://code.google.com/p/cassius/wiki/Installation>`_.

Dependencies
------------

Cassius requires at least `Python 2.6 <http://www.python.org/>`_, `NumPy 1.3 <http://numpy.scipy.org/>`_, `PIL 1.1.7 <http://www.pythonware.com/products/pil/>`_, and `Augustus 0.4.2.1 <http://code.google.com/p/augustus/>`_.

The Python dependencies can be installed in Ubuntu 10.04 (or later) with::

   linux> sudo apt-get install python python-numpy python-imaging

and Augustus can be installed by following the `Augustus instructions <http://code.google.com/p/augustus/wiki/Installation>`_.

**One more thing:** to use Augustus's UniTable, we also need PyGSL (you would only notice this if you call the cassius.inspect() function). To get it, do the following::

    linux> sudo apt-get install gsl-bin libgsl0-dev python-dev gcc
    linux> http://sourceforge.net/projects/pygsl/files/pygsl/pygsl-0.9.5/pygsl-0.9.5.tar.gz/download -O pygsl-0.9.5.tar.gz
    linux> tar -xzvf pygsl-0.9.5.tar.gz
    linux> cd pygsl-0.9.5/
    linux> sudo python setup.py install
    linux> cd ..

Future versions of Cassius won't have this dependency.

Optional add-on
---------------

While developing a plotting script, it is often useful to see updates in a plot without having to save a file and load it in another program. For this reason, Cassius has an interactive viewer module that can be invoked with::

   >>> view(plot_object)

The viewer has the following dependencies: `GTK <http://www.gtk.org/>`_, `librsvg 2.32.0 <http://librsvg.sourceforge.net/>`_, and `Cairo <http://www.cairographics.org/>`_, and it must be compiled as a C program. These dependencies can be satisfied in Ubuntu **10.10** or later with::

   linux> sudo apt-get install python-dev libgtk2.0-dev libglib2.0-dev librsvg2-dev libcairo2-dev

(The librsvg in Ubuntu 10.04 (librsvg 2.26.2) is not sufficient.)

*The viewer is optional.*  Without it, Cassius can save plots as files with::

   >>> draw(plot_object, fileName="plot.svg")

Also, Cassius only directly outputs SVG files. If you do not have any software to view, edit, or convert SVG files, I recommend Inkscape::

   linux> sudo apt-get install inkscape
   linux> inkview plot.svg                           # quick viewer
   linux> inkscape plot.svg                          # fully featured editor
   linux> inkscape plot.svg --export-pdf=plot.pdf    # convert to PDF
                                                     # convert to PNG at a given scale
   linux> inkscape plot.svg --export-png=plot.png --export-width=400 --export-background=white

Installing Cassius
------------------

   1. Download a Cassius archive from the `downloads page <http://code.google.com/p/cassius/downloads/list?q=label:Cassius>`_. The filename is cassius-x_y_z_b.tgz or cassius-x_y_z_b.zip. 

   2. Unpack the archive and enter the installation directory::

         linux> tar -xzvf cassius-x_y_z_b.tgz
         linux> cd cassius-x_y_z_b/

      or::

         windows> unzip cassius-x_y_z_b.zip
         windows> cd cassius-x_y_z_b

   3. Invoke the setup.py script, either with normal user privileges (local installation) or as the superuser (system-wide installation).

Local installation
^^^^^^^^^^^^^^^^^^

::

   linux> python setup.py install --home=/path/to/desired/location

where ``/path/to/desired/location`` can be your home directory, ~.

The installation script attempts to compile the optional viewer, but if the dependencies are not met, it will just present a warning message and install the rest of the package.

If ``/path/to/desired/location`` does not contain a ``bin`` and a ``lib`` directory, these directories will be created and filled with executable scripts and the Cassius libraries, respectively. To access the executable scripts from a commandline, you may need to add the ``bin`` directory to your ``PATH`` environment variable::

   linux> export PATH=/path/to/desired/location/bin:$PATH

To access the Cassius libraries in Python, you may need to add the ``lib`` directory to your ``PYTHONPATH``::

   linux> export PYTHONPATH=/path/to/desired/location/lib/python:$PYTHONPATH

You can check your ``PATH`` by executing one of the scripts::

   linux> CassiusScorePlane --help
   ...

and you can check your ``PYTHONPATH`` by loading the Cassius module from a directory other than the installation directory::

   linux> cd /
   linux> python
   >>> import cassius

To be sure that these environment variables are correctly set in new terminals, add them to your login script. If your shell is ``csh`` or ``tcsh`` (check with ``echo $SHELL``), use the::

   linux> setenv VARIABLE value

syntax instead.

System-wide installation
^^^^^^^^^^^^^^^^^^^^^^^^

::

   linux> sudo python setup.py install

The installation script attempts to compile the optional viewer, but if the dependencies are not met, it will just present a warning message and install the rest of the package.

The scripts and Cassius module will be installed in your system's standard locations, so it is not necessary to set environment variables.

Verifying installation
----------------------

To verify your installation of Cassius, try the following simple commands::

   >>> from cassius import *
   >>> dir()
   ['Auto', 'ClosePolygon', 'ColorField', 'Curve', 'DAY', 'EdgeTo', 'Grid', 'HLS', 'HOUR', 'HSV',
   'Histogram', 'HistogramCategorical', 'HistogramNonUniform', 'Infinity', 'InspectTable',
   'Layout', 'Legend', 'Line', 'MINUTE', 'MONTH', 'MinusInfinity', 'MoveTo', 'Overlay', 'RGB',
   'Region', 'RegionMap', 'SECOND', 'Scatter', 'Stack', 'Style', 'TimeSeries', 'WEEK', 'YEAR',
   '__builtins__', '__doc__', '__name__', '__package__', 'asymptotic_shift', 'binning',
   'calcrange', 'calcrange_quartile', 'color', 'colors', 'containers', 'correlation', 'covariance',
   'darken', 'darkseries', 'draw', 'drawpdf', 'epsilon', 'erf', 'erfc', 'fromtimestring',
   'gaussian_likelihood', 'gradient', 'gradients', 'inspect', 'lighten', 'lightseries',
   'linearfit', 'mathtools', 'mean', 'poisson_likelihood', 'regular', 'rms', 'round_errpair',
   'round_sigfigs', 'stdev', 'str_errpair', 'str_round', 'str_sigfigs', 'svgdraw', 'tickmarks',
   'timeticks', 'totimestring', 'truncated_shift', 'ubiquitous', 'unicode_errpair', 'unicode_number',
   'utilities', 'view', 'wmean']
   # The above output will vary, depending on version.  This is for 0.1.0.0.

   >>> histogram = Histogram(20, 0., 20.)
   >>> histogram.fill(range(2, 15))
   >>> histogram.fill(range(10, 18))
   >>> print histogram
   bin                            value
   ========================================
   [0, 1)                         0
   [1, 2)                         0
   [2, 3)                         1
   [3, 4)                         1
   [4, 5)                         1
   [5, 6)                         1
   [6, 7)                         1
   [7, 8)                         1
   [8, 9)                         1
   [9, 10)                        1
   [10, 11)                       2
   [11, 12)                       2
   [12, 13)                       2
   [13, 14)                       2
   [14, 15)                       2
   [15, 16)                       1
   [16, 17)                       1
   [17, 18)                       1
   [18, 19)                       0
   [19, 20)                       0

   >>> view(histogram)
   >>> draw(histogram, fileName="/tmp/output.svg")

If the interactive viewer was compiled and installed, then ``view(histogram)`` would pop up a window containing the histogram. If not, you would get a message like the following::

   Traceback (most recent call last):
     File "<stdin>", line 1, in <module>
     File "cassius/svgdraw.py", line 128, in view
       raise RuntimeError, "The '_svgview' extension module has not been compiled; use \"draw(object, fileName='...')\" instead."
   RuntimeError: The '_svgview' extension module has not been compiled; use "draw(object, fileName='...')" instead.

To view the plot in ``/tmp/output.svg``, try::

   linux> inkview /tmp/output.svg

It should look like this:

.. image:: PLOTS/wiki_Installation_output.png
