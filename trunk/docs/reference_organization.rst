.. automodule:: cassius.containers

Combining plots in a single view
--------------------------------

It is often desirable to show several datasets at once, to correlate
patterns in the data by eye.  The plots may be side-by-side,
overlapping, or stacked: each case has a corresponding object.

All of these objects may be used as drop-in replacements for a single
plot object, and they all have a `plots` member function containing
the list of plots they represent.

Layout: a grid of plots
^^^^^^^^^^^^^^^^^^^^^^^

A ``Layout`` object represents an arrangement of plots in a side-by-side
grid.  The desired number of rows and columns is required; they may
either be specified at the beginning of the constructor or as keyword
arguments.  Layouts can also be nested (see examples below).

.. autoclass:: Layout
   :members: index

.. container::

   First example: a two-by-two grid of plots.

   ::
 
      >>> from cassius import *
      >>> histogram = Histogram(10, 0, 1, fillcolor="yellow")
      >>> histogram.fill([0.1, 0.1, 0.5, 0.8, 0.1])

      >>> view(Layout(2, 2, histogram, histogram, histogram, histogram))

   .. image:: PLOTS/Layout_1.png

.. container::

   Second example: nested ``Layouts`` to create one wide plot above
   two small plots.

   ::

      >>> view(Layout(2, 1, histogram,
      ...                   Layout(1, 2, histogram, histogram)))

   .. image:: PLOTS/Layout_2.png

.. todo:: Optimize axis margins for cases other than just Layout(1, 1).  There should be some linear function that keeps axis labels from overlapping each other, for all reasonable sizes and aspect ratios.  That way, the user won't have to fiddle with it by hand each time.

.. todo:: Allow variable row and column widths.

Multiframe: a grid of plots with shared axes
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. todo:: Not implemented yet: this would both cover plots with common axes and "split axis" plots with the same object.  It would behave like a `Layout`, but the plots on the bottom and right edges would set the axes for everything in their row/column.


Overlay: multiple plots in the same coordinate frame
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

An ``Overlay`` object represents a set of overlapping objects, such as
plots and annotations.  Any object that draws itself in a coordinate
frame can be used in an ``Overlay``.  If no ``frame`` is specified,
the coordinate frame will be large enough to show all objects.  If
``frame`` is an index *i* (starting with zero), the *ith* object's
frame will be used.

Like any other plotable object, ``Overlays`` can be used inside of
``Layouts``.

.. autoclass:: Overlay
   :members: append, prepend, ranges

.. container::

   This example shows four ways of overlaying two histograms,
   differing in plot order (`h1` above `h2` or `h2` above `h1`) and
   `frame`.

   ::

      >>> from cassius import *
      >>> from random import gauss

      >>> h1 = Histogram(100, 0., 1., data=[gauss(0.4, 0.15) for i in xrange(10000)],
      ...                             fillcolor="lightblue")
      >>> h2 = Histogram(100, 0., 2., data=[gauss(0.7, 0.3) for i in xrange(10000)],
      ...                             fillcolor="pink")

      >>> view(Layout(2, 2, Overlay(h1, h2),
      ...                   Overlay(h2, h1),
      ...                   Overlay(0, h1, h2),           # frame is 0
      ...                   Overlay(h1, h2, frame=1)))    # frame is 1

   .. image:: PLOTS/Overlay_1.png

Stack: histograms on top of one another
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

The ``Stack`` container is used to overlay histograms by adding their
contents.  It can only be used for histograms (no other types of
plots) with exactly the same bins (same number of bins, same low edge,
same high edge).

.. autoclass:: Stack
   :members: stack, bins, ranges

.. container::

   This example demonstrates stacking of histograms.

   ::

      >>> from cassius import *
      >>> from numpy.random import standard_cauchy as lorentz

      >>> h1 = Histogram(100, 0., 1., data=[0.3 + 0.1*lorentz() for i in xrange(10000)],
      ...                             fillcolor="lightblue")
      >>> h2 = Histogram(100, 0., 1., data=[0.7 + 0.1*lorentz() for i in xrange(15000)],
      ...                             fillcolor="pink")

      >>> view(Layout(2, 1, Stack(h1, h2), Stack(h2, h1)))

   .. image:: PLOTS/Stack_1.png
