.. automodule:: cassius.mathtools

Mathematical tools
------------------

The ``mathtools`` subpackage contains a set of convenience
functions that do some level of mathematical computation.  The
convenience functions that are more structural are in the
`<utilities reference_utilities>`_ subpackage.

Special numbers
^^^^^^^^^^^^^^^

.. autodata:: epsilon

.. autodata:: Infinity

.. container::

   In this example, an infinite ray has a slope of 5 because it goes
   from (0, 0) to (infinity, infinity * 5).

   ::
 
      >>> from cassius import *
      >>> view(Line(0., 0., Infinity, Infinity * 5., \
      ...      xmin=0., ymin=0., xmax=10., ymax=10.))

   .. image:: PLOTS/mathtools_Infinity.png

Rounding numbers
^^^^^^^^^^^^^^^^

Plot annotations often include numerical summaries of the data, which
should be rounded to a specified number of significant figures for
legibility.  Some of these functions return rounded numbers (or value,
error pairs) while others return strings.  Strings have the advantage
that zero-padding can be guaranteed.

.. autofunction:: str_round
.. autofunction:: round_sigfigs
.. autofunction:: str_sigfigs
.. autofunction:: round_errpair
.. autofunction:: str_errpair
.. autofunction:: unicode_errpair

.. container::

   In this example, −pi is rounded with a measurement uncertainty of
   0.00012345 (in most contexts, only one or two digits of an
   uncertainty are taken to be significant).  Return the result as a
   number pair, a string, or a unicode string.

   ::

      >>> from cassius import *
      >>> from math import pi

      >>> round_errpair(-pi, 0.00012345)
      (-3.1415899999999999, 0.00012)

      >>> "%s +- %s" % str_errpair(-pi, 0.00012345)
      '-3.14159 +- 0.00012'

      >>> unicode_errpair(-pi, 0.00012345)
      u'\u22123.14159\xb10.00012'
      >>> print unicode_errpair(-pi, 0.00012345)
      −3.14159±0.00012
      
Summarizing data
^^^^^^^^^^^^^^^^

Plot annotations often include numerical summaries of the data, such
as the mean, root-mean-square, and standard deviation.  The following
functions perform these calculations with optional rounding services.

.. container::

   Return the mean of a random distribution with the estimated error
   in cannonical significant figures.

   >>> from cassius import *
   >>> from random import gauss
   >>> from math import sqrt

   >>> values = [gauss(0.5, 0.1) for i in xrange(100)]
   >>> print unicode_errpair(mean(values), stdev(values)/sqrt(100))
   0.4959±0.0085

**Functions for continuous data:**

.. autofunction:: mean
.. autofunction:: wmean
.. autofunction:: linearfit
.. autofunction:: rms
.. autofunction:: stdev
.. autofunction:: covariance
.. autofunction:: correlation

**Functions for categorical data:**

.. autofunction:: ubiquitous

Missing math functions
^^^^^^^^^^^^^^^^^^^^^^

Before Python 2.7, erf was missing from ``python.math`` (because it is
based on an old C library).  The following functions provide the
missing functionality to Python 2.6 users.  (It is an efficient,
pure-Python implementation with errors less than 1.5e-7 for all
inputs.)

.. autofunction:: erf
.. autofunction:: erfc

Likelihood functions for regression
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

In regression (curve fitting), one maximizes a likelihood of a
functional shape to a distribution.  The most common one-dimensional
cases are Gaussian likelihood (chi-square fitting) and Poisson
likelihood (histogram fitting with small samples).

The following functions are normalized in the same way, so that
one can be easily be swapped for another in a minimization package.  With
this normalization, one standard deviation of error (68% confidence
level) corresponds to a displacement from the minimum such that the
likelihood increases by 1.0.

.. autofunction:: gaussian_likelihood
.. autofunction:: poisson_likelihood

Principal components analysis (PCA)
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. autofunction:: principleComponents
