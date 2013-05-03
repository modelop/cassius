.. automodule:: cassius.containers

Mathematical curves
-------------------

The ability to draw mathematical expressions as curves is useful on
its own, but it is especially useful as an overlay on or a fit to
data.

.. container::

   It should be as easy as possible to just get a mathematical
   expression onto the screen.

   ::

      >>> from cassius import *
      >>> view(Curve("10.*x**3 - 10.*x**2 + x"))

   .. image::
      PLOTS/Curve_example1.png

.. container::

   By default, the endpoints of the curve are determined by the
   coordinate frame.  For instance, if another plot object (random
   scatter points in this example) sets the window boundary to (-5,
   5), then curves are drawn over the same interval.  Explicit
   endpoints can be set with `xmin` and `xmax`.

   ::

      >>> from cassius import *
      >>> import random
      >>> dataset = Scatter(x=[random.uniform(-5., 5.) for i in xrange(20)],
      ...                   y=[random.uniform(-5., 5.) for i in xrange(20)])

      >>> view(Overlay(dataset, Curve("sin(x)")))

   .. image::
      PLOTS/Curve_example2.png

.. container::

   The expression between the quotation marks is a Python expression,
   converted by `Curve` into an executable function.  A precompiled or
   user-defined function could be used instead.

   ::

      >>> from cassius import *
      >>> import math

      >>> def squarewave(x):
      ...     if int(math.floor(x)) % 2 == 0:
      ...         return -0.5
      ...     else:
      ...         return +0.5
      ... 

      >>> view(Overlay(Curve("sin(x)"), Curve(math.cos), Curve(squarewave),
      ...      xmin=0., xmax=6.28, ymin=-2., ymax=2.))

   .. image::
      PLOTS/Curve_example3.png

.. container::

   The way an expression string is interpreted is highly configurable.

   ::

      >>> from cassius import *
      >>> view(Curve("t*exp(t * (0+1j))", varmin=0., varmax=10.,
      ...            var="t", form=Curve.COMPLEX))

   .. image::
      PLOTS/Curve_example4.png

   ::

      >>> from cassius import *
      >>> import scipy.special # (sudo apt-get install python-scipy)
      >>> curve = Curve("jn(4, x)", namespace=scipy.special)
      >>> view(curve, xmin=-20., xmax=20.)

   .. image::
      PLOTS/Curve_example5.png

.. container::

   Curves are one-dimensional in the sense that only one input
   parameter is varied to produce a plot.  However, the function
   string can depend on additional parameters, specified once per
   drawing.

   ::

      >>> from cassius import *
      >>> curve = Curve("a + b*x")
      >>> view(curve)  # causes an error because a and b are not defined

      >>> curve.parameters = {"a": 1., "b": 5.}
      >>> first = curve.scatter(0., 2.)

      >>> curve.parameters = {"a": 5., "b": 1.}
      >>> second = curve.scatter(0., 2.)

      >>> view(Overlay(first, second))

   .. image::
      PLOTS/Curve_example6.png

.. todo::
   The `Curve` class was also defined for curve-fitting, in which
   `parameters` are the fit parameters.  This was designed around
   Minuit and the PyMinuit library, but that's too awkward of a
   dependency.  The code works, but it has been turned off to avoid
   causing installation failures.  This feature should be modified to
   use SciPy instead (a more reasonable dependency, as we already
   require NumPy).

.. autoclass:: Curve
   :members: __call__, derivative, scatter, ranges, objective, fit, round_errpair, str_errpair, unicode_errpair, expr
