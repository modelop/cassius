Percolation of frame arguments
==============================

Plotting toolkits are complicated because many things need to be
parameterized, to give users the flexibility to produce nice graphics
at the end of a study, but most parameters should be hidden until
needed, to let the user concentrate on the analysis task at the
beginning of a study.  The usual solution is to put most options in a
global scope, and let the user modify them when he or she is ready.

Instead of requiring dependence on a global state, Cassius
associates plotting parameters with all plotable objects.  That is, if
histogram1 needs wider margins than histogram2, one can set

::

   >>> histogram1.leftmargin = 0.2
   >>> histogram2.leftmargin = 0.1

and the correct margin will be used whenever `view(histogram1)` or
`view(histogram2)` is called--- it does not need to be manually set
before plotting.  Every plotable object keeps track of container
arguments, such as `bins`, `values`, and `fillcolor` for histograms,
as well as coordinate frame arguments, such as `leftmargin`, `xlabel`,
and `ymax`.

It is natural to associate container arguments with the container, but
associating the coordinate frame arguments with a container raises
two issues.

   * Sometimes we want to set coordinate frame arguments once in a
     session for all plotable objects, so that we don't have to re-set
     them every time we create a new object.  For this reason, objects
     are not *required* to contain frame arguments.  If
     `histogram1.leftmargin` is not defined, then a `leftmargin` will
     be taken from `cassius.svgview.default_frameargs` (a dictionary).
     So, technically, Cassius does have a global state, but it is
     optional.

   * Sometimes we want to set frame arguments for one `view` or `draw`
     invocation, without permanently changing the plotable object.
     For this reason, optional frame arguments passed to the `view`
     and `draw` commands override the frame arguments associated with
     the objects.

With optional frame arguments bound to the plotable objects and
optional frame arguments passed to `view` and `draw`, as well as the
fallback values in `default_frameargs`, a single argument can be
multiply defined.  Which argument should Cassius use?  Frame arguments
have the following priority::

   >>> from cassius import *
   >>> import cassius.svgview

   >>> cassius.svgview.default_frameargs["framearg"] = third_priority

   >>> plot = PlotType(..., framearg = second_priority)

   >>> view(plot, framearg = first_priority)

Arguments passed to `view` and `draw` are the highest priority, but
are the most transient, while values defined in `default_frameargs`
are the lowest priority, but are guaranteed to exist and are rarely
changed.  This scheme may sound complicated, but it feels natural in
practice.

A list of all frame arguments and their meanings can be found `here
<reference_svgdraw>`_.

Frame arguments with Layout, Overlay, and Stack
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

The fact that plots can be grouped and overlaid adds an additional
layer of complexity.  Nested plots can define aspects of the
coordinate frame, but there can be arbitrarily many such plots in a
layout or overlay.  Which should Cassius use?

   * The `Layout` class creates an N-by-M grid of coordinate frames.
     Within each of the coordinate frames, the normal rules apply.
   * The `Overlay` class creates one coordinate frame with multiple
     objects in it.  This class has two modes.
        * Specified frame: the user points to one of the contained
          objects with a `frame=INDEX` argument.  The object at index
          `INDEX` defines the frame.  (Python indexing rules apply:
          `frame=0` is the first object and `frame=-1` is the last
          object.)
        * Union frame: the `Overlay` object itself defines a frame
          large enough to show all of its contents.
   * The `Stack` class overlays a set of cumulative histograms.
     The histogram on the top of the stack defines all frame
     arguments.

Page arguments: setting the aspect ratio
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Arguments defining properties of the page, such as the width and
height, and therefore the aspect ratio, can only be passed to `view`
or `draw` directly::

   >>> view(histogram1, width=1000, height=500)
   >>> draw(histogram1, width=1000, height=500, fileName="myplot.svg")

System-wide defaults can be set once per session with

::

   >>> import cassius.svgdraw
   >>> cassius.svgdraw.defaults["height"] = 500

The `fileName` parameter has no default value and must be specified
in every `draw` or `drawpdf` call.
