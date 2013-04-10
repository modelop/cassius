.. automodule:: cassius.containers

Scatter plots and X-Y data
--------------------------

Several different types of plots are all based on placing
two-dimensional data at X-Y points in a plane.  The most basic is a
scatter-plot, which just places some kind of marker at each point.
Line graphs (also called time-series if the horizontal axis represents
time) do the same thing, but connect each point with a line, instead
of markers or in addition to markers.  Plots with error bars are the
same thing, but with confidence level intervals at each point.

In Cassius, all of these plot types are represented by one class,
`Scatter`.  The plot types are produced by parameterization, making it
easy to add or remove markers, lines, and error bars.

.. todo::
   I've also seen plots with circles centered at each point, in which
   the radius of the circle conveys some meaning.  We could extend the
   *x*, *y*, *ex*, *ey*, *exl*, *eyl* list to include *r*, the radius
   of the circle, or we could re-interpret *ex* as radius in a
   different graphical output mode.  In fact, it could be useful to
   have an error ellipse at each point, where we re-use *ex* and *ey*
   as the two diagonal elements in the error matrix and add a
   correlation parameter *exy* for the off-diagonal element.  Or perhaps
   extend this list with *z*, represented by marker color (overriding
   `markercolor` and `markeroutline`), though this would also require
   adding `zmin`, `zmax`, and `tocolor` to transform data into a color
   range.

Scatter: X-Y points, line graphs, and error bars
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

The `Scatter` class represents X-Y data (with auxiliary fields for
error bars), and can draw it many different ways.  See the example
below.

.. container::

   Example of using `Scatter` to draw (1) markers at X-Y points, (2)
   error bars, (3) asymmetric error bars, (4) a line following the
   order of the points, (5) a function y(x), like a time-series, and
   (6) an inverse function x(y).  Lines and markers/error bars can be
   combined, but are not in this example.

   ::

         >>> from cassius import *
         >>> import random

	 >>> # make a dataset
         >>> xlist = [random.uniform(0., 1.) for i in xrange(20)]
         >>> ylist = [random.uniform(0., 1.) for i in xrange(20)]
         >>> exlist = [random.gauss(0.1, 0.01) for i in xrange(20)]
         >>> eylist = [random.gauss(0.1, 0.01) for i in xrange(20)]
         >>> exllist = [random.gauss(0.05, 0.01) for i in xrange(20)]
         >>> eyllist = [random.gauss(0.05, 0.01) for i in xrange(20)]

	 >>> # plot it six different ways with the Scatter class
         >>> view(Layout(2, 3, Scatter(x=xlist, y=ylist),
         ...                   Scatter(x=xlist, y=ylist, ex=exlist, ey=eylist),
         ...                   Scatter(x=xlist, y=ylist, ex=exlist, ey=eylist, exl=exllist, eyl=eyllist),
         ...                   Scatter(x=xlist, y=ylist, marker=None, connector="unsorted"),
         ...                   Scatter(x=xlist, y=ylist, marker=None, connector="xsort"),
         ...                   Scatter(x=xlist, y=ylist, marker=None, connector="ysort")),
         ...      leftmargin=0.2)

   .. image::
       PLOTS/Scatter_example1.png

Data can be inserted into a `Scatter` class as a single matrix or as
separate lists of equal length.  The most convenient method depends on
the data source.  To enter data as a single matrix, it is necessary to
also provide a signature `sig` to tell Cassius how to interpret it.
For instance, if your data are provided as a list of *(x, y, ey)*
triplets, `sig = ["x", "y", "ey"]`.  The `Scatter` class internally
stores data as a single matrix `values` with signature `sig`.

It is also possible to create an empty `Scatter` and fill it after
construction using `append` (similar to `Histogram.fill`).  However,
this is less efficient, because `append` must grow the array
allocation.  (Values are stored as `numpy` arrays, not Python lists.)

The `Scatter` class can be safely used for large datasets if an
appropriate `limit` is set.  The `limit` is the maximum number of
marker points shown within the coordinate frame.

.. container::

   Illustration of the `limit` parameter.  A million-element dataset
   is drawn (1) using only 20 points, (2) using 200 points, and (3)
   using 200 points within a tiny viewport around the point of peak
   density.

   ::

	>>> from cassius import *
	>>> import random

	>>> values = [[random.gauss(0.5, 0.2), random.gauss(0.5, 0.2)] for i in xrange(1000000)]
	>>> view(Scatter(values, sig=["x", "y"], limit=100, xmin=0.4, xmax=0.6, ymin=0.4, ymax=0.6))

	>>> view(Layout(1, 3, Scatter(values, sig=["x", "y"], limit=20),
	...                   Scatter(values, sig=["x", "y"], limit=200),
	...                   Scatter(values, sig=["x", "y"], limit=200, xmin=0.49, xmax=0.51, ymin=0.49, ymax=0.51)),
	...      width=2000, height=1000)

   .. image::
        PLOTS/Scatter_example2.png

Unless the user specifies `xmin`, `ymin`, `xmax`, and `ymax`, the axis
range will be automatically determined from the data.  The `calcrange`
parameter determines how the axis range is calculated.  The
`calcrange` and `calcrange_quartile` functions in the `utilities
module
<reference_utilities#auto-generating-ranges-and-binnings>`_ are
two useful options.

.. container::
   
   The `calcrange` function returns the most extreme values in *x* and
   *y*, while the `calcrange_quartile` function derives window
   boundaries from the shape of the distribution.  The former (the
   default) is useful if you want to make sure you see all of the
   data, while the latter is useful if you want to see the bulk of the
   distribution.

   ::

       >>> from cassius import *
       >>> from numpy.random import standard_cauchy as lorentz
       >>> small_dataset = [(lorentz(), lorentz()) for i in xrange(10)]
       >>> big_dataset = [(lorentz(), lorentz()) for i in xrange(1000)]

       >>> view(Layout(2, 2, Scatter(small_dataset, sig=["x", "y"], calcrange=calcrange),
       ...                   Scatter(small_dataset, sig=["x", "y"], calcrange=calcrange_quartile),
       ...                   Scatter(big_dataset, sig=["x", "y"], calcrange=calcrange),
       ...                   Scatter(big_dataset, sig=["x", "y"], calcrange=calcrange_quartile)),
       ...      leftmargin=0.15, fileName="Scatter_example3.svg")

   .. image::
      PLOTS/Scatter_example3.png

.. autoclass:: Scatter
   :members: setbysig, setvalues, sort, index, append, x, y, ex, ey, exl, eyl, ranges

.. todo::
   * Both methods for setting points _copies_ the whole input.  It may
     be desirable if `setbysig` merely references while `setvalues`
     copies.
   * Since there's an `append`, there should be an `extend` as well
     (which would be a more efficient way of adding large amounts of
     data)

TimeSeries: X axis interpreted as date/time
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

The `TimeSeries` class is just a subclass of `Scatter` with
convenience functions for converting time strings.  The underlying
functions that do the conversions are in the `utilities module
<reference_utilities#converting-timestrings>`_.

.. container::

   An illustration of `TimeSeries`: `times` is a list of time strings
   and `data` is a rough sinusoidal trend.  Two time string
   conversions are involved: `informat` specifies the conversion of
   strings to seconds since 1970 and `outformat` specifies another
   conversion back to strings, to format the horizontal axis nicely.

   ::

	>>> from cassius import *
	>>> import random, time, math

	>>> times = []
	>>> data = []
	>>> for i in xrange(1000):
	...     t = 1e9 + random.uniform(0, 1e6)
	...     x = 10.*math.sin(t * 2.*math.pi / (60*60*24*7)) + random.gauss(0., 1.) + 30.
	...     times.append(time.strftime("%b %d, %Y at %H:%M:%S", time.gmtime(t)))
	...     data.append(x)

	>>> times[:3]
	['Sep 12, 2001 at 16:20:47', 'Sep 19, 2001 at 01:29:01', 'Sep 16, 2001 at 11:01:25']

	>>> view(TimeSeries(informat="%b %d, %Y at %H:%M:%S", outformat="%m/%d/%y", x=times, y=data))

   .. image::
        PLOTS/TimeSeries_example1.png


.. autoclass:: TimeSeries
   :members: timeticks, fromtimestring, totimestring, setbysig, setvalues, sort, index, append, x, y, ex, ey, exl, eyl, ranges
