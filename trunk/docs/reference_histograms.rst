.. automodule:: cassius.containers

Histograms
----------

Histograms are perhaps the most important type of plot in statistics,
because they quantify distributions with more precision than can be
seen by looking at the collection of data points themselves.  It
therefore needs to be easy to create, manipulate, and view many
histograms in the process of an analysis.  Cassius provides three
histogram classes with a lot of shared behavior:

   * `Histogram` for distributions over a continuous range,
     partitioned into a regular number of bins;
   * `HistogramNonUniform` for distributions over a continuous range,
     partitioned into user-specified intervals;
   * `HistogramCategorical` for distributions over a finite set of
     categories, represented by strings.

The `HistogramCategorical` case includes bar charts, and in principle
pie charts.  (Drawing `HistogramCategoricals` as pie charts has not
been implemented.)

Features and examples
^^^^^^^^^^^^^^^^^^^^^

Empty histograms can be allocated and filled later, or data can be
passed to a histogram's constructor.  Histograms can be printed to the
text terminal for a quick look at their contents during development.
Histograms can also store a copy of the dataset used to create it, to
allow later changes to the bin sizes and spacing.  It is also possible
to weight the data, so that some entries are emphasized at the expense
of others.

The vertical axis in plotted histograms represents the number of
entries per bin (or sum of weights per bin for weighted data).  This
is unlike R, in which the vertical axis is a density (number of
entries per bin times width of the bin).

.. container::

      Three data-filling examples.

      ::

      	 >>> from cassius import *
      	 >>> import random, numpy

      	 >>> h1 = Histogram(100, 0., 1.)            # allocate (book) a histogram
      	 >>> for i in xrange(10000):                # fill it with data generated
      	 ...     h1.fill(random.gauss(0.5, 0.1))    # on the fly
      	 ... 

      	 >>> dataset = numpy.array([random.gauss(0.5, 0.1) for i in xrange(10000)])

      	 >>> h2 = Histogram(100, 0., 1.)            # allocate another histogram
      	 >>> h2.fill(dataset)                       # fill it with all the data

      	 >>> h3 = Histogram(100, 0., 1., data=dataset)   # allocate and fill

      	 >>> view(Layout(1, 3, h1, h2, h3), 
      	 ...      leftmargin=0.2, height=500, width=1000)

      .. image::
         PLOTS/Histogram_example1.png

.. container::

      Quick print-out of histogram contents (for three different types of histograms).

      ::

         >>> from cassius import *
         >>> import random

         >>> # First dataset: Gaussian-distributed numbers
         >>> dataset = [random.gauss(0.5, 0.1) for i in xrange(1000000)]
	 >>> dataset[:3]
	 [0.48374693701030957, 0.43524708038962179, 0.49343378450571512]

	 >>> # Second dataset: uniformly-distributed strings
         >>> strings = ["one", "two", "three", "four", "five", "whatever"]
         >>> dataset2 = [strings[random.randint(0, 5)] for i in xrange(10000)]
         >>> dataset2[:8]
         ['three', 'one', 'two', 'five', 'five', 'whatever', 'one', 'one']

         >>> h1 = Histogram(5, 0., 1., data=dataset)
	 >>> h1, h1.entries
	 (<Histogram 5 0 1 at 0x7f01180f7248>, 1000000)
	 >>> print h1
	 bin                            value
	 ========================================
	 underflow                      1
	 [0, 0.2)                       1370
	 [0.2, 0.4)                     157651
	 [0.4, 0.6)                     682115
	 [0.6, 0.8)                     157467
	 [0.8, 1)                       1395
	 overflow                       1

	 >>> h2 = HistogramNonUniform(bins=[(0., 0.5), (0.5, 0.75), (0.75, 0.875),
         ...                                (0.875, 0.9375), (0.9375, 0.96875)],
         ...                          data=dataset)
	 >>> h2, h2.entries
	 (<HistogramNonUniform 5 at 0x1712248>, 1000000)
	 >>> print h2
	 bin                            value
	 ========================================
	 underflow                      1
	 [0, 0.5)                       500298
	 [0.5, 0.75)                    493439
	 [0.75, 0.875)                  6177
	 [0.875, 0.9375)                75
	 [0.9375, 0.96875)              4
	 overflow                       6

         >>> h3 = HistogramCategorical(bins=["one", "two", "three", "four", "five"],
         ...                           data=dataset2)
	 >>> h3, h3.entries
	 (<HistogramCategorical 5 at 0x1715e18>, 10000)
	 >>> print h3
	 bin                            value
	 ========================================
	 "one"                          1678
	 "two"                          1666
	 "three"                        1593
	 "four"                         1742
	 "five"                         1625
	 inflow                         1696

.. container::

      Examples with unbinned-data storage.

      ::

         >>> from cassius import *
         >>> import random

	 >>> h = Histogram(100, 0., 1.,
         ...               data=[random.gauss(0.5, 0.1) for i in xrange(10000)],
         ...               storelimit=None)
         ...
         >>> view(h)   # 1

         >>> h.reshape(100, 0., 0.5)
         >>> view(h)   # 2

         >>> h.reshape(5, 0., 1.)
         >>> view(h)   # 3

         >>> h.reshape(1000, 0., 1.)
         >>> view(h)   # 4

         >>> h.optimize(ranges=calcrange)
         >>> view(h)   # 5

         >>> h.optimize(ranges=calcrange_quartile)
         >>> view(h)   # 6

         >>> # from bins       # from unbinned data
	 >>> h.mean(),         mean(h.store())
	 (0.50066400000000011, 0.50067976294653072)
	 >>> h.stdev(),        stdev(h.store())
	 (0.10005638526362588, 0.10007538386851399)

      .. image::
         PLOTS/Histogram_example3.png

.. container::

      Example of weighted data.

      ::

          >>> from cassius import *
          >>> import random

	  >>> hnormal = Histogram(100, 0., 1., fillcolor="lightgrey")
	  >>> hweighted = Histogram(100, 0., 1., linecolor="blue")

	  >>> for i in xrange(10000):
	  ...     x = random.gauss(0.5, 0.1)
	  ...     if x < 0.5:
	  ...         weight = 0.2
	  ...     else:
	  ...         weight = 1.3
	  ...     hnormal.fill(x)
	  ...     hweighted.fill(x, weight)
	  ... 
	  >>> view(Overlay(hnormal, hweighted, frame=1))

      .. image::
          PLOTS/Histogram_example4.png

.. container::

      Example of the `gap` parameter for graphical rendering.

      ::

          >>> from cassius import *
          >>> h = Histogram(10, 0., 1., fillcolor="lightblue")
          >>> h.values = [1., 2., 3., 4., 5., 5., 4., 3., 2., 1.]
          >>> view(h)
          >>> h.gap = 0.2
          >>> view(h)

      .. image::
          PLOTS/Histogram_example5.png

      Categorical histograms have a non-zero gap by default, making
      them look more like bar charts.

Histogram: 1-D distribution with uniform binning
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

This is the basic histogram class that would be used most often for
numerical data.  The constructor creates a list of bin intervals from
the `numbins`, `low`, `high` arguments, but this list should be
treated as read-only.  Histogram-filling uses `numbins`, `low`, and
`high`, to add an entry in constant time, rather than walking down the
list of bin intervals.

.. autoclass:: Histogram
    :members: fill, low, high, index, mean, rms, stdev, reshape, optimize, refill, center, centers, centroid, centroids, support, ranges, store, weights, clearbins, clearstore

.. todo::
   * adding, subtracting histograms has not been implemented

.. autofunction:: histogramInteger

.. container::

   ::

      >>> from cassius import *
      >>> histogramInteger(0, 12, fillcolor="purple")
      <Histogram 13 -0.5 12.5 at 0x2e13320>
      >>> histogramInteger(1, 12, fillcolor="purple")
      <Histogram 12 0.5 12.5 at 0x2e13248>

The `TimeHist` subclass behaves exactly like a `Histogram`, except
that it provides additional methods for converting time strings into a
number of seconds (`informat`) and plots on a temporal axis
(`outformat`).

.. autoclass:: TimeHist
    :members: fill, fromtimestring, totimestring, timeticks

HistogramNonUniform: user-defined binning
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

This class is special cases in which bins are not uniformly spaced (or
need not be uniformly spaced).  Note that histogram-filling is slower
than it is in the uniform-bin case.  In addition to "underflow" and
"overflow" (data that fall outside the range of bins),
`HistogramNonUniform` also have "inflow" for data that fall *between*
bins.  Bins do not need to fully cover an interval, but they must not
overlap.

.. autoclass:: HistogramNonUniform
    :members: fill, low, high, index, mean, rms, stdev, reshape, center, centers, centroid, centroids, support, ranges, store, weights, clearbins, clearstore, refill

HistogramCategorical: bar charts and pie charts
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

This class is for non-numerical data.  The `bins` are a list of strings
and the `fill` method takes strings.  Any string that matches one of
the known categories increments that category's counter; any string
that does not match is added to `inflow` (the categorical equivalent
of overflow and underflow).  A categorical histogram represents data
that would be expressed in a bar chart or a pie chart in other
plotting toolkits.

.. todo::
   Add graphical modes for pie charts.

.. autoclass:: HistogramCategorical
    :members: fill, top, binedges, low, high, index, binorder, support, ranges, store, weights, clearbins, clearstore, refill

