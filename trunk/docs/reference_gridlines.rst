.. automodule:: cassius.containers

Grids, Lines, and Text
----------------------

Grids and lines are used to guide the eye, and text is used for annotation.


Grid: adding regular grids or individual lines
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. container::

   Grids are specified by a list of horizontal positions and/or a list
   of vertical positions.  The `regular` function in the `utilities
   module <reference_utilities#specifying-grids-and-tick-marks>`_
   is useful for generating these numbers.

   ::

	  >>> from cassius import *
	  >>> from math import sqrt

	  >>> curve = Curve("10.*x**3 - 10.*x**2 + x")

	  >>> view(Layout(2, 2, curve,
	  ...                   Overlay(Grid(vert=regular(0.1)), curve),
	  ...                   Overlay(Grid(horiz=regular(0.1)), curve),
	  ...                   Overlay(Grid(regular(0.1), regular(0.1)), curve)))
	  ...

   .. image::
       PLOTS/Grid_example1.png

   But they can also be user-specified.

   ::

	  >>> # using a grid to focus on the minimum of a function
	  >>> x0 = 1./3. + sqrt(7./10.)/3.
	  >>> y0 = (-55. - 7.*sqrt(70.))/135.
	  >>> grid = Grid(vert=[x0, x0-0.1, x0+0.1], horiz=[y0])
	  >>> view(Overlay(grid, curve))

   .. image::
       PLOTS/Grid_example2.png


.. autoclass:: Grid

Line: a line segment or ray
^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. container::

   A `Line` is simply a straight line that connects two points
   (technically, a line segment) or one finite point and a point at
   infinity (technically, a ray).

   ::
 
      >>> from cassius import *
      >>> line = Line(0., 0., Infinity, Infinity * 5., \
      ...             xmin=0., ymin=0., xmax=10., ymax=10.)
      >>> view(layout)

   .. image:: PLOTS/mathtools_Infinity.png

.. autoclass:: Line

Text: annotations in the coordinate space
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. todo::
   Implement the `Text` class.  It should be easy.
