.. automodule:: cassius.containers

Regions of the plane
--------------------

It is sometimes useful to draw two-dimensional regions, for example,
when expressing complicated cuts or the output of a machine learning
algorithm.

Region: colored region of 2-D space
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

The `Region` class describes a region using a sequence of vector-based
commands: `MoveTo`, `EdgeTo`, and `ClosePolygon`.  Coordinates for the
vector-based commands may include `Infinity` and multiples of
`Infinity` to enclose an infinite region (see the `mathtools module
<reference_mathtools#special-numbers>`_).

.. container::

   Example

   ::

	  >>> from cassius import *
	  >>> from math import sin, cos, pi

	  >>> # the bottom half of the plane
	  >>> r1 = Region(MoveTo(-Infinity, 0.), EdgeTo(Infinity, 0.), EdgeTo(Infinity, -Infinity),
          ...             EdgeTo(-Infinity, -Infinity), ClosePolygon(), fillcolor="lightblue")

	  >>> # a circular region built up from 1000 finite vector-based commands
	  >>> r2 = Region(MoveTo(1., 0.), fillcolor="yellow")
	  >>> for i in xrange(1000):
	  ...     r2.commands.append(EdgeTo(cos(i*2.*pi/1000.), sin(i*2.*pi/1000.)))

	  >>> r2.commands.append(ClosePolygon())

	  >>> # two crystal-shaped regions, each containing different corners of infinity
	  >>> r3 = Region(MoveTo(1., 1.), EdgeTo(2., 1.), EdgeTo(Infinity, Infinity*2.),
          ...             EdgeTo(Infinity*2., Infinity), EdgeTo(1., 2.), ClosePolygon(),
          ...             fillcolor="pink")
	  >>> r4 = Region(MoveTo(-1., 1.), EdgeTo(-2., 1.), EdgeTo(-Infinity, Infinity*2.),
          ...             EdgeTo(-Infinity*2., Infinity), EdgeTo(-1., 2.), ClosePolygon(),
          ...             fillcolor="lightgreen")

	  >>> view(Overlay(r1, r2, r3, r4))

   .. image::
          PLOTS/Regions_example1.png

**Gotcha:** Be sure to include empty parentheses after `ClosePolygon`
to add a `ClosePolygon` object to the commands list, rather than the
class itself.

.. autoclass:: Region

.. autoclass:: MoveTo

.. autoclass:: EdgeTo

.. autoclass:: ClosePolygon

RegionMap: region defined point-by-point
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

The `RegionMap` class describes a region as a raster image, rather
than a sequence of vector-based commands.

.. autoclass:: RegionMap

.. todo::
   `RegionMap` derives from `ColorField`, so if `ColorField` needs to be
   improved, then `RegionMap` does as well.
