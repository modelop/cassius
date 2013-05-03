__version__ = "0.1.0.3"
_CASSIUS_VER = __version__

# The `if True` is needed because this file must be both functional
# and act as auto-generated documentation.  reStructuredText needs
# everything after the double-colon to be indented, and Python is only
# okay with that if it's inside of a code block.

if True: #STARTDOCUMENTATION::

    from mathtools import Infinity, MinusInfinity, epsilon
    from mathtools import str_round, round_sigfigs, str_sigfigs, round_errpair, str_errpair, unicode_errpair
    from mathtools import mean, wmean, linearfit, rms, stdev, covariance, correlation, ubiquitous
    from mathtools import erf, erfc
    from mathtools import gaussian_likelihood, poisson_likelihood
    from mathtools import principleComponents

    from utilities import unicode_number
    from utilities import regular, tickmarks
    from utilities import calcrange, calcrange_quartile
    from utilities import binning
    from utilities import timesec, fromtimestring, totimestring, timeticks
    from utilities import SECOND, MINUTE, HOUR, DAY, WEEK, MONTH, YEAR

    from color import RGB, HLS, HSV
    from color import truncated_shift, asymptotic_shift
    from color import lighten, darken, gradient
    from color import colors, gradients, darkseries, lightseries

    from containers import Auto
    from containers import Layout, Overlay, Stack
    from containers import Histogram, histogramInteger, TimeHist, HistogramNonUniform, HistogramCategorical
    from containers import Scatter, TimeSeries
    from containers import ColorField
    from containers import Region, MoveTo, EdgeTo, ClosePolygon, RegionMap
    from containers import Curve
    from containers import Line, Grid
    from containers import Legend, Style
    from containers import histogram

    from svgdraw import view, draw, drawpdf

#ENDDOCUMENTATION
