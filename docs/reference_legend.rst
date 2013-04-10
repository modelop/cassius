.. automodule:: cassius.containers

Legends to annotate plots
-------------------------

A legend is a collection of annotations at one of the four corners of
the coordinate frame.  It is used to associate plot elements with
names or explanations by style.  The text is completely
user-specified: it can include whatever information is needed to
communicate to the intended audience.

.. container::

   Here is a basic example of three plot elements and a legend.  The
   `Legend.fields` is a user-specified table in which plot objects are
   represented by a marker, a filled rectangle, and/or a line to
   indicate which style the reader of the plot should look for.  In
   this example, we also provide the histogram mean.

   ::

      >>> from cassius import *
      >>> import random

      >>> dataset = Scatter(x=[random.uniform(0., 1.) for i in xrange(100)],
      ...                   y=[random.uniform(0., 500.) for i in xrange(100)])
      ... 
      >>> curve = Curve("200. + 100.*sin(2.*pi*x)", linecolor="red")
      >>> histogram = Histogram(100, 0., 1.,
      ...                       data=[random.gauss(0.5, 0.1) for i in xrange(10000)],
      ...                       fillcolor="lightblue")
      ... 
      >>> legend = Legend([[dataset, "dataset"],
      ...                  [histogram, "histogram", str_sigfigs(histogram.mean(), 3)],
      ...                  [curve, "curve"]],
      ...                 justify="clr", width=0.45)
      >>> view(Overlay(dataset, histogram, curve, legend))

   .. image::
      PLOTS/Legend_example1.png

   (Snowglobe!)

.. autoclass:: Legend
   :members: dimensions

A `Style` object can be used as a drop-in replacement for a plot
element in a `Legend.fields` table to produce the graphic without
necessarily having a real plot element.

.. container::

   The same kind of legend as above, but this time without any plots.

   ::

      >>> from cassius import *
      >>> legend = Legend([[Style(marker="circle"), "dataset"],
      ...                  [Style(linecolor="black", fillcolor="lightblue"), "histogram"],
      ...                  [Style(linecolor="red"), "curve"]],
      ...                 justify="cl")
      >>> view(legend)

   .. image::
      PLOTS/Legend_example2.png

.. autoclass:: Style
