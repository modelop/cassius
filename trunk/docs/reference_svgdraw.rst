.. automodule:: cassius.svgdraw

SVG backend: drawing static pictures of plots
---------------------------------------------

.. autofunction:: view

.. autofunction:: draw

.. autofunction:: drawpdf

.. autodata:: defaults

==================== =============== ================= =====================================
Argument             Type            Default           Meaning
==================== =============== ================= =====================================
width                int             1000              Width of the image in SVG units.
height               int             1000              Height of the image in SVG units.
background           bool            True              Fill the background with uniform
                                                       white (as opposed to transparency)
==================== =============== ================= =====================================

.. autodata:: default_frameargs

==================== =============== ================= =====================================
Argument             Type            Default           Meaning
==================== =============== ================= =====================================
leftmargin           float           0.12              Distance between the left edge of the
                                                       image and the left edge of the
                                                       coordinate frame in SVG units
rightmargin          float           0.05              Same for right edges
topmargin            float           0.05              Same for top edges
bottommargin         float           0.08              Same for bottom edges
textscale            float           1.                Scale factor for all text (2. would
                                                       double all text)
xlabel               str or None     None              Label for the x (bottom) axis
ylabel               str or None     None              Label for the y (left) axis
rightlabel           str or None     None              Label for the right axis
toplabel             str or None     None              Label for the top axis
xlabeloffset         float           0.08              Vertical displacement between the
                                                       bottom edge of the coordinate frame
                                                       and the middle of the xlabel text
                                                       in SVG units (down is positive)
ylabeloffset         float           -0.10	       Horizontal displacement between the
                                                       left edge of the coordinate frame
                                                       and the middle of the ylabel text
                                                       in SVG units (right is positive)
rightlabeloffset     float           0.                Same for rightlabel
toplabeloffset       float           0.                Same for toplabel
xlog                 bool            False	       If True, draw a logarithmic x axis
                                                       (implemented but untested)
ylog                 bool            False	       If True, draw a logarithmic y axis
                                                       (implemented but untested)
xticks               dict or Auto    Auto              Specification for x (bottom) axis
                                                       tick-marks (see `utilities <reference_utilities#specifying-grids-and-tick-marks>`_)
yticks               dict or Auto    Auto              Specification for y (left) axis
                                                       tick-marks
rightticks           dict or Auto    Auto              Same for right axis tick-marks
                                                       (Auto copies y axis, without the
                                                       labels)
topticks             dict or Auto    Auto              Same for top axis tick-marks
                                                       (Auto copies x axis, without the
                                                       labels)
show_topticklabels   bool or Auto    Auto              If True, copy the labels as well
show_rightticklabels bool or Auto    Auto              If True, copy the labels as well
xmin                 float or Auto   Auto              X-minimum (left) edge of the
                                                       coordinate frame in data units
ymin                 float or Auto   Auto              Y-minimum (bottom) edge of the
                                                       coordinate frame in data units
xmax                 float or Auto   Auto              X-maximum (right) edge of the
                                                       coordinate frame in data units
ymax                 float or Auto   Auto              Y-maximum (top) edge of the
                                                       coordinate frame in data units
xmargin              float           0.1               Fractional padding for coordinate
                                                       frame around data: if a dataset
                                                       covers (-1, +1), xmargin=0.1 makes
                                                       the coordinate frame cover
                                                       (-1.1, +1.1)
ymargin              float           0.1               Same for y
==================== =============== ================= =====================================
