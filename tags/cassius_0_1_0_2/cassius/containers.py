# Standard Python packages
import math, cmath
import re
import itertools
import numbers
import random

# Special dependencies
import numpy, numpy.random # sudo apt-get install python-numpy
# import minuit # no package

# Augustus dependencies
from augustus.kernel.unitable import UniTable

# Cassius interdependencies
import mathtools
import utilities
import color
import containers

class ContainerException(Exception):
    """Run-time errors in container objects."""
    pass

class AutoType:
    def __repr__(self):
        if self is Auto:
            return "Auto"
        else:
            raise ContainerException, "There must only be one instance of Auto"

    def __copy__(self):
        return self

    def __deepcopy__(self, memo):
        return self

#: Symbol indicating that a frame argument should be
#: automatically-generated, if possible.  Similar to `None` in that
#: there is only one instance (checked with `is`), but with a different
#: meaning.
#:
#: Example:
#:    `xticks = None` means that no x-ticks are drawn
#: 
#:    `xticks = Auto` means that x-ticks are automatically generated
#:
#: `Auto` is the only instance of `AutoType`.
Auto = AutoType()

######################################################### Layout of the page, coordinate frames, overlays

# for arranging a grid of plots
class Layout:
    """Represents a regular grid of plots.

    Signatures::

       Layout(nrows, ncols, plot1[, plot2[, ...]])
       Layout(plot1[, plot2[, ...]], nrows=value, ncols=value)

    Arguments:
       nrows (number): number of rows

       ncols (number): number of columns

       plots (list of `Frame` or other `Layout` objects): plots to
       draw, organized in normal reading order (left to right, columns
       before rows)
       
    Public Members:
       `nrows`, `ncols`, `plots`

    Behavior:
       It is possible to create an empty Layout (no plots).

       For a Layout object named `layout`, `layout[i,j]` accesses a
       plot in row `i` and column `j`, while `layout.plots[k]`
       accesses a plot by a serial index (`layout.plots` is a normal
       list).

       Spaces containing `None` will be blank.

       Layouts can be nested: e.g. `Layout(1, 2, top, Layout(2, 1,
       bottomleft, bottomright))`.
       """

    def __init__(self, *args, **kwds):
        if "nrows" in kwds and "ncols" in kwds:
            self.nrows, self.ncols = kwds["nrows"], kwds["ncols"]
            self.plots = list(args)
            if set(kwds.keys()) != set(["nrows", "ncols"]):
                raise TypeError, "Unrecognized keyword argument"

        elif len(args) >= 2 and isinstance(args[0], (numbers.Number, numpy.number)) and isinstance(args[1], (numbers.Number, numpy.number)):
            self.nrows, self.ncols = args[0:2]
            self.plots = list(args[2:])
            if set(kwds.keys()) != set([]):
                raise TypeError, "Unrecognized keyword argument"
        else:
            raise TypeError, "Missing nrows or ncols argument"
        
    def index(self, i, j):
        """Convert a grid index (i,j) into a serial index."""
        if i < 0 or j < 0 or i >= self.nrows or j >= self.ncols:
            raise ContainerException, "Index (%d,%d) is beyond the %dx%d grid of plots" % (i, j, self.nrows, self.ncols)
        return self.ncols*i + j

    def __getitem__(self, ij):
        i, j = ij
        index = self.index(i, j)
        if index < len(self.plots):
            return self.plots[index]
        else:
            return None

    def __setitem__(self, ij, value):
        i, j = ij
        index = self.index(i, j)
        if index < len(self.plots):
            self.plots[index] = value
        else:
            for k in range(len(self.plots), index):
                self.plots.append(None)
            self.plots.append(value)
            
    def __delitem__(self, ij):
        i, j = ij
        if self.index(i, j) < len(self.plots):
            self.plots[self.index(i, j)] = None

    def __repr__(self):
        return "<Layout %dx%d at 0x%x>" % (self.nrows, self.ncols, id(self))

# for representing a coordinate axis
class Frame:
    """Abstract superclass for all plots with drawable coordinate frames.

    Frame arguments:
       Any frame argument (axis labels, margins, etc.) can be passed
       as a keyword in the constructor or later as member data.  The
       frame arguments are interpreted only by the backend and are
       replaced with defaults if not present.

    Public Members:
       All frame arguments that have been set.
    """

    _not_frameargs = []

    def __init__(self, **frameargs):
        self.__dict__.update(frameargs)

    def __repr__(self):
        return "<Frame %s at 0x%x>" % (str(self._frameargs()), id(self))

    def _frameargs(self):
        output = dict(self.__dict__)
        for i in self._not_frameargs:
            if i in output: del output[i]
        for i in output.keys():
            if i[0] == "_": del output[i]
        return output

    def ranges(self, xlog=False, ylog=False):
        """Return a data-space bounding box as `xmin, ymin, xmax, ymax`.

        Arguments:
           xlog (bool): requesting a logarithmic x axis (negative
           and zero-valued contents are ignored)

           ylog (bool): requesting a logarithmic y axis

        The abstract class, `Frame`, returns constant intervals (0, 1)
        (or (0.1, 1) for log scales.)
        """

        if xlog:
            xmin, xmax = 0.1, 1.
        else:
            xmin, xmax = 0., 1.
        if ylog:
            ymin, ymax = 0.1, 1.
        else:
            ymin, ymax = 0., 1.
        return xmin, ymin, xmax, ymax

    def _prepare(self, xmin=None, ymin=None, xmax=None, ymax=None, xlog=None, ylog=None): pass  # get ready to be drawn

# for overlaying different containers' data in a single frame
class Overlay(Frame):
    """Represents an overlay of several plots in the same coordinate axis.

    Signatures::

       Overlay(frame, plot1[, plot2[, ...]], [framearg=value[, ...]])
       Overlay(plot1[, plot2[, ...]], [frame=value[, framearg=value[, ...]]])

    Arguments:
       plots (`Frame` instances): plots to be overlaid

       frame (index or `None`): which, if any, plot to use to set the
       coordinate frame.  If `frame=None`, then `frameargs` will be
       taken from the `Overlay` instance and a data-space bounding box
       will be derived from the union of all contents.

    Public Members:
       `plots`, `frame`

    Behavior:
       It is *not* possible to create an empty Overlay (no plots).
    """

    _not_frameargs = ["plots", "frame"]

    def __init__(self, first, *others, **frameargs):
        if isinstance(first, (int, long)):
            self.frame = first
            self.plots = list(others)
        else:
            self.plots = [first] + list(others)
        Frame.__init__(self, **frameargs)

    def append(self, plot):
        """Append a plot to the end of `plots` (drawn last), keeping the `frame` pointer up-to-date."""

        self.plots.append(plot)
        if getattr(self, "frame", None) is not None and self.frame < 0:
            self.frame -= 1

    def prepend(self, plot):
        """Prepend a plot at the beginning of `plots` (drawn first), keeping the `frame` pointer up-to-date."""

        self.plots.insert(0, plot)
        if getattr(self, "frame", None) is not None and self.frame >= 0:
            self.frame += 1

    def __repr__(self):
        if getattr(self, "frame", None) is not None:
            return "<Overlay %d items (frame=%d) at 0x%x>" % (len(self.plots), self.frame, id(self))
        else:
            return "<Overlay %d items at 0x%x>" % (len(self.plots), id(self))

    def _frameargs(self):
        if getattr(self, "frame", None) is not None:
            if self.frame >= len(self.plots):
                raise ContainerException, "Overlay.frame points to a non-existent plot (%d <= %d)" % (self.frame, len(self.plots))
            output = dict(self.plots[self.frame].__dict__)
            output.update(self.__dict__)
        else:
            output = dict(self.__dict__)

        for i in self._not_frameargs:
            if i in output: del output[i]
        for i in output.keys():
            if i[0] == "_": del output[i]
        return output

    def ranges(self, xlog=False, ylog=False):
        """Return a data-space bounding box of all contents as `xmin, ymin, xmax, ymax`.

        Arguments:
           xlog (bool): requesting a logarithmic x axis (negative
           and zero-valued contents are ignored)

           ylog (bool): requesting a logarithmic y axis
        """

        if getattr(self, "frame", None) is not None:
            if self.frame >= len(self.plots):
                raise ContainerException, "Overlay.frame points to a non-existent plot (%d <= %d)" % (self.frame, len(self.plots))
            return self.plots[self.frame].ranges(xlog, ylog)

        xmins, ymins, xmaxs, ymaxs = [], [], [], []
        for plot in self.plots:
            xmin, ymin, xmax, ymax = plot.ranges(xlog, ylog)
            xmins.append(xmin)
            ymins.append(ymin)
            xmaxs.append(xmax)
            ymaxs.append(ymax)
        return min(xmins), min(ymins), max(xmaxs), max(ymaxs)
            
######################################################### Histograms, bar charts, pie charts

class Stack(Frame):
    """Represents a stack of histograms.

    Signature::

       Stack(plot1[, plot2[, ...]] [linewidths=list,] [linestyles=list,] [linecolors=list,] [**frameargs])

    Arguments:
       plots (list of `HistogramAbstract` instances): histograms to be stacked

       linewidths (list): list of linewidths with the same length as
       the number of histograms

       linestyles (list): list of styles

       linecolors (list): list of colors

       fillcolors (list): list of fill colors (most commonly used to
       distinguish between stacked histograms

    Public members:
       `plots`, `linewidths`, `linestyles`, `linecolors`, `fillcolors`

    Behavior:
       It is *not* possible to create an empty Stack (no plots).

       If `linewidths`, `linestyles`, `linecolors`, or `fillcolors`
       are not specified, the input histograms' own styles will be
       used.
"""

    _not_frameargs = ["plots", "linewidths", "linestyles", "linecolors", "fillcolors"]

    def __init__(self, first, *others, **frameargs):
        self.plots = [first] + list(others)
        Frame.__init__(self, **frameargs)

    def __repr__(self):
        return "<Stack %d at 0x%x>" % (len(self.plots), id(self))

    def bins(self):
        """Returns a list of histogram (low, high) bin edges.

        Exceptions:
           Raises `ContainerException` if any of the histogram bins
           differ (ignoring small numerical errors).
        """

        bins = None
        for hold in self.plots:
            if bins is None:
                bins = hold.bins[:]
            else:
                same = (len(hold.bins) == len(bins))
                if same:
                    for oldbin, refbin in zip(hold.bins, bins):
                        if HistogramAbstract._numeric(hold, oldbin) and HistogramAbstract._numeric(hold, refbin):
                            xepsilon = mathtools.epsilon * abs(refbin[1] - refbin[0])
                            if abs(oldbin[0] - refbin[0]) > xepsilon or abs(oldbin[1] - refbin[1]) > xepsilon:
                                same = False
                                break
                        else:
                            if oldbin != refbin:
                                same = False
                                break

                if not same:
                    raise ContainerException, "Bins in stacked histograms must be the same"
        return bins

    def stack(self):
        """Returns a list of new histograms, obtained by stacking the inputs.

        Exceptions:
           Raises `ContainerException` if any of the histogram bins
           differ (ignoring small numerical errors).
        """

        if len(self.plots) == 0:
            raise ContainerException, "Stack must contain at least one histogram"

        for styles in "linewidths", "linestyles", "linecolors", "fillcolors":
            if getattr(self, styles, None) is not None:
                if len(getattr(self, styles)) != len(self.plots):
                    raise ContainerException, "There must be as many %s as plots" % styles

        bins = self.bins()
        gap = max([i.gap for i in self.plots])
        output = []
        for i in xrange(len(self.plots)):
            if getattr(self, "linewidths", None) is not None:
                linewidth = self.linewidths[i]
            else:
                linewidth = self.plots[i].linewidth

            if getattr(self, "linestyles", None) is not None:
                linestyle = self.linestyles[i]
            else:
                linestyle = self.plots[i].linestyle

            if getattr(self, "linecolors", None) is not None:
                linecolor = self.linecolors[i]
            else:
                linecolor = self.plots[i].linecolor

            if getattr(self, "fillcolors", None) is not None:
                fillcolor = self.fillcolors[i]
            else:
                fillcolor = self.plots[i].fillcolor

            if isinstance(self.plots[i], HistogramCategorical):
                hnew = HistogramCategorical(bins, None, None, 0, linewidth, linestyle, linecolor, fillcolor, gap)
            else:
                hnew = HistogramAbstract(bins, 0, linewidth, linestyle, linecolor, fillcolor, gap)

            for j in xrange(i+1):
                for bin in xrange(len(hnew.values)):
                    hnew.values[bin] += self.plots[j].values[bin]

            output.append(hnew)
        return output

    def overlay(self):
        self._stack = self.stack()
        self._stack.reverse()
        self._overlay = Overlay(*self._stack, frame=0)
        self._overlay.plots[0].__dict__.update(self._frameargs())
        return self._overlay

    def ranges(self, xlog=False, ylog=False):
        """Return a data-space bounding box of all contents as `xmin, ymin, xmax, ymax`.

        Arguments:
           xlog (bool): requesting a logarithmic x axis (negative
           and zero-valued contents are ignored)

           ylog (bool): requesting a logarithmic y axis
        """

        self.overlay()

        if ylog:
            ymin = min(filter(lambda y: y > 0., self._stack[-1].values))
            ymax = max(filter(lambda y: y > 0., self._stack[0].values))
        else:
            ymin = min(list(self._stack[-1].values) + [0.])
            ymax = max(self._stack[0].values)

        if ymin == ymax:
            if ylog:
                ymin, ymax = ymin / 2., ymax * 2.
            else:
                ymin, ymax = ymin - 0.5, ymax + 0.5

        return self.plots[0].low(), ymin, self.plots[0].high(), ymax
        
    def _prepare(self, xmin=None, ymin=None, xmax=None, ymax=None, xlog=None, ylog=None):
        self.overlay()

class HistogramAbstract(Frame):
    """Abstract class for histograms: use concrete classes (Histogram, HistogramNonUniform, and HistogramCategorical) instead."""

    _not_frameargs = ["bins", "storelimit", "entries", "linewidth", "linestyle", "linecolor", "fillcolor", "gap", "values", "underflow", "overflow", "inflow"]

    def __init__(self, bins, storelimit, linewidth, linestyle, linecolor, fillcolor, gap, **frameargs):
        self.bins, self.storelimit = bins, storelimit
        self.entries = 0
        self.linewidth, self.linestyle, self.linecolor, self.fillcolor, self.gap = linewidth, linestyle, linecolor, fillcolor, gap

        self.values = numpy.zeros(len(self.bins), numpy.float)
        self._sumx = numpy.zeros(len(self.bins), numpy.float)
        self.underflow, self.overflow, self.inflow = 0., 0., 0.

        if storelimit is None:
            self._store = []
            self._weights = []
            self._lenstore = None
        else:
            self._store = numpy.empty(storelimit, numpy.float)
            self._weights = numpy.empty(storelimit, numpy.float)
            self._lenstore = 0

        Frame.__init__(self, **frameargs)

    def __repr__(self):
        return "<HistogramAbstract at 0x%x>" % id(self)

    def _numeric(self, bin):
        return len(bin) == 2 and isinstance(bin[0], (numbers.Number, numpy.number)) and isinstance(bin[1], (numbers.Number, numpy.number))

    def __str__(self):
        output = []
        output.append("%-30s %s" % ("bin", "value"))
        output.append("="*40)
        if self.underflow > 0: output.append("%-30s %g" % ("underflow", self.underflow))
        for i in xrange(len(self.bins)):
            if self._numeric(self.bins[i]):
                category = "[%g, %g)" % self.bins[i]
            else:
                category = "\"%s\"" % self.bins[i]
            output.append("%-30s %g" % (category, self.values[i]))
        if self.overflow > 0: output.append("%-30s %g" % ("overflow", self.overflow))
        if self.inflow > 0: output.append("%-30s %g" % ("inflow", self.inflow))
        return "\n".join(output)

    def binedges(self):
        """Return numerical values for the the edges of bins."""

        categorical = False
        for bin in self.bins:
            if not self._numeric(bin):
                categorical = True
                break

        if categorical:
            lows = map(lambda x: x - 0.5, xrange(len(self.bins)))
            highs = map(lambda x: x + 0.5, xrange(len(self.bins)))
            return zip(lows, highs)

        else:
            return self.bins[:]
        
    def center(self, i):
        """Return the center (x value) of bin `i`."""

        if self._numeric(self.bins[i]):
            return (self.bins[i][0] + self.bins[i][1])/2.
        else:
            return self.bins[i]

    def centers(self):
        """Return the centers of all bins."""
        return [self.center(i) for i in range(len(self.bins))]

    def centroid(self, i):
        """Return the centroid (average data x value) of bin `i`."""

        if self.values[i] == 0.:
            return self.center(i)
        else:
            return self._sumx[i] / self.values[i]

    def centroids(self):
        """Return the centroids of all bins."""
        return [self.centroid(i) for i in range(len(self.bins))]

    def mean(self, decimals=Auto, sigfigs=Auto, string=False):
        """Calculate the mean of the distribution, using bin contents.

        Keyword arguments:
           decimals (int or `Auto`): number of digits after the decimal
           point to found the result, if not `Auto`

           sigfigs (int or `Auto`): number of significant digits to round
           the result, if not `Auto`

           string (bool): return output as a string (forces number of digits)
        """

        numer = 0.
        denom = 0.
        for bin, value in zip(self.bins, self.values):
            if self._numeric(bin):
                width = bin[1] - bin[0]
                center = (bin[0] + bin[1])/2.
            else:
                raise ContainerException, "The mean of a categorical histogram is not meaningful"

            numer += width * value * center
            denom += width * value

        output = numer/denom
        if decimals is not Auto:
            if string:
                return mathtools.str_round(output, decimals)
            else:
                return round(output, decimals)
        elif sigfigs is not Auto:
            if string:
                return mathtools.str_sigfigs(output, sigfigs)
            else:
                return mathtools.round_sigfigs(output, sigfigs)
        else:
            if string:
                return str(output)
            else:
                return output

    def rms(self, decimals=Auto, sigfigs=Auto, string=False):
        """Calculate the root-mean-square of the distribution, using bin contents.

        Keyword arguments:
           decimals (int or `Auto`): number of digits after the decimal
           point to found the result, if not `Auto`

           sigfigs (int or `Auto`): number of significant digits to round
           the result, if not `Auto`

           string (bool): return output as a string (forces number of digits)
        """

        numer = 0.
        denom = 0.
        for bin, value in zip(self.bins, self.values):
            if self._numeric(bin):
                width = bin[1] - bin[0]
                center = (bin[0] + bin[1])/2.
            else:
                raise ContainerException, "The RMS of a categorical histogram is not meaningful"

            numer += width * value * center**2
            denom += width * value

        output = math.sqrt(numer/denom)
        if decimals is not Auto:
            if string:
                return mathtools.str_round(output, decimals)
            else:
                return round(output, decimals)
        elif sigfigs is not Auto:
            if string:
                return mathtools.str_sigfigs(output, sigfigs)
            else:
                return mathtools.round_sigfigs(output, sigfigs)
        else:
            if string:
                return str(output)
            else:
                return output

    def stdev(self, unbiased=True, decimals=Auto, sigfigs=Auto, string=False):
        """Calculate the standard deviation of the distribution, using bin contents.

        Keyword arguments:
           unbiased (bool defaulting to True): return unbiased sample
           deviation, sqrt(sum(xi - mean)**2/(N - 1)), rather than the
           biased estimator, sqrt(sum(xi - mean)**2/ N )

           decimals (int or `Auto`): number of digits after the decimal
           point to found the result, if not `Auto`

           sigfigs (int or `Auto`): number of significant digits to round
           the result, if not `Auto`

           string (bool): return output as a string (forces number of digits)

        Note:
           To use an unbiased estimator, the "entries" member must be
           properly defined and greater than 1.
        """

        numer1 = 0.
        numer2 = 0.
        denom = 0.
        for bin, value in zip(self.bins, self.values):
            if self._numeric(bin):
                width = bin[1] - bin[0]
                center = (bin[0] + bin[1])/2.
            else:
                raise ContainerException, "The standard deviation of a categorical histogram is not meaningful"

            numer1 += width * value * center
            numer2 += width * value * center**2
            denom += width * value

        output = math.sqrt(numer2/denom - (numer1/denom)**2)
        if unbiased:
            if self.entries <= 1.:
                raise ValueError, "To use an unbiased standard deviation estimator, the \"entries\" member must be properly defined and greater than 1."
            output *= math.sqrt(self.entries / (self.entries - 1.))

        if decimals is not Auto:
            if string:
                return mathtools.str_round(output, decimals)
            else:
                return round(output, decimals)
        elif sigfigs is not Auto:
            if string:
                return mathtools.str_sigfigs(output, sigfigs)
            else:
                return mathtools.round_sigfigs(output, sigfigs)
        else:
            if string:
                return str(output)
            else:
                return output

    def store(self):
        """Return a _copy_ of the histogram's stored values (if any)."""

        if self._lenstore is None:
            return self._store[:]
        else:
            return self._store[0:self._lenstore]

    def weights(self):
        """Return a _copy_ of the histogram's stored weights (if any)."""

        if self._lenstore is None:
            return self._weights[:]
        else:
            return self._weights[0:self._lenstore]

    def clearbins(self):
        """Clear all bin values, including `underflow`, `overflow`, and `inflow`, and set `entries` to zero."""

        self.entries = 0
        self.values = numpy.zeros(len(self.bins), self.values.dtype)
        self._sumx = numpy.zeros(len(self.bins), self._sumx.dtype)
        self.underflow, self.overflow, self.inflow = 0., 0., 0.

    def clearstore(self):
        """Clear the histogram's stored values (if any)."""

        if self._lenstore is None:
            self._store = []
            self._weights = []
        else:
            self._lenstore = 0

    def refill(self):
        """Clear and refill all bin values using the stored values (if any)."""

        self.clearbins()
        self.fill(self._store, self._weights, self._lenstore, fillstore=False)

    def support(self):
        """Return the widest interval of bin values with non-zero contents."""

        all_numeric = True
        for bin in self.bins:
            if not self._numeric(bin):
                all_numeric = False
                break

        xmin, xmax = None, None
        output = []
        for bin, value in zip(self.bins, self.values):
            if value > 0.:
                if all_numeric:
                    x1, x2 = bin
                    if xmin is None or x1 < xmin: xmin = x1
                    if xmax is None or x2 > xmax: xmax = x2
                else:
                    output.append(bin)

        if all_numeric: return xmin, xmax
        else: return output

    def scatter(self, centroids=False, poisson=False, **frameargs):
        """Return the bins and values of the histogram as a Scatter plot.

        Arguments:
           centroids (bool): if `False`, use bin centers; if `True`,
           use centroids

           poisson (bool): if `False`, do not create error bars; if
           `True`, create error bars assuming the bin contents to
           belong to Poisson distributions

        Note:
           Asymmetric Poisson tail-probability is used for error bars
           on quantities up to 20 (using a pre-calculated table);
           for 20 and above, a symmetric square root is used
           (approximating Poisson(x) ~ Gaussian(x) for x >> 1).
        """

        kwds = {"linewidth": self.linewidth,
                "linestyle": self.linestyle,
                "linecolor": self.linecolor}
        kwds.update(frameargs)

        def poisson_errorbars(value):
            if value < 20:
                return {0: (0, 1.1475924708896912),
                        1: (-1, 1.3593357241843194),
                        2: (-2, 1.5187126521158518),
                        3: (-2.1423687562878797, 1.7239415816257235),
                        4: (-2.2961052720689565, 1.9815257924746845),
                        5: (-2.4893042928478337, 2.2102901353154891),
                        6: (-2.6785495948620621, 2.418184093020642),
                        7: (-2.8588433484599989, 2.6100604797946687),
                        8: (-3.0300038654056323, 2.7891396571794473),
                        9: (-3.1927880092968906, 2.9576883353481378),
                        10: (-3.348085587280849, 3.1173735938098446),
                        11: (-3.4967228532132424, 3.2694639669834089),
                        12: (-3.639421017629985, 3.4149513337692667),
                        13: (-3.7767979638286704, 3.5546286916146812),
                        14: (-3.9093811537390764, 3.6891418894420838),
                        15: (-4.0376219573077776, 3.8190252444691453),
                        16: (-4.1619085382943979, 3.9447267851063259),
                        17: (-4.2825766762666433, 4.0666265902382577),
                        18: (-4.3999186228618044, 4.185050401352413),
                        19: (-4.5141902851535463, 4.3002799167131514)}[value]
            else:
                return -math.sqrt(value), math.sqrt(value)

        if poisson: values = numpy.empty((len(self.bins), 4), dtype=numpy.float)
        else: values = numpy.empty((len(self.bins), 2), dtype=numpy.float)

        if centroids: values[:,0] = self.centroids()
        else: values[:,0] = self.centers()

        values[:,1] = self.values

        if poisson:
            for i in range(len(self.bins)):
                values[i,2:4] = poisson_errorbars(self.values[i])
            return Scatter(values=values, sig=("x", "y", "eyl", "ey"), **kwds)
        else:
            return Scatter(values=values, sig=("x", "y"), **kwds)

        ### to reproduce the table:
        # from scipy.stats import poisson
        # from scipy.optimize import bisect
        # from math import sqrt

        # def calculate_entry(value):
        #     def down(x):
        #         if x < 1e-5:
        #             return down(1e-5) - x
        #         else:
        #             if value in (0, 1, 2):
        #                 return poisson.cdf(value, x) - 1. - 2.*0.3413
        #             else:
        #                 return poisson.cdf(value, x) - poisson.cdf(value, value) - 0.3413

        #     def up(x):
        #         if x < 1e-5:
        #             return up(1e-5) - x
        #         else:
        #             if value in (0, 1, 2):
        #                 return poisson.cdf(value, x) - 1. + 2.*0.3413
        #             else:
        #                 return poisson.cdf(value, x) - poisson.cdf(value, value) + 0.3413

        #     table[value] = bisect(down, -100., 100.) - value, bisect(up, -100., 100.) - value
        #     if table[value][0] + value < 0.:
        #         table[value] = -value, table[value][1]

        # table = {}
        # for i in range(20):
        #     calculate_entry(i)
        
    def ranges(self, xlog=False, ylog=False):
        """Return a data-space bounding box as `xmin, ymin, xmax, ymax`.

        Arguments:
           xlog (bool): requesting a logarithmic x axis (negative
           and zero-valued contents are ignored)

           ylog (bool): requesting a logarithmic y axis
        """

        xmin, ymin, xmax, ymax = None, None, None, None
        all_numeric = True
        for bin, value in zip(self.bins, self.values):
            if self._numeric(bin):
                x1, x2 = bin
                if (not xlog or x1 > 0.) and (xmin is None or x1 < xmin): xmin = x1
                if (not xlog or x2 > 0.) and (xmax is None or x2 > xmax): xmax = x2
            else:
                all_numeric = False
            if (not ylog or value > 0.) and (ymin is None or value < ymin): ymin = value
            if (not ylog or value > 0.) and (ymax is None or value > ymax): ymax = value

        if not all_numeric:
            xmin, xmax = -0.5, len(self.bins) - 0.5

        if xmin is None and xmax is None:
            if xlog:
                xmin, xmax = 0.1, 1.
            else:
                xmin, xmax = 0., 1.
        if ymin is None and ymax is None:
            if ylog:
                ymin, ymax = 0.1, 1.
            else:
                ymin, ymax = 0., 1.

        if xmin == xmax:
            if xlog:
                xmin, xmax = xmin/2., xmax*2.
            else:
                xmin, xmax = xmin - 0.5, xmax + 0.5

        if ymin == ymax:
            if ylog:
                ymin, ymax = ymin/2., ymax*2.
            else:
                ymin, ymax = ymin - 0.5, ymax + 0.5

        return xmin, ymin, xmax, ymax

class Histogram(HistogramAbstract):
    """Represent a 1-D histogram with uniform bins.

    Arguments:
       numbins (int): number of bins

       low (float): low edge of first bin

       high (float): high edge of last bin

       storelimit (int or `None`): maximum number of values to store,
       so that the histogram bins can be redrawn; `None` means no
       limit

       linewidth (float): scale factor for the line used to draw the
       histogram border

       linestyle (tuple or string): "solid", "dashed", "dotted", or a
       tuple of numbers representing a dash-pattern

       linecolor (string, color, or `None`): color of the boundary
       line of the histogram area; no line if `None`

       fillcolor (string, color, or `None`): fill color of the
       histogram area; hollow if `None`

       gap (float): space drawn between bins, as a fraction of the bin
       width

       `**frameargs`: keyword arguments for the coordinate frame

    Public members:
       bins (list of `(low, high)` pairs): bin intervals (x axis)

       values (numpy array of floats): contents of each bin (y axis),
       has the same length as `bins`

       entries (int): unweighted number of entries accumulated so far

       underflow (float): number of values encountered that are less
       than all bin ranges

       overflow (float): number of values encountered that are greater
       than all bin ranges

       `storelimit`, `linewidth`, `linestyle`, `linecolor`,
       `fillcolor`, and frame arguments.

    Behavior:
       The histogram bins are initially fixed, but can be 'reshaped'
       if `entries <= storelimit`.

       After construction, do not set the bins directly; use `reshape`
       instead.

       Setting `linecolor = None` is the only proper way to direct the
       graphics backend to not draw a line around the histogram
       border.
    """

    def __init__(self, numbins, low, high, data=None, weights=None, storelimit=0, linewidth=1., linestyle="solid", linecolor="black", fillcolor=None, gap=0, **frameargs):
        self.reshape(numbins, low, high, refill=False, warnings=False)
        HistogramAbstract.__init__(self, self.bins, storelimit, linewidth, linestyle, linecolor, fillcolor, gap, **frameargs)
        if data is not None:
            if weights is not None:
                self.fill(data, weights)
            else:
                self.fill(data)

    def low(self):
        """Return the low edge of the lowest bin."""
        return self._low

    def high(self):
        """Return the high edge of the highest bin."""
        return self._high

    def __repr__(self):
        try:
            xlabel = " \"%s\"" % self.xlabel
        except AttributeError:
            xlabel = ""
        return "<Histogram %d %g %g%s at 0x%x>" % (len(self.bins), self.low(), self.high(), xlabel, id(self))

    def reshape(self, numbins, low=None, high=None, refill=True, warnings=True):
        """Change the bin structure of the histogram and refill its contents.

        Arguments:
           numbins (int): new number of bins

           low (float or `None`): new low edge, or `None` to keep the
           old one

           high (float or `None`): new high edge, or `None` to keep
           the old one

           refill (bool): call `refill` after setting the bins

           warnings (bool): raise `ContainerException` if `storelimit
           < entries`: that is, if the reshaping cannot be performed
           without losing data
        """

        if low is None: low = self.low()
        if high is None: high = self.high()

        if warnings:
            if self._lenstore is None:
                if len(self._store) < self.entries: raise ContainerException, "Cannot reshape a histogram without a full set of stored data"
            else:
                if self._lenstore < self.entries: raise ContainerException, "Cannot reshape a histogram without a full set of stored data"
        self._low, self._high, self._factor = low, high, numbins/float(high - low)
        self._binwidth = (high-low)/float(numbins)
        lows = numpy.arange(low, high, self._binwidth)
        highs = lows + self._binwidth
        self.bins = zip(lows, highs)
        if refill: self.refill()
    
    def optimize(self, numbins=utilities.binning, ranges=utilities.calcrange_quartile):
        """Optimize the number of bins and/or range of the histogram.

        Arguments:

           numbins (function, int, or `None`): function that returns
           an optimal number of bins, given a dataset, or a simple
           number of bins, or `None` to leave the number of bins as it is

           ranges (function, (low, high), or `None`): function that
           returns an optimal low, high range, given a dataset, or an
           explicit low, high tuple, or `None` to leave the ranges as
           they are
        """

        if numbins is Auto: numbins = utilities.binning
        if ranges is Auto: ranges = utilities.calcrange_quartile

        # first do the ranges
        if ranges is None:
            low, high = self.low(), self.high()

        elif isinstance(ranges, (tuple, list)) and len(ranges) == 2 and isinstance(ranges[0], (numbers.Number, numpy.number)) and isinstance(ranges[1], (numbers.Number, numpy.number)):
            low, high = ranges

        elif callable(ranges):
            if self._lenstore is None:
                if len(self._store) < self.entries: raise ContainerException, "Cannot optimize a histogram without a full set of stored data"
            else:
                if self._lenstore < self.entries: raise ContainerException, "Cannot optimize a histogram without a full set of stored data"
            low, high = ranges(self._store, self.__dict__.get("xlog", False))

        else:
            raise ContainerException, "The 'ranges' argument must be a function, (low, high), or `None`."

        # then do the binning
        if numbins is None:
            numbins = len(self.bins)

        elif isinstance(numbins, (int, long)):
            pass

        elif callable(numbins):
            if self._lenstore is None:
                if len(self._store) < self.entries: raise ContainerException, "Cannot optimize a histogram without a full set of stored data"
                storecopy = numpy.array(filter(lambda x: low <= x < high, self._store))
            else:
                if self._lenstore < self.entries: raise ContainerException, "Cannot optimize a histogram without a full set of stored data"
                storecopy = self._store[0:self._lenstore]
            numbins = numbins(storecopy, low, high)

        else:
            raise ContainerException, "The 'numbins' argument must be a function, int, or `None`."

        self.reshape(numbins, low, high)

    def fill(self, values, weights=None, limit=None, fillstore=True):
        """Put one or many values into the histogram.

        Arguments:
           values (float or list of floats): value or values to put
           into the histogram

           weights (float, list of floats, or `None`): weights for
           each value; all have equal weight if `weights = None`.

           limit (int or `None`): maximum number of values, weights to
           put into the histogram

           fillstore (bool): also fill the histogram's store (if any)

        Behavior:
           `itertools.izip` is used to loop over values and weights,
           filling the histogram.  If values and weights have
           different lengths, the filling operation would be truncated
           to the shorter list.

           Histogram weights are usually either 1 or 1/(value uncertainty)**2.
        """

        # handle the case of being given only one value
        if isinstance(values, (numbers.Number, numpy.number)):
            values = [values]

        if weights is None:
            weights = numpy.ones(len(values), numpy.float)
        elif isinstance(weights, (numbers.Number, numpy.number)):
            weights = [weights]

        for counter, (value, weight) in enumerate(itertools.izip(values, weights)):
            if limit is not None and counter >= limit: break

            if fillstore:
                if self._lenstore is None:
                    self._store.append(value)
                    self._weights.append(weight)
                elif self._lenstore < self.storelimit:
                    self._store[self._lenstore] = value
                    self._weights[self._lenstore] = weight
                    self._lenstore += 1

            index = int(math.floor((value - self._low)*self._factor))
            if index < 0:
                self.underflow += weight
            elif index >= len(self.bins):
                self.overflow += weight
            else:
                self.values[index] += weight
                self._sumx[index] += weight * value
            self.entries += 1

def histogramInteger(low, high, **kwds):
    """Create a histogram of all integers between low and high (inclusive).

    Keyword arguments are passed to the Histogram class constructor.
    """
    return Histogram((high - low + 1), low - 0.5, high + 0.5, **kwds)

class HistogramNonUniform(HistogramAbstract):
    """Represent a 1-D histogram with uniform bins.

    Arguments:
       bins (list of `(low, high)` pairs): user-defined bin intervals

       storelimit (int or `None`): maximum number of values to store,
       so that the histogram bins can be redrawn; `None` means no
       limit

       linewidth (float): scale factor for the line used to draw the
       histogram border

       linestyle (tuple or string): "solid", "dashed", "dotted", or a
       tuple of numbers representing a dash-pattern

       linecolor (string, color, or `None`): color of the boundary
       line of the histogram area; no line if `None`

       fillcolor (string, color, or `None`): fill color of the
       histogram area; hollow if `None`

       gap (float): space drawn between bins, as a fraction of the bin
       width

       `**frameargs`: keyword arguments for the coordinate frame

    Public members:
       values (numpy array of floats): contents of each bin (y axis),
       has the same length as `bins`

       entries (int): unweighted number of entries accumulated so far

       underflow (float): number of values encountered that are less
       than all bin ranges

       overflow (float): number of values encountered that are greater
       than all bin ranges

       inflow (float): number of values encountered that are between
       bins (if there are any gaps between user-defined bin intervals)

       `bins`, `storelimit`, `linewidth`, `linestyle`, `linecolor`,
       `fillcolor`, and frame arguments.

    Behavior:
       If any bin intervals overlap, values will be entered into the
       first of the two overlapping bins.

       After construction, do not set the bins directly; use `reshape`
       instead.

       Setting `linecolor = None` is the only proper way to direct the
       graphics backend to not draw a line around the histogram
       border.
    """

    def __init__(self, bins, data=None, weights=None, storelimit=0, linewidth=1., linestyle="solid", linecolor="black", fillcolor=None, gap=0, **frameargs):
        HistogramAbstract.__init__(self, bins, storelimit, linewidth, linestyle, linecolor, fillcolor, gap, **frameargs)
        self._low, self._high = None, None
        for low, high in self.bins:
            if self._low is None or low < self._low:
                self._low = low
            if self._high is None or high > self._high:
                self._high = high
        if data is not None:
            if weights is not None:
                self.fill(data, weights)
            else:
                self.fill(data)

    def low(self):
        """Return the low edge of the lowest bin."""
        return self._low

    def high(self):
        """Return the high edge of the highest bin."""
        return self._high

    def __repr__(self):
        try:
            xlabel = " \"%s\"" % self.xlabel
        except AttributeError:
            xlabel = ""
        return "<HistogramNonUniform %d%s at 0x%x>" % (len(self.bins), xlabel, id(self))

    def reshape(self, bins, refill=True, warnings=True):
        """Change the bin structure of the histogram and refill its contents.

        Arguments:
           bins (list of `(low, high)` pairs): user-defined bin intervals

           refill (bool): call `refill` after setting the bins

           warnings (bool): raise `ContainerException` if `storelimit
           < entries`: that is, if the reshaping cannot be performed
           without losing data
        """

        if warnings:
            if self._lenstore is None:
                if len(self._store) < self.entries: raise ContainerException, "Cannot reshape a histogram without a full set of stored data"
            else:
                if self._lenstore < self.entries: raise ContainerException, "Cannot reshape a histogram without a full set of stored data"
        self.bins = bins
        if refill: self.refill()

    def fill(self, values, weights=None, limit=None, fillstore=True):
        """Put one or many values into the histogram.

        Arguments:
           values (float or list of floats): value or values to put
           into the histogram

           weights (float, list of floats, or `None`): weights for
           each value; all have equal weight if `weights = None`.

           limit (int or `None`): maximum number of values, weights to
           put into the histogram

           fillstore (bool): also fill the histogram's store (if any)

        Behavior:
           `itertools.izip` is used to loop over values and weights,
           filling the histogram.  If values and weights have
           different lengths, the filling operation would be truncated
           to the shorter list.

           Histogram weights are usually either 1 or 1/(value uncertainty)**2.
        """

        # handle the case of being given only one value
        if isinstance(values, (numbers.Number, numpy.number)):
            values = [values]

        if weights is None:
            weights = numpy.ones(len(values), numpy.float)
        elif isinstance(weights, (numbers.Number, numpy.number)):
            weights = [weights]

        for counter, (value, weight) in enumerate(itertools.izip(values, weights)):
            if limit is not None and counter >= limit: break

            if fillstore:
                if self._lenstore is None:
                    self._store.append(value)
                    self._weights.append(weight)
                elif self._lenstore < self.storelimit:
                    self._store[self._lenstore] = value
                    self._weights[self._lenstore] = weight
                    self._lenstore += 1

            filled = False
            less_than_all = True
            greater_than_all = True
            for i, (low, high) in enumerate(self.bins):
                if low <= value < high:
                    self.values[i] += weight
                    self._sumx[i] += weight * value
                    filled = True
                    break
                elif not (value < low): less_than_all = False
                elif not (value >= high): greater_than_all = False

            if not filled: 
                if less_than_all: self.underflow += weight
                elif greater_than_all: self.overflow += weight
                else: self.inflow += weight

            self.entries += 1

class HistogramCategorical(HistogramAbstract):
    """Represent a 1-D histogram with categorical bins (a bar chart).

    Arguments:
       bins (list of strings): names of the categories

       storelimit (int or `None`): maximum number of values to store,
       so that the histogram bins can be redrawn; `None` means no
       limit

       linewidth (float): scale factor for the line used to draw the
       histogram border

       linestyle (tuple or string): "solid", "dashed", "dotted", or a
       tuple of numbers representing a dash-pattern

       linecolor (string, color, or `None`): color of the boundary
       line of the histogram area; no line if `None`

       fillcolor (string, color, or `None`): fill color of the
       histogram area; hollow if `None`

       gap (float): space drawn between bins, as a fraction of the bin
       width

       `**frameargs`: keyword arguments for the coordinate frame

    Public members:
       values (numpy array of floats): contents of each bin (y axis),
       has the same length as `bins`

       entries (int): unweighted number of entries accumulated so far

       inflow (float): number of values encountered that do not belong
       to any bins

       `bins`, `storelimit`, `linewidth`, `linestyle`, `linecolor`,
       `fillcolor`, and frame arguments.

    Behavior:
       After construction, never change the bins.

       Setting `linecolor = None` is the only proper way to direct the
       graphics backend to not draw a line around the histogram
       border.
    """

    def __init__(self, bins, data=None, weights=None, storelimit=0, linewidth=1., linestyle="solid", linecolor="black", fillcolor=None, gap=0.1, **frameargs):
        self._catalog = dict(map(lambda (x, y): (y, x), enumerate(bins)))
        HistogramAbstract.__init__(self, bins, storelimit, linewidth, linestyle, linecolor, fillcolor, gap, **frameargs)
        if data is not None:
            if weights is not None:
                self.fill(data, weights)
            else:
                self.fill(data)

    def __repr__(self):
        try:
            xlabel = " \"%s\"" % self.xlabel
        except AttributeError:
            xlabel = ""
        return "<HistogramCategorical %d%s at 0x%x>" % (len(self.bins), xlabel, id(self))

    def low(self):
        """Return the effective low edge, with all categories treated as integers (-0.5)."""

        return -0.5

    def high(self):
        """Return the effective low edge, with all categories treated as integers (numbins - 0.5)."""

        return len(self.bins) - 0.5

    def top(self, N):
        """Return a simplified histogram containing only the top N values (sorted)."""

        pairs = zip(self.bins, self.values)
        pairs.sort(lambda a, b: cmp(b[1], a[1]))
        othervalue = sum([values for bins, values in pairs[N:]])
        bins, values = zip(*pairs[:N])
        h = HistogramCategorical(list(bins) + ["other"])
        h.values = numpy.array(list(values) + [othervalue])
        for name, value in self.__dict__.items():
            if name not in ("bins", "values"):
                h.__dict__[name] = value
        return h

    def binorder(self, *neworder):
        """Specify a new order for the bins with a list of string arguments (updating bin values).

        All arguments must be the names of existing bins.

        If a bin name is missing, it will be deleted!
        """

        reverse = dict(map(lambda (x, y): (y, x), enumerate(self.bins)))

        indicies = []
        for name in neworder:
            if name not in self.bins:
                raise ContainerException, "Not a recognized bin name: \"%s\"." % name

            indicies.append(reverse[name])

        newinflow = 0.
        for i, name in enumerate(self.bins):
            if name not in neworder:
                newinflow += self.values[i]

        self.bins = [self.bins[i] for i in indicies]

        indicies = numpy.array(indicies)
        self.values = self.values[indicies]
        self._sumx = self._sumx[indicies]

        self.inflow += newinflow

    def fill(self, values, weights=None, limit=None, fillstore=True):
        """Put one or many values into the histogram.

        Arguments:
           values (float or list of floats): value or values to put
           into the histogram

           weights (float, list of floats, or `None`): weights for
           each value; all have equal weight if `weights = None`.

           limit (int or `None`): maximum number of values, weights to
           put into the histogram

           fillstore (bool): also fill the histogram's store (if any)

        Behavior:
           `itertools.izip` is used to loop over values and weights,
           filling the histogram.  If values and weights have
           different lengths, the filling operation would be truncated
           to the shorter list.

           Histogram weights are usually either 1 or 1/(value uncertainty)**2.
        """

        # handle the case of being given only one value
        if isinstance(values, basestring):
            values = [values]

        if weights is None:
            weights = numpy.ones(len(values), numpy.float)
        elif isinstance(weights, (numbers.Number, numpy.number)):
            weights = [weights]

        for counter, (value, weight) in enumerate(itertools.izip(values, weights)):
            if limit is not None and counter >= limit: break

            try:
                value = self._catalog[value]
                self.values[value] += weight
                self._sumx[value] += weight * value
            except KeyError:
                value = -1
                self.inflow += weight
            self.entries += 1

            if fillstore:
                if self._lenstore is None:
                    self._store.append(value)
                    self._weights.append(weight)
                elif self._lenstore < self.storelimit:
                    self._store[self._lenstore] = value
                    self._weights[self._lenstore] = weight
                    self._lenstore += 1

######################################################### Scatter plots, with and without error bars, and timeseries

class Scatter(Frame):
    """Represents a scatter of X-Y points, a line graph, and error bars.

    Signatures::

       Scatter(values, sig, ...)
       Scatter(x, y, [ex,] [ey,] [exl,] [eyl,] ...)

    Arguments for signature 1:
       values (numpy array of N-dimensional points): X-Y points to
       draw (with possible error bars)

       sig (list of strings): how to interpret each N-dimensional
       point, e.g. `('x', 'y', 'ey')` for triplets of x, y, and y
       error bars

    Arguments for signature 2:
       x (list of floats): x values

       y (list of floats): y values

       ex (list of floats or `None`): symmetric or upper errors in x;
       `None` for no x error bars

       ey (list of floats or `None`): symmetric or upper errors in y

       exl (list of floats or `None`): asymmetric lower errors in x

       eyl (list of floats or `None`): asymmetric lower errors in y

    Arguments for both signatures:
       limit (int or `None`): maximum number of points to draw
       (randomly selected if less than total number of points)

       calcrange (function): a function that chooses a reasonable range
       to plot, based on the data (overruled by `xmin`, `xmax`, etc.)

       connector (`None`, "unsorted", "xsort", "ysort"): toggles
       whether a line is drawn through all of the visible points, and
       whether those points are sorted before drawing the line

       marker (string or `None`): symbol to draw at each point; `None`
       for no markers (e.g. just lines)

       markersize (float): scale factor to resize marker points

       markercolor (string, color, or `None`): color of the marker
       points; hollow markers if `None`

       markeroutline (string, color, or `None`): color of the outline
       of each marker; no outline if `None`

       linewidth (float): scale factor to resize line width

       linestyle (tuple or string): "solid", "dashed", "dotted", or a
       tuple of numbers representing a dash-pattern

       linecolor (string, color, or `None`): color of a line
       connecting all points; no line if `None`

       `**frameargs`: keyword arguments for the coordinate frame

    Public members:
       `values`, `sig`, `limit`, `calcrange`, `connector`, `marker`,
       `markersize`, `markercolor`, `markeroutline`, `lines`,
       `linewidth`, `linestyle`, `linecolor`, and frame arguments.

    Behavior:
       Points are stored internally as an N-dimensional numpy array of
       `values`, with meanings specified by `sig`.

       Input points are _copied_, not set by reference, with both
       input methods.  The set-by-signature method is likely to be
       faster for large datasets.
       
       Setting `limit` to a value other than `None` restricts the
       number of points to draw in the graphical backend, something
       that may be necessary if the number of points is very large.  A
       random subset is selected when the scatter plot is drawn.

       The numerical `limit` refers to the number of points drawn
       *within a coordinate frame,* so zooming in will reveal more
       points.

       Since the input set of points is not guaranteed to be
       monatonically increasing in x, a line connecting all points
       might cross itself.

       Setting `marker = None` is the only proper way to direct the
       graphics backend to not draw a marker at each visible point

       Setting `linecolor = None` is the only proper way to direct the
       graphics backend to not draw a line connecting all visible points

    Exceptions:
       At least `x` and `y` are required.
    """

    _not_frameargs = ["sig", "values", "limit", "calcrange", "connector", "marker", "markersize", "markercolor", "markeroutline", "linewidth", "linestyle", "linecolor"]

    def __init__(self, values=[], sig=None, x=None, y=None, ex=None, ey=None, exl=None, eyl=None, limit=None, calcrange=utilities.calcrange, connector=None, marker="circle", markersize=1., markercolor="black", markeroutline=None, linewidth=1., linestyle="solid", linecolor="black", **frameargs):
        self.limit, self.calcrange = limit, calcrange
        self.connector, self.marker, self.markersize, self.markercolor, self.markeroutline, self.linewidth, self.linestyle, self.linecolor = connector, marker, markersize, markercolor, markeroutline, linewidth, linestyle, linecolor

        if sig is None:
            self.setvalues(x, y, ex, ey, exl, eyl)
        else:
            self.setbysig(values, sig)

        Frame.__init__(self, **frameargs)

    def __repr__(self):
        if self.limit is None:
            return "<Scatter %d (draw all) at 0x%x>" % (len(self.values), id(self))
        else:
            return "<Scatter %d (draw %d) at 0x%x>" % (len(self.values), self.limit, id(self))

    def index(self):
        """Returns a dictionary of sig values ("x", "y", etc.) to `values` index.

        Example usage::

           scatter.values[0:1000,scatter.index()["ex"]]

        returns the first thousand x error bars.
        """

        return dict(zip(self.sig, range(len(self.sig))))

    def sort(self, key="x"):
        """Sorts the data in values by one of the fields (does not affect graphical output)."""
        self.values = self.values[self.values[:,self.index()[key]].argsort(),]

    def _prepare(self, xmin=None, ymin=None, xmax=None, ymax=None, xlog=None, ylog=None):
        if len(self.values) == 0:
            self._xlimited_values = numpy.array([], dtype=numpy.float)
            self._ylimited_values = numpy.array([], dtype=numpy.float)
            self._limited_values = numpy.array([], dtype=numpy.float)
            return

        index = self.index()

        # select elements within the given ranges
        mask = numpy.ones(len(self.values), dtype="bool")
        x = self.values[:,index["x"]]
        y = self.values[:,index["y"]]

        def limitx(mask):
            if "ex" in index:
                numpy.logical_and(mask, (x + abs(self.values[:,index["ex"]]) > xmin), mask)
            else:
                numpy.logical_and(mask, (x > xmin), mask)

            if "exl" in index:
                numpy.logical_and(mask, (x - abs(self.values[:,index["exl"]]) < xmax), mask)
            elif "ex" in index:
                numpy.logical_and(mask, (x - abs(self.values[:,index["ex"]]) < xmax), mask)
            else:
                numpy.logical_and(mask, (x < xmax), mask)
            return mask

        def limity(mask):
            if "ey" in index:
                numpy.logical_and(mask, (y + abs(self.values[:,index["ey"]]) > ymin), mask)
            else:
                numpy.logical_and(mask, (y > ymin), mask)

            if "eyl" in index:
                numpy.logical_and(mask, (y - abs(self.values[:,index["eyl"]]) < ymax), mask)
            elif "ey" in index:
                numpy.logical_and(mask, (y - abs(self.values[:,index["ey"]]) < ymax), mask)
            else:
                numpy.logical_and(mask, (y < ymax), mask)
            return mask

        if self.connector == "xsort":
            mask = limitx(mask)
            self._xlimited_values = (self.values[mask])[:,(index["x"],index["y"])]
            self._ylimited_values = numpy.array([], dtype=numpy.float)
            mask = limity(mask)

        elif self.connector == "ysort":
            mask = limity(mask)
            self._xlimited_values = numpy.array([], dtype=numpy.float)
            self._ylimited_values = (self.values[mask])[:,(index["x"],index["y"])]
            mask = limitx(mask)

        elif self.connector == "unsorted":
            self._xlimited_values = self.values[:,(index["x"],index["y"])]
            self._ylimited_values = numpy.array([], dtype=numpy.float)
            mask = limitx(mask)
            mask = limity(mask)

        else:
            self._xlimited_values = numpy.array([], dtype=numpy.float)
            self._ylimited_values = numpy.array([], dtype=numpy.float)
            mask = limitx(mask)
            mask = limity(mask)
            
        inrange = self.values[mask]

        # select an unbiased subset
        if self.limit is not None and self.limit < len(inrange):
            self._limited_values = inrange[random.sample(xrange(len(inrange)), self.limit)]
        else:
            self._limited_values = inrange

        if self.limit is not None and self.limit < len(self._xlimited_values):
            self._xlimited_values = self._xlimited_values[random.sample(xrange(len(self._xlimited_values)), self.limit)]

        if self.limit is not None and self.limit < len(self._ylimited_values):
            self._ylimited_values = self._ylimited_values[random.sample(xrange(len(self._ylimited_values)), self.limit)]

        # sort the xlimited and ylimited data
        if self.connector == "xsort" and len(self._xlimited_values) > 0:
            self._xlimited_values = self._xlimited_values[numpy.argsort(self._xlimited_values[:,0])]

        if self.connector == "ysort" and len(self._ylimited_values) > 0:
            self._ylimited_values = self._ylimited_values[numpy.argsort(self._ylimited_values[:,1])]

    def setbysig(self, values, sig=("x", "y")):
        """Sets the values using a signature.

        Arguments:
           values (numpy array of N-dimensional points): X-Y points to
           draw (with possible error bars)

           sig (list of strings): how to interpret each N-dimensional
           point, e.g. `('x', 'y', 'ey')` for triplets of x, y, and y
           error bars

        Exceptions:
           At least `x` and `y` are required.
        """

        if "x" not in sig or "y" not in sig:
            raise ContainerException, "Signature must contain \"x\" and \"y\""
        self.sig = sig
        self.values = numpy.array(values, dtype=numpy.float)

    def setvalues(self, x=None, y=None, ex=None, ey=None, exl=None, eyl=None):
        """Sets the values with separate lists.

        Arguments:
           x (list of floats or strings): x values

           y (list of floats or strings): y values

           ex (list of floats or `None`): symmetric or upper errors in x;
           `None` for no x error bars

           ey (list of floats or `None`): symmetric or upper errors in y

           exl (list of floats or `None`): asymmetric lower errors in x

           eyl (list of floats or `None`): asymmetric lower errors in y

        Exceptions:
           At least `x` and `y` are required.
        """

        if x is None and y is None:
            raise ContainerException, "Signature must contain \"x\" and \"y\""

        longdim = 0
        shortdim = 0
        if x is not None:
            longdim = max(longdim, len(x))
            shortdim += 1
        if y is not None:
            longdim = max(longdim, len(y))
            shortdim += 1
        if ex is not None:
            longdim = max(longdim, len(ex))
            shortdim += 1
        if ey is not None:
            longdim = max(longdim, len(ey))
            shortdim += 1
        if exl is not None:
            longdim = max(longdim, len(exl))
            shortdim += 1
        if eyl is not None:
            longdim = max(longdim, len(eyl))
            shortdim += 1

        self.sig = []
        self.values = numpy.empty((longdim, shortdim), dtype=numpy.float)

        if x is not None:
            x = numpy.array(x)
            if x.dtype.char == "?":
                x = numpy.array(x, dtype=numpy.string_)
            if x.dtype.char in numpy.typecodes["Character"] + "Sa":
                if len(x) > 0:
                    unique = numpy.unique(x)
                    self._xticks = dict(map(lambda (i, val): (float(i+1), val), enumerate(unique)))
                    strtoval = dict(map(lambda (i, val): (val, float(i+1)), enumerate(unique)))
                    x = numpy.apply_along_axis(numpy.vectorize(lambda s: strtoval[s]), 0, x)
                else:
                    x = numpy.array([], dtype=numpy.float)

            self.values[:,len(self.sig)] = x
            self.sig.append("x")

        if y is not None:
            y = numpy.array(y)
            if y.dtype.char == "?":
                y = numpy.array(y, dtype=numpy.string_)
            if y.dtype.char in numpy.typecodes["Character"] + "Sa":
                if len(y) > 0:
                    unique = numpy.unique(y)
                    self._yticks = dict(map(lambda (i, val): (float(i+1), val), enumerate(unique)))
                    strtoval = dict(map(lambda (i, val): (val, float(i+1)), enumerate(unique)))
                    y = numpy.apply_along_axis(numpy.vectorize(lambda s: strtoval[s]), 0, y)
                else:
                    y = numpy.array([], dtype=numpy.float)

            self.values[:,len(self.sig)] = y
            self.sig.append("y")

        if ex is not None:
            self.values[:,len(self.sig)] = ex
            self.sig.append("ex")
        if ey is not None:
            self.values[:,len(self.sig)] = ey
            self.sig.append("ey")
        if exl is not None:
            self.values[:,len(self.sig)] = exl
            self.sig.append("exl")
        if eyl is not None:
            self.values[:,len(self.sig)] = eyl
            self.sig.append("eyl")

    def append(self, x, y, ex=None, ey=None, exl=None, eyl=None):
        """Append one point to the dataset.

        Arguments:
           x (float): x value

           y (float): y value

           ex (float or `None`): symmetric or upper error in x

           ey (list of floats or `None`): symmetric or upper error in y

           exl (list of floats or `None`): asymmetric lower error in x

           eyl (list of floats or `None`): asymmetric lower error in y

        Exceptions:
           Input arguments must match the signature of the dataset
           (`sig`).

        Considerations:
           This method is provided for convenience; it is more
           efficient to input all points at once during
           construction.
        """

        index = self.index()
        oldlen = self.values.shape[0]
        oldwidth = self.values.shape[1]

        for i in self.sig:
            if eval(i) is None:
                raise ContainerException, "This %s instance requires %s" % (self.__class__.__name__, i)

        newvalues = [0.]*oldwidth
        if x is not None: newvalues[index["x"]] = x
        if y is not None: newvalues[index["y"]] = y
        if ex is not None: newvalues[index["ex"]] = ex
        if ey is not None: newvalues[index["ey"]] = ey
        if exl is not None: newvalues[index["exl"]] = exl
        if eyl is not None: newvalues[index["eyl"]] = eyl

        self.values.resize((oldlen+1, oldwidth), refcheck=False)
        self.values[oldlen,:] = newvalues

    def _strip(self, which, limited=False):
        try:
            index = self.index()[which]
        except KeyError:
            raise ContainerException, "The signature doesn't have any \"%s\" variable" % which
        if limited: return self._limited_values[:,index]
        else: return self.values[:,index]

    def x(self, limited=False):
        """Return a 1-D numpy array of x values.

        Arguments:
           limited (bool): if True, only return randomly selected
           values (must be called after `_prepare()`)
        """
        return self._strip("x", limited)

    def y(self, limited=False):
        """Return a 1-D numpy array of y values.

        Arguments:
           limited (bool): if True, only return randomly selected
           values (must be called after `_prepare()`)
        """
        return self._strip("y", limited)

    def ex(self, limited=False):
        """Return a 1-D numpy array of x error bars.

        Arguments:
           limited (bool): if True, only return randomly selected
           values (must be called after `_prepare()`)
        """
        return self._strip("ex", limited)

    def ey(self, limited=False):
        """Return a 1-D numpy array of y error bars.

        Arguments:
           limited (bool): if True, only return randomly selected
           values (must be called after `_prepare()`)
        """
        return self._strip("ey", limited)

    def exl(self, limited=False):
        """Return a 1-D numpy array of x lower error bars.

        Arguments:
           limited (bool): if True, only return randomly selected
           values (must be called after `_prepare()`)
        """
        return self._strip("exl", limited)

    def eyl(self, limited=False):
        """Return a 1-D numpy array of y lower error bars.

        Arguments:
           limited (bool): if True, only return randomly selected
           values (must be called after `_prepare()`)
        """
        return self._strip("eyl", limited)

    def ranges(self, xlog=False, ylog=False):
        """Return a data-space bounding box as `xmin, ymin, xmax, ymax`.

        Arguments:
           xlog (bool): requesting a logarithmic x axis (negative
           and zero-valued contents are ignored)

           ylog (bool): requesting a logarithmic y axis
        """

        x = self.x()
        y = self.y()

        # if we're plotting logarithmically, only the positive values are relevant for ranges
        if xlog or ylog:
            mask = numpy.ones(len(self.values), dtype="bool")
            if xlog:
                numpy.logical_and(mask, (x > 0.), mask)
            if ylog:
                numpy.logical_and(mask, (y > 0.), mask)
            x = x[mask]
            y = y[mask]

        if len(x) < 2:
            if xlog:
                xmin, xmax = 0.1, 1.
            else:
                xmin, xmax = 0., 1.
            if ylog:
                ymin, ymax = 0.1, 1.
            else:
                ymin, ymax = 0., 1.

        elif callable(self.calcrange):
            xmin, xmax = self.calcrange(x, xlog)
            ymin, ymax = self.calcrange(y, ylog)

        else:
            raise ContainerException, "Scatter.calcrange must be a function."

        if xmin == xmax:
            if xlog:
                xmin, xmax = xmin/2., xmax*2.
            else:
                xmin, xmax = xmin - 0.5, xmax + 0.5

        if ymin == ymax:
            if ylog:
                ymin, ymax = ymin/2., ymax*2.
            else:
                ymin, ymax = ymin - 0.5, ymax + 0.5

        return xmin, ymin, xmax, ymax

class TimeSeries(Scatter):
    """A scatter-plot in which the x axis is interpreted as time strings.

    Arguments:
       informat (string or `None`): time formatting string for
       interpreting x data (see `time documentation
       <http://docs.python.org/library/time.html#time.strftime>`_)

       outformat (string): time formatting string for plotting

       subseconds (bool): if True, interpret ".xxx" at the end of
       the string as fractions of a second

       t0 (number or time-string): the time from which to start
       counting; zero is equivalent to Jan 1, 1970

       x (list of strings): time strings for the x axis

       y (list of floats): y values

       ex (list of floats or `None`): symmetric or upper errors in x
       (in seconds); `None` for no x error bars

       ey (list of floats or `None`): symmetric or upper errors in y

       exl (list of floats or `None`): asymmetric lower errors in x

       eyl (list of floats or `None`): asymmetric lower errors in y

       limit (int or `None`): maximum number of points to draw
       (randomly selected if less than total number of points)

       calcrange (function): a function that chooses a reasonable range
       to plot, based on the data (overruled by `xmin`, `xmax`, etc.)

       connector (`None`, "unsorted", "xsort", "ysort"): toggles
       whether a line is drawn through all of the visible points, and
       whether those points are sorted before drawing the line

       marker (string or `None`): symbol to draw at each point; `None`
       for no markers (e.g. just lines)

       markersize (float): scale factor to resize marker points

       markercolor (string, color, or `None`): color of the marker
       points; hollow markers if `None`

       markeroutline (string, color, or `None`): color of the outline
       of each marker; no outline if `None`

       linewidth (float): scale factor to resize line width

       linestyle (tuple or string): "solid", "dashed", "dotted", or a
       tuple of numbers representing a dash-pattern

       linecolor (string, color, or `None`): color of a line
       connecting all points; no line if `None`

       `**frameargs`: keyword arguments for the coordinate frame

    Public members:
       `informat`, `outformat`, `values`, `sig`, `limit`, `calcrange`,
       `connector`, `marker`, `markersize`, `markercolor`,
       `markeroutline`, `lines`, `linewidth`, `linestyle`,
       `linecolor`, and frame arguments.

    Behavior:
       Points are stored internally as an N-dimensional numpy array of
       `values`, with meanings specified by `sig`.

       Input points are _copied_, not set by reference, with both
       input methods.  The set-by-signature method is likely to be
       faster for large datasets.
       
       Setting `limit` to a value other than `None` restricts the
       number of points to draw in the graphical backend, something
       that may be necessary if the number of points is very large.  A
       random subset is selected when the scatter plot is drawn.

       The numerical `limit` refers to the number of points drawn
       *within a coordinate frame,* so zooming in will reveal more
       points.

       Since the input set of points is not guaranteed to be
       monatonically increasing in x, a line connecting all points
       might cross itself.

       Setting `marker = None` is the only proper way to direct the
       graphics backend to not draw a marker at each visible point

       Setting `linecolor = None` is the only proper way to direct the
       graphics backend to not draw a line connecting all visible points

    Exceptions:
       At least `x` and `y` are required.
    """

    _not_frameargs = Scatter._not_frameargs + ["informat", "outformat"]

    def __init__(self, informat="%Y-%m-%d %H:%M:%S", outformat="%Y-%m-%d %H:%M:%S", subseconds=False, t0=0., x=None, y=None, ex=None, ey=None, exl=None, eyl=None, limit=None, calcrange=utilities.calcrange, connector="xsort", marker=None, markersize=1., markercolor="black", markeroutline=None, linewidth=1., linestyle="solid", linecolor="black", **frameargs):
        self.__dict__["informat"] = informat
        self.__dict__["outformat"] = outformat

        self._subseconds, self._t0 = subseconds, t0
        Scatter.__init__(self, x=utilities.fromtimestring(x, informat, subseconds, t0), y=y, ex=ex, ey=ey, exl=exl, eyl=eyl, limit=limit, calcrange=calcrange, connector=connector, marker=marker, markersize=markersize, markercolor=markercolor, markeroutline=markeroutline, linewidth=linewidth, linestyle=linestyle, linecolor=linecolor, **frameargs)
        
    def __repr__(self):
        if self.limit is None:
            return "<TimeSeries %d (draw all) at 0x%x>" % (len(self.values), id(self))
        else:
            return "<TimeSeries %d (draw %d) at 0x%x>" % (len(self.values), self.limit, id(self))

    def append(self, x, y, ex=None, ey=None, exl=None, eyl=None):
        """Append one point to the dataset.

        Arguments:
           x (string): x value (a time-string)

           y (float): y value

           ex (float or `None`): symmetric or upper error in x

           ey (list of floats or `None`): symmetric or upper error in y

           exl (list of floats or `None`): asymmetric lower error in x

           eyl (list of floats or `None`): asymmetric lower error in y

        Exceptions:
           Input arguments must match the signature of the dataset
           (`sig`).

        Considerations:
           This method is provided for convenience; it is more
           efficient to input all points at once during
           construction.
        """
        Scatter.append(self, utilities.fromtimestring(x, self.informat, self._subseconds, self._t0), y, ex, ey, exl, eyl)

    def totimestring(self, timenumbers):
        """Convert a number of seconds or a list of numbers into time string(s).

        Arguments:
           timenumbers (number or list of numbers): time(s) to be
           converted

        Behavior:
           If only one `timenumbers` is passed, the return value is a
           single string; if a list of strings is passed, the return value
           is a list of strings.

           Uses this timeseries's `outformat` and `t0` for the conversion.
        """
        return utilities.totimestring(timenumbers, self.outformat, self._subseconds, self._t0)

    def fromtimestring(self, timestrings):
        """Convert a time string or many time strings into a number(s) of seconds.

        Arguments:
           timestring (string or list of strings): time string(s) to be
           converted

        Behavior:
           If only one `timestring` is passed, the return value is a
           single number; if a list of strings is passed, the return value
           is a list of numbers.

           Uses this timeseries's `informat` and `t0` for the
           conversion.
        """
        return utilities.fromtimestring(timestrings, self.informat, self._subseconds, self._t0)

    def timeticks(self, major, minor, start=None):
        """Set x tick-marks to temporally meaningful values.

        Arguments:
           major (number): number of seconds interval (may use combinations
           of SECOND, MINUTE, HOUR, DAY, WEEK, MONTH, or YEAR constants)
           for major ticks (ticks with labels)

           minor (number): same for minor ticks (shorter ticks without labels)

           start (number, string, or `None`): a time to set the offset
           of the tick-marks (use `t0` if `None`)

        Behavior:
           A "month" is taken to be exactly 31 days and a "year" is
           taken to be exactly 365 days.  Week markers will only line
           up with month markers at `start`.
        """

        if isinstance(start, basestring): start = fromtimestring(start)
        return utilities.timeticks(major, minor, self.outformat, self._subseconds, self._t0, start)

######################################################### Colorfield

class ColorField(Frame):
    _not_frameargs = ["values", "zmin", "zmax", "zlog", "components", "tocolor", "smooth"]

    def __init__(self, xbins, xmin, xmax, ybins, ymin, ymax, zmin=Auto, zmax=Auto, zlog=False, components=1, tocolor=color.gradients["rainbow"], smooth=False, **frameargs):
        self.xmin, self.xmax, self.ymin, self.ymax, self.zmin, self.zmax, self.tocolor, self.smooth = xmin, xmax, ymin, ymax, zmin, zmax, tocolor, smooth
        if components == 1:
            self.values = numpy.zeros((xbins, ybins), numpy.float)
        else:
            self.values = numpy.zeros((xbins, ybins, components), numpy.float)
        Frame.__init__(self, **frameargs)

    def __repr__(self):
        if self.components() == 1:
            return "<ColorField [%d][%d] x=(%g, %g) y=(%g, %g) at 0x%x>" % (self.xbins(), self.ybins(), self.xmin, self.xmax, self.ymin, self.ymax, id(self))
        else:
            return "<ColorField [%d][%d][%d] x=(%g, %g) y=(%g, %g) at 0x%x>" % (self.xbins(), self.ybins(), self.components(), self.xmin, self.xmax, self.ymin, self.ymax, id(self))

    def xbins(self):
        return self.values.shape[0]

    def ybins(self):
        return self.values.shape[1]

    def components(self):
        if len(self.values.shape) > 2:
            return self.values.shape[2]
        else:
            return 1

    def index(self, x, y):
        xindex = int(math.floor((x - self.xmin)*self.values.shape[0]/(self.xmax - self.xmin)))
        if not (0 <= xindex < self.values.shape[0]):
            raise ContainerException, "The value %g is not between xmin=%g and xmax=%g." % (x, self.xmin, self.xmax)

        yindex = int(math.floor((y - self.ymin)*self.values.shape[1]/(self.ymax - self.ymin)))
        if not (0 <= yindex < self.values.shape[1]):
            raise ContainerException, "The value %g is not between ymin=%g and ymax=%g." % (y, self.ymin, self.ymax)

        return xindex, yindex

    def center(self, i, j):
        x = (i + 0.5)*(self.xmax - self.xmin)/float(self.values.shape[0]) + self.xmin
        if not (self.xmin <= x <= self.xmax):
            raise ContainerException, "The index %d is not between 0 and xbins=%d" % (i, self.values.shape[0])

        y = (j + 0.5)*(self.ymax - self.ymin)/float(self.values.shape[1]) + self.ymin
        if not (self.ymin <= y <= self.ymax):
            raise ContainerException, "The index %d is not between 0 and ybins=%d" % (j, self.values.shape[1])

        return x, y

    def map(self, func):
        ybins = self.ybins()
        for i in xrange(self.xbins()):
            for j in xrange(ybins):
                self.values[i,j] = func(*self.center(i, j))

    def remap(self, func):
        ybins = self.ybins()
        for i in xrange(self.xbins()):
            for j in xrange(ybins):
                self.values[i,j] = func(*self.center(i, j), old=self.values[i,j])

    def zranges(self):
        ybins = self.ybins()
        components = self.components()
        if components == 1:
            zmin, zmax = None, None
        else:
            zmin, zmax = [None]*self.components(), [None]*self.components()

        for i in xrange(self.xbins()):
            for j in xrange(ybins):
                if components == 1:
                    if zmin is None or self.values[i,j] < zmin: zmin = self.values[i,j]
                    if zmax is None or self.values[i,j] > zmax: zmax = self.values[i,j]
                else:
                    for k in xrange(components):
                        if zmin[k] is None or self.values[i,j,k] < zmin[k]: zmin[k] = self.values[i,j,k]
                        if zmax[k] is None or self.values[i,j,k] > zmax[k]: zmax[k] = self.values[i,j,k]
        return zmin, zmax

    def ranges(self, xlog=False, ylog=False):
        """Return a data-space bounding box as `xmin, ymin, xmax, ymax`.

        Arguments:
           xlog (bool): requesting a logarithmic x axis (negative
           and zero-valued contents are ignored)

           ylog (bool): requesting a logarithmic y axis
        """
        return self.xmin, self.ymin, self.xmax, self.ymax

######################################################### Subregions of the plane

class Region(Frame):
    """Represents an enclosed region of the plane.

    Signature::

       Region([command1[, command2[, command3[, ...]]]], [linewidth=width,] [linestyle=style,] [linecolor=color,] [fillcolor=color,] [**frameargs])

    Arguments:
       commands (list of RegionCommands): a list of `MoveTo`, `EdgeTo`,
       or `ClosePolygon` commands; commands have the same structure as
       SVG path data, but may have infinite arguments (to enclose an
       unbounded region of the plane)

       fillcolor (string or color): fill color of the enclosed region

       `**frameargs`: keyword arguments for the coordinate frame

    Public members:
       `commands`, `fillcolor`, and frame arguments.
    """

    _not_frameargs = ["commands", "fillcolor"]

    def __init__(self, *commands, **kwds):
        self.commands = list(commands)

        params = {"fillcolor": "lightblue"}
        params.update(kwds)
        Frame.__init__(self, **params)

    def __repr__(self):
        return "<Region (%s commands) at 0x%x>" % (len(self.commands), id(self))

    def ranges(self, xlog=False, ylog=False):
        """Return a data-space bounding box as `xmin, ymin, xmax, ymax`.

        Arguments:
           xlog (bool): requesting a logarithmic x axis (negative
           and zero-valued contents are ignored)

           ylog (bool): requesting a logarithmic y axis
        """

        xmin, ymin, xmax, ymax = None, None, None, None
        
        for command in self.commands:
            if not isinstance(command, RegionCommand):
                raise ContainerException, "Commands passed to Region must all be RegionCommands (MoveTo, EdgeTo, ClosePolygon)"
            for x, y in command.points():
                if not isinstance(x, mathtools.InfiniteType) and not xlog or x > 0.:
                    if xmin is None or x < xmin: xmin = x
                    if xmax is None or x > xmax: xmax = x
                if not isinstance(y, mathtools.InfiniteType) and not ylog or y > 0.:
                    if ymin is None or y < ymin: ymin = y
                    if ymax is None or y > ymax: ymax = y

        if xmin is None:
            if xlog:
                xmin, xmax = 0.1, 1.
            else:
                xmin, xmax = 0., 1.
        if ymin is None:
            if ylog:
                ymin, ymax = 0.1, 1.
            else:
                ymin, ymax = 0., 1.

        if xmin == xmax:
            if xlog:
                xmin, xmax = xmin/2., xmax*2.
            else:
                xmin, xmax = xmin - 0.5, xmax + 0.5

        if ymin == ymax:
            if ylog:
                ymin, ymax = ymin/2., ymax*2.
            else:
                ymin, ymax = ymin - 0.5, ymax + 0.5

        return xmin, ymin, xmax, ymax

class RegionCommand:
    def points(self): return []

class MoveTo(RegionCommand):
    """Represents a directive to move the pen to a specified point."""

    def __init__(self, x, y):
        self.x, self.y = x, y
    def __repr__(self):
        if isinstance(self.x, (numbers.Number, numpy.number)): x = "%g" % self.x
        else: x = repr(self.x)
        if isinstance(self.y, (numbers.Number, numpy.number)): y = "%g" % self.y
        else: y = repr(self.y)
        return "MoveTo(%s, %s)" % (x, y)
    def points(self): return [(self.x, self.y)]

class EdgeTo(RegionCommand):
    """Represents a directive to draw an edge to a specified point."""

    def __init__(self, x, y):
        self.x, self.y = x, y
    def __repr__(self):
        if isinstance(self.x, (numbers.Number, numpy.number)): x = "%g" % self.x
        else: x = repr(self.x)
        if isinstance(self.y, (numbers.Number, numpy.number)): y = "%g" % self.y
        else: y = repr(self.y)
        return "EdgeTo(%s, %s)" % (x, y)
    def points(self): return [(self.x, self.y)]

class ClosePolygon(RegionCommand):
    """Represents a directive to close the current polygon."""

    def __repr__(self):
        return "ClosePolygon()"

class RegionMap(Frame):
    _not_frameargs = ["xbins", "ybins", "categories", "categorizer", "colors", "bordercolor"]

    def __init__(self, xbins, xmin, xmax, ybins, ymin, ymax, categories, categorizer, colors=Auto, bordercolor=None, **frameargs):
        self.xbins, self.xmin, self.xmax, self.ybins, self.ymin, self.ymax, self.categories, self.categorizer, self.colors, self.bordercolor = xbins, xmin, xmax, ybins, ymin, ymax, categories, categorizer, colors, bordercolor
        Frame.__init__(self, **frameargs)

    def __repr__(self):
        return "<RegionMap [%d][%d] x=(%g, %g) y=(%g, %g) at 0x%x>" % (self.xbins, self.ybins, self.xmin, self.xmax, self.ymin, self.ymax, id(self))

    def index(self, x, y):
        xindex = int(math.floor((x - self.xmin)*self.xbins/(self.xmax - self.xmin)))
        if not (0 <= xindex < self.xbins):
            raise ContainerException, "The value %g is not between xmin=%g and xmax=%g." % (x, self.xmin, self.xmax)

        yindex = int(math.floor((y - self.ymin)*self.ybins/(self.ymax - self.ymin)))
        if not (0 <= yindex < self.ybins):
            raise ContainerException, "The value %g is not between ymin=%g and ymax=%g." % (y, self.ymin, self.ymax)

        return xindex, yindex

    def center(self, i, j):
        x = (i + 0.5)*(self.xmax - self.xmin)/float(self.xbins) + self.xmin
        if not (self.xmin <= x <= self.xmax):
            raise ContainerException, "The index %d is not between 0 and xbins=%d" % (i, self.xbins)

        y = (j + 0.5)*(self.ymax - self.ymin)/float(self.ybins) + self.ymin
        if not (self.ymin <= y <= self.ymax):
            raise ContainerException, "The index %d is not between 0 and ybins=%d" % (j, self.ybins)

        return x, y

    def ranges(self, xlog=False, ylog=False):
        """Return a data-space bounding box as `xmin, ymin, xmax, ymax`.

        Arguments:
           xlog (bool): requesting a logarithmic x axis (negative
           and zero-valued contents are ignored)

           ylog (bool): requesting a logarithmic y axis
        """
        return self.xmin, self.ymin, self.xmax, self.ymax

    def _compile(self):
        if isinstance(self.categorizer, numpy.ndarray) or callable(self.categorizer):
            self._categorizer = self.categorizer
        else:
            self._categorizer = eval("lambda x, y: (%s)" % self.categorizer)

    def _prepare(self, xmin=None, ymin=None, xmax=None, ymax=None, xlog=False, ylog=False):
        self._compile()

        if self.colors is Auto:
            cols = color.lightseries(len(self.categories), alternating=False)
        else:
            cols = self.colors

        self._colors = {}
        ints = {}
        counter = 0
        for category, col in zip(self.categories, cols):
            self._colors[category] = color.RGB(col).ints()
            ints[category] = counter
            counter += 1

        if self.bordercolor is not None:
            asarray = numpy.zeros((self.xbins, self.ybins), dtype=numpy.int)

        self._values = []
        for i in xrange(self.xbins):
            row = []
            for j in xrange(self.ybins):
                if isinstance(self._categorizer, numpy.ndarray):
                    category = self.categories[self._categorizer[i,j]]
                else:
                    category = self._categorizer(*self.center(i, j))
                row.append(self._colors[category])
                if self.bordercolor is not None:
                    asarray[i,j] = ints[category]
            self._values.append(row)

        if self.bordercolor is not None:
            roll1 = numpy.roll(asarray, 1, 0)
            roll2 = numpy.roll(asarray, -1, 0)
            roll3 = numpy.roll(asarray, 1, 1)
            roll4 = numpy.roll(asarray, -1, 1)

            mask = numpy.equal(asarray, roll1)
            numpy.logical_and(mask, numpy.equal(asarray, roll2), mask)
            numpy.logical_and(mask, numpy.equal(asarray, roll3), mask)
            numpy.logical_and(mask, numpy.equal(asarray, roll4), mask)

            thecolor = color.RGB(self.bordercolor).ints()
            for i in xrange(self.xbins):
                for j in xrange(self.ybins):
                    if not mask[i,j]:
                        self._values[i][j] = thecolor

######################################################### Curves and functions

class Curve(Frame):
    """Represents a parameterized function.

    Arguments:
       func (function or string): the function to plot; if callable,
       it should take one argument and accept parameters as keywords;
       if a string, it should be valid Python code, accepting a
       variable name specified by `var`, parameter names to be passed
       through `parameters`, and any function in the `math` library
       (`cmath` if complex).

       varmin, varmax (numbers or `Auto`): nominal range of function input

       parameters (dict): parameter name, value pairs to be passed
       before plotting

       var (string): name of the input variable (string `func` only)

       namespace (module, dict, or `None`): names to be used by the
       function; for example::

          import scipy.special # (sudo apt-get install python-scipy)
          curve = Curve("jn(4, x)", namespace=scipy.special)
          view(curve, xmin=-20., xmax=20.)

       form (built-in constant): if Curve.FUNCTION, `func` is expected
       to input x and output y; if Curve.PARAMETRIC, `func` is expected
       to input t and output the tuple (x, y); if Curve.COMPLEX, `func` 
       is expected to output a 2-D point as a complex number

       samples (number or `Auto`): number of sample points or `Auto`
       for dynamic sampling (_not yet copied over from SVGFig!_)

       linewidth (float): scale factor to resize line width

       linestyle (tuple or string): "solid", "dashed", "dotted", or a
       tuple of numbers representing a dash-pattern

       linecolor (string, color, or `None`): color specification for
       the curve

       `**frameargs`: keyword arguments for the coordinate frame

    Public members:
       `horiz`, `vert`, `linewidth`, `linestyle`, `linecolor`, and
       frame arguments.

    Examples::

       >>> c = Curve("sin(x + delta)", 0, 6.28)
       >>> c
       <Curve x -> sin(x + delta) from 0 to 6.28>
       >>> c(0., delta=0.1)
       0.099833416646828155

       >>> c.parameters = {"delta": 0.1}
       >>> view(c)

       >>> def f(x, delta=0.):
       ...     return math.sin(x + delta)
       ... 
       >>> c = Curve(f, 0, 6.28)
       >>> c
       <Curve f from 0 to 6.28>
       >>> c(0., delta=0.1)
       0.099833416646828155

    """

    _not_frameargs = ["func", "varmin", "varmax", "parameters", "var", "namespace", "form", "samples", "linewidth", "linestyle", "linecolor", "FUNCTION", "PARAMETRIC", "COMPLEX"]

    class CurveType:
        def __init__(self, name): self.name = "Curve." + name
        def __repr__(self): return self.name

    FUNCTION = CurveType("FUNCTION")
    PARAMETRIC = CurveType("PARAMETRIC")
    COMPLEX = CurveType("COMPLEX")

    def __init__(self, func, varmin=Auto, varmax=Auto, parameters={}, var="x", namespace=None, form=FUNCTION, samples=1000, linewidth=1., linestyle="solid", linecolor="black", **frameargs):
        self.func, self.varmin, self.varmax, self.parameters, self.var, self.namespace, self.form, self.samples, self.linewidth, self.linestyle, self.linecolor = func, varmin, varmax, parameters, var, namespace, form, samples, linewidth, linestyle, linecolor
        Frame.__init__(self, **frameargs)

    def _compile(self, parameters):
        if callable(self.func):
            self._func = lambda t: self.func(t, **parameters)
            try:
                self._func.func_name = self.func.func_name
            except AttributeError:
                self._func.func_name = "built-in"
        else:
            if self.form is self.COMPLEX: g = dict(cmath.__dict__)
            else: g = dict(math.__dict__)

            # missing these important functions
            g["erf"] = mathtools.erf
            g["erfc"] = mathtools.erfc

            if self.namespace is not None:
                if isinstance(self.namespace, dict):
                    g.update(self.namespace)
                else:
                    g.update(self.namespace.__dict__)

            g.update(parameters)
            self._func = eval("lambda (%s): (%s)" % (self.var, self.func), g)
            self._func.func_name = "%s -> %s" % (self.var, self.func)

    def __repr__(self):
        if callable(self.func):
            try:
                func_name = self.func.func_name
            except AttributeError:
                func_name = "built-in"
        else:
            func_name = "%s -> %s" % (self.var, self.func)
        return "<Curve %s>" % func_name

    def __call__(self, values, **parameters):
        """Call the function for a set of values and parameters.

        Arguments:
           values (number or list of numbers): input(s) to the function

           parameters (keyword arguments): parameter values for this
           set of evaluations
        """

        self._compile(parameters)

        if isinstance(values, (numbers.Number, numpy.number)):
            singleton = True
            values = [values]
        else:
            singleton = False

        if self.form is self.FUNCTION:
            output = numpy.empty(len(values), dtype=numpy.float)
        elif self.form is self.PARAMETRIC:
            output = numpy.empty((len(values), 2), dtype=numpy.float)
        elif self.form is self.COMPLEX:
            output = numpy.empty(len(values), dtype=numpy.complex)
        else:
            raise ContainerException, "Curve.form must be one of Curve.FUNCTION, Curve.PARAMETRIC, or Curve.COMPLEX."

        try:
            for i, value in enumerate(values):
                output[i] = self._func(value)
        except NameError, err:
            raise NameError, "%s: are the Curve's parameters missing (or namespace not set)?" % err

        if singleton: output = output[0]
        return output

    def derivative(self, values, epsilon=mathtools.epsilon, **parameters):
        """Numerically calculate derivative for a set of values and parameters.

        Arguments:
           values (number or list of numbers): input(s) to the function

           parameters (keyword arguments): parameter values for this
           set of evaluations
        """

        self._compile(parameters)

        if isinstance(values, (numbers.Number, numpy.number)):
            singleton = True
            values = [values]
        else:
            singleton = False

        if self.form is self.FUNCTION:
            output = numpy.empty(len(values), dtype=numpy.float)
        elif self.form is self.PARAMETRIC:
            output = numpy.empty((len(values), 2), dtype=numpy.float)
        elif self.form is self.COMPLEX:
            raise ContainerException, "Curve.derivative not implemented for COMPLEX functions."
        else:
            raise ContainerException, "Curve.form must be one of Curve.FUNCTION, Curve.PARAMETRIC, or Curve.COMPLEX."

        for i, value in enumerate(values):
            up = self._func(value + mathtools.epsilon)
            down = self._func(value - mathtools.epsilon)
            output[i] = (up - down)/(2. * mathtools.epsilon)

        if singleton: output = output[0]
        return output
    
    def scatter(self, low, high, samples=Auto, xlog=False, **parameters):
        """Create a `Scatter` object from the evaluated function.

        Arguments:
           samples (number or `Auto`): number of sample points

           low, high (numbers): domain to sample

           xlog (bool): if `form` == `FUNCTION`, distribute the sample
           points logarithmically

           parameters (keyword arguments): parameter values for this
           set of evaluations
        """

        tmp = self.parameters
        tmp.update(parameters)
        parameters = tmp

        if samples is Auto: samples = self.samples
        
        if self.form is self.FUNCTION:
            points = numpy.empty((samples, 2), dtype=numpy.float)

            if xlog:
                step = (math.log(high) - math.log(low))/(samples - 1.)
                points[:,0] = numpy.exp(numpy.arange(math.log(low), math.log(high) + 0.5*step, step))
            else:
                step = (high - low)/(samples - 1.)
                points[:,0] = numpy.arange(low, high + 0.5*step, step)

            points[:,1] = self(points[:,0], **parameters)

        elif self.form is self.PARAMETRIC:
            step = (high - low)/(samples - 1.)
            points = self(numpy.arange(low, high + 0.5*step, step), **parameters)

        elif self.form is self.COMPLEX:
            step = (high - low)/(samples - 1.)
            tmp = self(numpy.arange(low, high + 0.5*step, step), **parameters)

            points = numpy.empty((samples, 2), dtype=numpy.float)
            for i, value in enumerate(tmp):
                points[i] = value.real, value.imag

        else: raise ContainerException, "Curve.form must be one of Curve.FUNCTION, Curve.PARAMETRIC, or Curve.COMPLEX."

        return Scatter(points, ("x", "y"), limit=None, calcrange=utilities.calcrange, connector="unsorted", marker=None, lines=True, linewidth=self.linewidth, linestyle=self.linestyle, linecolor=self.linecolor, **self._frameargs())

    def _prepare(self, xmin=None, ymin=None, xmax=None, ymax=None, xlog=False, ylog=False):
        if xmin in (None, Auto) and xmax in (None, Auto):
            if xlog:
                xmin, xmax = 0.1, 1.
            else:
                xmin, xmax = 0., 1.
        elif xmin is None:
            if xlog:
                xmin = xmax / 2.
            else:
                xmin = xmax - 1.
        elif xmax is None:
            if xlog:
                xmax = xmin * 2.
            else:
                xmax = xmin + 1.

        if self.form is self.FUNCTION:
            if self.varmin is not Auto: xmin = self.varmin
            if self.varmax is not Auto: xmax = self.varmax
            self._scatter = self.scatter(xmin, xmax, self.samples, xlog, **self.parameters)
        else:
            varmin = self.varmin
            varmax = self.varmax
            if varmin is Auto: varmin = 0.
            if varmax is Auto: varmax = 1.
            self._scatter = self.scatter(varmin, varmax, self.samples, xlog, **self.parameters)

    def ranges(self, xlog=False, ylog=False):
        """Return a data-space bounding box as `xmin, ymin, xmax, ymax`.

        Arguments:
           xlog (bool): requesting a logarithmic x axis (negative
           and zero-valued contents are ignored)

           ylog (bool): requesting a logarithmic y axis
        """

        if getattr(self, "_scatter", None) is not None:
            return self._scatter.ranges(xlog=xlog, ylog=ylog)
        else:
            self._prepare(xlog=xlog)
            output = self._scatter.ranges(xlog=xlog, ylog=ylog)
            self._scatter = None
            return output

    def objective(self, data, parnames, method=Auto, exclude=Auto, centroids=False):
        """Return an objective function whose minimum represents a
best fit to a given dataset.

        Arguments:
           data (`Histogram` or `Scatter`): the data to fit

           parnames (list of strings): names of the parameters

           method (function or `Auto`): a function that will be called
           for each data point to calculate the final value of the
           objective function; examples:

           `lambda f, x, y: (f - y)**2`  chi^2 for data without uncertainties

           `lambda f, x, y, ey: (f - y)**2/ey**2`  chi^2 with uncertainties

           If `method` is `Auto`, an appropriate chi^2 function will
           be used.

           exclude (function, `Auto`, or `None`): a function that will
           be called for each data point to determine whether to
           exclude the point; `Auto` excludes only zero values and
           `None` excludes nothing

           centroids (bool): use centroids of histogram, rather than
           centers
        """

        if isinstance(data, Histogram):
            if isinstance(data, HistogramCategorical):
                raise ContainerException, "A fit to a categorical histogram is not meaningful."

            if exclude is Auto and method is Auto:
                exclude = lambda x, y: y == 0.
            else:
                exclude = lambda x, y: False
            self._exclude = exclude

            if method is Auto:
                method = lambda f, x, y: (f - y)**2/abs(y)

            values = numpy.empty((len(data.bins), 2), dtype=numpy.float)
            if centroids: values[:,0] = data.centroids()
            else: values[:,0] = data.centers()
            values[:,1] = data.values

            return eval("lambda %s: sum([method(f, x, y) for f, (x, y) in itertools.izip(curve(values[:,0], **{%s}), values) if not exclude(x, y)])" % (", ".join(parnames), ", ".join(["\"%s\": %s" % (x, x) for x in parnames])), {"method": method, "itertools": itertools, "curve": self, "values": values, "exclude": exclude})

        elif isinstance(data, Scatter):
            if "ey" in data.sig and "eyl" in data.sig:
                if method is Auto:
                    method = lambda f, x, y, ey, eyl: ((f - y)**2/eyl**2 if f < y else (f - y)**2/ey**2)
                if exclude is Auto:
                    exclude = lambda x, y, ey, eyl: eyl == 0. or ey == 0.
                elif exclude is None:
                    exclude = lambda x, y, ey, eyl: False

            elif "ey" in data.sig:
                if method is Auto:
                    method = lambda f, x, y, ey: (f - y)**2/ey**2
                if exclude is Auto:
                    exclude = lambda x, y, ey: ey == 0.
                elif exclude is None:
                    exclude = lambda x, y, ey: False

            else:
                if method is Auto:
                    method = lambda f, x, y: (f - y)**2
                if exclude is Auto or exclude is None:
                    exclude = lambda x, y: False

            self._exclude = exclude

            index = data.index()
            if "ey" in data.sig and "eyl" in data.sig:
                values = numpy.empty((len(data.values), 4))
                values[:,0] = data.values[:,index["x"]]
                values[:,1] = data.values[:,index["y"]]
                values[:,2] = data.values[:,index["ey"]]
                values[:,3] = data.values[:,index["eyl"]]
                return eval("lambda %s: sum([method(f, x, y, ey, eyl) for f, (x, y, ey, eyl) in itertools.izip(curve(values[:,0], **{%s}), values) if not exclude(x, y, ey, eyl)])" % (", ".join(parnames), ", ".join(["\"%s\": %s" % (x, x) for x in parnames])), {"method": method, "itertools": itertools, "curve": self, "values": values, "exclude": exclude})

            elif "ey" in data.sig:
                values = numpy.empty((len(data.values), 3))
                values[:,0] = data.values[:,index["x"]]
                values[:,1] = data.values[:,index["y"]]
                values[:,2] = data.values[:,index["ey"]]
                return eval("lambda %s: sum([method(f, x, y, ey) for f, (x, y, ey) in itertools.izip(curve(values[:,0], **{%s}), values) if not exclude(x, y, ey)])" % (", ".join(parnames), ", ".join(["\"%s\": %s" % (x, x) for x in parnames])), {"method": method, "itertools": itertools, "curve": self, "values": values, "exclude": exclude})

            else:
                values = numpy.empty((len(data.values), 2))
                values[:,0] = data.values[:,index["x"]]
                values[:,1] = data.values[:,index["y"]]
                return eval("lambda %s: sum([method(f, x, y) for f, (x, y) in itertools.izip(curve(values[:,0], **{%s}), values) if not exclude(x, y)])" % (", ".join(parnames), ", ".join(["\"%s\": %s" % (x, x) for x in parnames])), {"method": method, "itertools": itertools, "curve": self, "values": values, "exclude": exclude})

        else:
            raise ContainerException, "Data for Curve.objective must be a Histogram or a Scatter plot."

    def fit(self, data, parameters=Auto, sequence=[("migrad",)], method=Auto, exclude=Auto, centroids=False, **fitter_arguments):
        """Fit this curve to a given dataset, updating its `parameters` and creating a `minimizer` member.

        Arguments:
           data (`Histogram` or `Scatter`): the data to fit

           parameters (dict of strings -> values): the initial
           parameters for the fit

           sequence (list of (string, arg, arg)): sequence of Minuit
           commands to call, with optional arguments

           method (function or `Auto`): a function that will be called
           for each data point to calculate the final value of the
           objective function; examples:

           `lambda f, x, y: (f - y)**2`  chi^2 for data without uncertainties

           `lambda f, x, y, ey: (f - y)**2/ey**2`  chi^2 with uncertainties

           If `method` is `Auto`, an appropriate chi^2 function will
           be used.

           exclude (function, `Auto`, or `None`): a function that will
           be called for each data point to determine whether to
           exclude the point; `Auto` excludes only zero values and
           `None` excludes nothing

           centroids (bool): use centroids of histogram, rather than
           centers

        Keyword arguments:

           Keyword arguments will be passed to the Minuit object as member data.
        """

        if parameters is Auto: parameters = self.parameters

        self.minimizer = minuit.Minuit(self.objective(data, parameters.keys(), method=method, exclude=exclude, centroids=centroids))
        for name, value in fitter_arguments.items():
            exec("self.minimizer.%s = %s" % (name, str(value)))
        self.minimizer.values = parameters

        # this block is just to set ndf (with all exclusions applied)
        ndf = 0
        if isinstance(data, Histogram):
            if isinstance(data, HistogramCategorical):
                raise ContainerException, "A fit to a categorical histogram is not meaningful."
            values = numpy.empty((len(data.bins), 2), dtype=numpy.float)
            if centroids: values[:,0] = data.centroids()
            else: values[:,0] = data.centers()
            values[:,1] = data.values
            for x, y in values:
                if not self._exclude(x, y):
                    ndf += 1
        elif isinstance(data, Scatter):
            index = data.index()
            if "ey" in data.sig and "eyl" in data.sig:
                values = numpy.empty((len(data.values), 4))
                values[:,0] = data.values[:,index["x"]]
                values[:,1] = data.values[:,index["y"]]
                values[:,2] = data.values[:,index["ey"]]
                values[:,3] = data.values[:,index["eyl"]]
                for x, y, ey, eyl in values:
                    if not self._exclude(x, y, ey, eyl):
                        ndf += 1
            elif "ey" in data.sig:
                values = numpy.empty((len(data.values), 3))
                values[:,0] = data.values[:,index["x"]]
                values[:,1] = data.values[:,index["y"]]
                values[:,2] = data.values[:,index["ey"]]
                for x, y, ey in values:
                    if not self._exclude(x, y, ey):
                        ndf += 1
            else:
                values = numpy.empty((len(data.values), 2))
                values[:,0] = data.values[:,index["x"]]
                values[:,1] = data.values[:,index["y"]]
                for x, y in values:
                    if not self._exclude(x, y):
                        ndf += 1
        else:
            raise ContainerException, "Data for Curve.objective must be a Histogram or a Scatter plot."

        ndf -= len(parameters)
        # end block to set ndf

        try:
            for command in sequence:
                name = command[0]
                args = list(command[1:])
                for i in range(len(args)):
                    if isinstance(args[i], basestring): args[i] = "\"%s\"" % args[i]
                    else: args[i] = str(args[i])
                eval("self.minimizer.%s(%s)" % (name, ", ".join(args)))
        except Exception as tmp:
            self.parameters = self.minimizer.values
            self.chi2 = self.minimizer.fval
            self.ndf = ndf
            self.normalizedChi2 = (self.minimizer.fval / float(self.ndf) if self.ndf > 0 else -1.)
            raise tmp

        self.parameters = self.minimizer.values
        self.chi2 = self.minimizer.fval
        self.ndf = ndf
        self.normalizedChi2 = (self.minimizer.fval / float(self.ndf) if self.ndf > 0 else -1.)

    # reporting results after fitting

    def round_errpair(self, parname, n=2):
        """Round a parameter and its uncertainty to n significant figures in
        the uncertainty (default is two)."""

        if getattr(self, "minimizer", None) is None:
            raise ContainerException, "Curve.round_errpair can only be called after fitting."

        return mathtools.round_errpair(self.minimizer.values[parname], self.minimizer.errors[parname], n=n)
        
    def str_errpair(self, parname, n=2):
        """Round a number and its uncertainty to n significant figures in the
        uncertainty (default is two) and return the result as a string."""

        if getattr(self, "minimizer", None) is None:
            raise ContainerException, "Curve.str_errpair can only be called after fitting."

        return mathtools.str_errpair(self.minimizer.values[parname], self.minimizer.errors[parname], n=n)

    def unicode_errpair(self, parname, n=2):
        """Round a number and its uncertainty to n significant figures in the
uncertainty (default is two) and return the result joined by a unicode
plus-minus sign."""

        if getattr(self, "minimizer", None) is None:
            raise ContainerException, "Curve.unicode_errpair can only be called after fitting."

        return mathtools.unicode_errpair(self.minimizer.values[parname], self.minimizer.errors[parname], n=n)

    def expr(self, varrepl=None, sigfigs=2):
        if callable(self.func):
            raise ContainerException, "Curve.expr only works for string-based functions."

        if getattr(self, "minimizer", None) is None:
            raise ContainerException, "Curve.expr can only be called after fitting."
        
        output = self.func[:]
        for name, value in self.minimizer.values.items():
            if sigfigs is None:
                value = ("%g" % value)
            else:
                value = mathtools.str_sigfigs(value, sigfigs)

            output = re.sub(r"\b%s\b" % name, value, output)

        if varrepl is not None:
            output = re.sub(r"\b%s\b" % self.var, varrepl, output)

        return output

######################################################### Grids, horiz/vert lines, annotations

class Line(Frame):
    """Represents a line drawn between two points (one of which may be at infinity).

    Arguments:
       x1, y1 (numbers): a point; either coordinate can be Infinity or
       multiples of Infinity

       x2, y2 (numbers): another point; either coordinate can be
       Infinity or multiples of Infinity

       linewidth (float): scale factor to resize line width

       linestyle (tuple or string): "solid", "dashed", "dotted", or a
       tuple of numbers representing a dash-pattern

       linecolor (string or color): color specification for grid line(s)

       `**frameargs`: keyword arguments for the coordinate frame

    Public members:
       `x1`, `y1`, `x2`, `y2`, `linewidth`, `linestyle`, `linecolor`,
       and frame arguments.
    """

    _not_frameargs = ["x1", "y1", "x2", "y2", "linewidth", "linestyle", "linecolor"]

    def __init__(self, x1, y1, x2, y2, linewidth=1., linestyle="solid", linecolor="black", **frameargs):
        self.x1, self.y1, self.x2, self.y2, self.linewidth, self.linestyle, self.linecolor = x1, y1, x2, y2, linewidth, linestyle, linecolor
        Frame.__init__(self, **frameargs)

    def __repr__(self):
        if isinstance(self.x1, mathtools.InfiniteType): x1 = repr(self.x1)
        else: x1 = "%g" % self.x1

        if isinstance(self.y1, mathtools.InfiniteType): y1 = repr(self.y1)
        else: y1 = "%g" % self.y1

        if isinstance(self.x2, mathtools.InfiniteType): x2 = repr(self.x2)
        else: x2 = "%g" % self.x2

        if isinstance(self.y2, mathtools.InfiniteType): y2 = repr(self.y2)
        else: y2 = "%g" % self.y2

        return "<Line %s %s %s %s at 0x%x>" % (x1, y1, x2, y2, id(self))

    def ranges(self, xlog=False, ylog=False):
        if (isinstance(self.x1, mathtools.InfiniteType) or isinstance(self.y1, mathtools.InfiniteType) or (getattr(self, "xlog", False) and self.x1 <= 0.) or (getattr(self, "ylog", False) and self.y1 <= 0.)) and \
           (isinstance(self.x2, mathtools.InfiniteType) or isinstance(self.y2, mathtools.InfiniteType) or (getattr(self, "xlog", False) and self.x2 <= 0.) or (getattr(self, "ylog", False) and self.y2 <= 0.)):
            if getattr(self, "xlog", False):
                xmin, xmax = 0.1, 1.
            else:
                xmin, xmax = 0., 1.
            if getattr(self, "ylog", False):
                ymin, ymax = 0.1, 1.
            else:
                ymin, ymax = 0., 1.

            return xmin, ymin, xmax, ymax

        elif isinstance(self.x1, mathtools.InfiniteType) or isinstance(self.y1, mathtools.InfiniteType) or (getattr(self, "xlog", False) and self.x1 <= 0.) or (getattr(self, "ylog", False) and self.y1 <= 0.):
            singlepoint = (self.x2, self.y2)

        elif isinstance(self.x2, mathtools.InfiniteType) or isinstance(self.y2, mathtools.InfiniteType) or (getattr(self, "xlog", False) and self.x2 <= 0.) or (getattr(self, "ylog", False) and self.y2 <= 0.):
            singlepoint = (self.x1, self.y1)
        
        else:
            return min(self.x1, self.x2), min(self.y1, self.y2), max(self.x1, self.x2), max(self.y1, self.y2)

        # handle singlepoint
        if getattr(self, "xlog", False):
            xmin, xmax = singlepoint[0]/2., singlepoint[0]*2.
        else:
            xmin, xmax = singlepoint[0] - 1., singlepoint[0] + 1.
        if getattr(self, "ylog", False):
            ymin, ymax = singlepoint[1]/2., singlepoint[1]*2.
        else:
            ymin, ymax = singlepoint[1] - 1., singlepoint[1] + 1.

        return xmin, ymin, xmax, ymax

class Grid(Frame):
    """Represents one or more horizontal/vertical lines or a whole grid.

    Arguments:
       horiz (list of numbers, function, or `None`): a list of values
       at which to draw horizontal lines, a function `f(a, b)` taking
       an interval and providing such a list, or `None` for no
       horizontal lines.

       vert (list of numbers, function, or `None`): same for vertical
       lines

       linewidth (float): scale factor to resize line width

       linestyle (tuple or string): "solid", "dashed", "dotted", or a
       tuple of numbers representing a dash-pattern

       linecolor (string or color): color specification for grid line(s)

       `**frameargs`: keyword arguments for the coordinate frame

    Public members:
       `horiz`, `vert`, `linewidth`, `linestyle`, `linecolor`, and
       frame arguments.

    Considerations:
       The `regular` utility provides functions suitable for `horiz`
       and `vert`.
    """

    _not_frameargs = ["horiz", "vert", "linewidth", "linestyle", "linecolor"]

    def __init__(self, horiz=None, vert=None, linewidth=1., linestyle="dotted", linecolor="grey", **frameargs):
        self.horiz, self.vert, self.linewidth, self.linestyle, self.linecolor = horiz, vert, linewidth, linestyle, linecolor
        Frame.__init__(self, **frameargs)

    def __repr__(self):
        return "<Grid %s %s at 0x%x>" % (repr(self.horiz), repr(self.vert), id(self))

    def _prepare(self, xmin=None, ymin=None, xmax=None, ymax=None, xlog=None, ylog=None):
        try:
            self._horiz = []
            for i in self.horiz:
                self._horiz.append(i)
        except TypeError:
            if callable(self.horiz):
                try:
                    self._horiz = self.horiz(ymin, ymax)
                except TypeError:
                    raise ContainerException, "If Grid.horiz is a function, it must take two endpoints and return a list of values"
            elif self.horiz is None:
                self._horiz = []
            else:
                raise ContainerException, "Grid.horiz must be None, a list of values, or a function returning a list of values (given endpoints)"

        try:
            self._vert = []
            for i in self.vert:
                self._vert.append(i)
        except TypeError:
            if callable(self.vert):
                try:
                    self._vert = self.vert(xmin, xmax)
                except TypeError:
                    raise ContainerException, "If Grid.vert is a function, it must take two endpoints and return a list of values"
            elif self.vert is None:
                self._vert = []
            else:
                raise ContainerException, "Grid.vert must be None, a list of values, or a function returning a list of values (given endpoints)"

######################################################### User-defined plot legend

class Legend(Frame):
    """Represents a table of information to overlay on a plot.

    Arguments:
       fields (list of lists): table data; may include text, numbers,
       and objects with line, fill, or marker styles

       colwid (list of numbers): column widths as fractions of the
       whole width (minus padding); e.g. [0.5, 0.25, 0.25]

       justify (list of "l", "m", "r"): column justification: "l" for
       left, "m" or "c" for middle, and "r" for right

       x, y (numbers): position of the legend box (use with
       `textanchor`) in units of frame width; e.g. (1, 1) is the
       top-right corner, (0, 0) is the bottom-left corner

       width (number): width of the legend box in units of frame width

       height (number or `Auto`): height of the legend box in units of
       frame width or `Auto` to calculate from the number of rows,
       `baselineskip`, and `padding`

       anchor (2-character string): placement of the legend box
       relative to `x`, `y`; first character is "t" for top, "m" or
       "c" for middle, and "b" for bottom, second character is
       "l" for left, "m" or "c" for middle, and "r" for right

       textscale (number): scale factor for text (1 is normal)

       padding (number): extra space between the legend box and its
       contents, as a fraction of the whole SVG document

       baselineskip (number): space to skip between rows of the table,
       as a fraction of the whole SVG document

       linewidth (float): scale factor to resize legend box line width

       linestyle (tuple or string): "solid", "dashed", "dotted", or a
       tuple of numbers representing a dash-pattern

       linecolor (string, color, or `None`): color of the boundary
       around the legend box; no line if `None`

       fillcolor (string, color, or `None`): fill color of the legend
       box; hollow if `None`

       `**frameargs`: keyword arguments for the coordinate frame

    Public members:
       `fields`, `colwid`, `justify`, `x`, `y`, `width`, `height`,
       `anchor`, `textscale`, `padding`, `baselineskip`, `linewidth`,
       `linestyle`, `linecolor`, `fillcolor`, and frame arguments.

    Considerations:
       `Legend` is a drawable data container on its own, not attached
       to any histogram or scatter plot.  To overlay a `Legend` on
       another plot, use the `Overlay` command, and be sure to point
       `Overlay.frame` to the desired plot::

          Overlay(plot, legend, frame=0)

       Legends will always be drawn _above_ the frame (and therefore
       also above all other plots in an overlay).
    """

    _not_frameargs = ["colwid", "justify", "x", "y", "width", "height", "anchor", "textscale", "padding", "baselineskip", "linewidth", "linestyle", "linecolor", "fillcolor"]

    def __init__(self, fields, colwid=Auto, justify="l", x=1., y=1., width=0.4, height=Auto, anchor="tr", textscale=1., padding=0.01, baselineskip=0.035, linewidth=1., linestyle="solid", linecolor="black", fillcolor="white"):
        self.fields, self.colwid, self.justify, self.x, self.y, self.width, self.height, self.anchor, self.textscale, self.padding, self.baselineskip, self.linewidth, self.linestyle, self.linecolor, self.fillcolor = fields, colwid, justify, x, y, width, height, anchor, textscale, padding, baselineskip, linewidth, linestyle, linecolor, fillcolor

    def __repr__(self):
        return "<Legend %dx%d>" % self.dimensions()

    def dimensions(self):
        """Determine the number of rows and columns in `fields`."""

        rows = 1
        columns = 1
        if not isinstance(self.fields, basestring):
            iterable = False
            try:
                iter(self.fields)
                iterable = True
            except TypeError: pass

            if iterable:
                rows -= 1
                for line in self.fields:
                    if not isinstance(line, basestring):
                        length = 0
                        try:
                            for cell in line:
                                length += 1
                        except TypeError: pass

                        if length > columns: columns = length
                    rows += 1
        return rows, columns

    def _prepare(self, xmin=None, ymin=None, xmax=None, ymax=None, xlog=None, ylog=None):
        self._rows, self._columns = self.dimensions()

        # make _fields a rectangular array with None in missing fields
        self._fields = [[None for j in range(self._columns)] for i in range(self._rows)]
        if isinstance(self.fields, basestring):
            self._fields[0][0] = self.fields
        else:
            iterable = False
            try:
                iter(self.fields)
                iterable = True
            except TypeError: pass

            if not iterable:
                self._fields[0][0] = self.fields
            else:
                for i, line in enumerate(self.fields):
                    if isinstance(line, basestring):
                        self._fields[i][0] = line
                    else:
                        lineiterable = False
                        try:
                            iter(line)
                            lineiterable = True
                        except TypeError: pass

                        if not lineiterable:
                            self._fields[i][0] = line
                        else:
                            for j, cell in enumerate(line):
                                self._fields[i][j] = cell

        # take user input if available, fill in what's remaining by evenly splitting the difference
        if self.colwid is Auto:
            self._colwid = [1./self._columns]*self._columns
        else:
            self._colwid = list(self.colwid[:self._columns])
            if len(self._colwid) < self._columns:
                if sum(self._colwid) < 1.:
                    width = (1. - sum(self._colwid)) / (self._columns - len(self._colwid))
                    self._colwid.extend([width]*(self._columns - len(self._colwid)))
                else:
                    # or put in typical values if we have to normalize anyway
                    average = float(sum(self._colwid))/len(self._colwid)
                    self._colwid.extend([average]*(self._columns - len(self._colwid)))

        # normalize: sum of colwid = 1
        total = 1.*sum(self._colwid)
        for i in range(len(self._colwid)):
            self._colwid[i] /= total

        # if we only get one directive, repeat for all self._columns
        if self.justify is Auto or self.justify == "l":
            self._justify = ["l"]*self._columns
        elif self.justify == "m" or self.justify == "c":
            self._justify = ["m"]*self._columns
        elif self.justify == "r":
            self._justify = ["r"]*self._columns
        else:
            # take all user input and fill in whatever's missing with "l"
            self._justify = list(self.justify[:self._columns])
            if len(self._justify) < self._columns:
                self._justify.extend(["l"]*(self._columns - len(self._justify)))

        self._anchor = [None, None]
        if len(self.anchor) == 2:
            if self.anchor[0] == "t": self._anchor[0] = "t"
            if self.anchor[0] in ("m", "c"): self._anchor[0] = "m"
            if self.anchor[0] == "b": self._anchor[0] = "b"
            if self.anchor[1] == "l": self._anchor[1] = "l"
            if self.anchor[1] in ("m", "c"): self._anchor[1] = "m"
            if self.anchor[1] == "r": self._anchor[1] = "r"

            # try the letters backward
            if self._anchor[0] is None or self._anchor[1] is None:
                self._anchor = [None, None]
                if self.anchor[1] == "t": self._anchor[0] = "t"
                if self.anchor[1] in ("m", "c"): self._anchor[0] = "m"
                if self.anchor[1] == "b": self._anchor[0] = "b"
                if self.anchor[0] == "l": self._anchor[1] = "l"
                if self.anchor[0] in ("m", "c"): self._anchor[1] = "m"
                if self.anchor[0] == "r": self._anchor[1] = "r"

        if self._anchor[0] is None or self._anchor[1] is None:
            raise ContainerException, "Legend.anchor not recognized: \"%s\"" % self.anchor

class Style:
    """Represents a line, fill, and marker style, but is not drawable.

    Arguments:
       linewidth (float): scale factor to resize line width

       linestyle (tuple or string): "solid", "dashed", "dotted", or a
       tuple of numbers representing a dash-pattern

       linecolor (string, color, or `None`): stroke color

       fillcolor (string, color, or `None`): fill color

       marker (string or `None`): symbol at each point

       markersize (float): scale factor to resize marker points

       markercolor (string, color, or `None`): fill color for markers

       markeroutline (string, color, or `None`): stroke color for markers

    Public members:
       `linewidth`, `linestyle`, `linecolor`, `fillcolor`, `marker`,
       `markersize`, `markercolor`, and `markeroutline`.

    Purpose:
       Can be used in place of a real Histogram/Scatter/etc. in Legend.
    """

    def __init__(self, linewidth=1., linestyle="solid", linecolor=None, fillcolor=None, marker=None, markersize=1., markercolor="black", markeroutline=None):
        self.linewidth, self.linestyle, self.linecolor, self.fillcolor, self.marker, self.markersize, self.markercolor, self.markeroutline = linewidth, linestyle, linecolor, fillcolor, marker, markersize, markercolor, markeroutline

    def __repr__(self):
        attributes = [""]
        if self.linecolor is not None:
            attributes.append("linewidth=%g" % self.linewidth)
            attributes.append("linestyle=%s" % str(self.linestyle))
            attributes.append("linecolor=%s" % str(self.linecolor))
        if self.fillcolor is not None:
            attributes.append("fillcolor=%s" % str(self.fillcolor))
        if self.marker is not None:
            attributes.append("marker=%s" % str(self.marker))
            attributes.append("markersize=%g" % self.markersize)
            attributes.append("markercolor=%s" % str(self.markercolor))
        return "<Style%s>" % " ".join(attributes)

######################################################### Interactive table for a PAW-style analysis

class InspectTable(UniTable):
    """Load, manipulate, and plot data quickly and interactively.

    Class members:
        cache_limit (int or `None`): a maximum number of preselected
        subtables to cache
    """

    cache_limit = 10
    _comma = re.compile("\s*,\s*")

    def __repr__(self):
        return "<InspectTable %d keys %d rows>" % (len(self.keys()), len(self))

    def _setup_cache(self):
        if getattr(self, "_cache_subtables", None) is None:
            self._cache_subtables = {}
            self._cache_order = []

    def __call__(self, expr, cuts=None, use_cache=True):
        """Select and return a subtable based on the expression and cuts.

        Arguments:
           expr (string): expression to evaluate in the namespace of
           the table and plot

           cuts (string): expression for filtering out unwanted data

           use_cache (bool): if True, keep track of all preselected
           subtables (it is likely that the user will want them again)
        """

        if cuts is None or cuts == "":
            subtable = self

        else:
            if use_cache:
                self._setup_cache()
                if cuts in self._cache_subtables and set(self.keys()) == set(self._cache_subtables[cuts].keys()):
                    subtable = self._cache_subtables[cuts]
                    self._cache_order = [cuts] + filter(lambda x: x != cuts, self._cache_order)
                else:
                    subtable = self.compress(self.eval(cuts))
                    self._cache_subtables[cuts] = subtable

                    self._cache_order = [cuts] + filter(lambda x: x != cuts, self._cache_order)
                    if self.cache_limit is not None:
                        while len(self._cache_order) > self.cache_limit:
                            del self._cache_subtables[self._cache_order.pop()]
            else:
                subtable = self.compress(self.eval(cuts))

        return subtable.eval(expr)

    def unique(self, expr=None, cuts=None, use_cache=True):
        if expr is None:
            keys = self.keys()
            expr = ",".join(keys)
        subtable = self(expr, cuts, use_cache)
        
        if isinstance(subtable, tuple):
            # can't use numpy because the output may be heterogeneous
            output = set()
            for event in zip(*subtable):
                output.add(event)
            return output

        else:
            return set(numpy.unique(subtable))

    def scan(self, expr=None, cuts=None, subset=slice(0, 10), use_cache=True, width=12):
        """Print a table or subtable of values on the screen.

        Arguments:
           expr (string): comma-separated set of expressions to print
           (if `None`, print all fields)

           cuts (string): expression for filtering out unwanted data

           subset (slice): slice applied to all fields, so that the
           output is manageable

           use_cache (bool): if True, keep track of all preselected
           subtables (it is likely that the user will want them again)
        """

        if expr is None:
            keys = self.keys()
            expr = ",".join(keys)
        subtable = self(expr, cuts, use_cache)

        fields = re.split(self._comma, expr)
        format_fields = []
        separator = []
        format_line = []
        typechar = []
        for field, array in zip(fields, subtable):
            format_fields.append("%%%d.%ds" % (width, width))
            separator.append("=" * width)

            if array.dtype.char in numpy.typecodes["Float"]:
                format_line.append("%%%dg" % width)
                typechar.append("f")
            elif array.dtype.char in numpy.typecodes["AllInteger"]:
                format_line.append("%%%dd" % width)
                typechar.append("i")
            elif array.dtype.char == "?":
                format_line.append("%%%ds" % width)
                typechar.append("?")
            elif array.dtype.char in numpy.typecodes["Complex"]:
                format_line.append("%%%dg+%%%dgj" % ((width-2)//2, (width-2)//2))
                typechar.append("F")
            elif array.dtype.char in numpy.typecodes["Character"] + "Sa":
                format_line.append("%%%d.%ds" % (width, width))
                typechar.append("S")

        format_fields = " ".join(format_fields)
        separator = "=".join(separator)

        print format_fields % tuple(fields)
        print separator

        if isinstance(subtable, tuple):
            for records in zip(*[i[subset] for i in subtable]):
                for r, f, c in zip(records, format_line, typechar):
                    if c == "F":
                        print f % (r.real, r.imag),
                    elif c == "?":
                        if r: print f % "True",
                        else: print f % "False",
                    elif c == "S":
                        print f % ("'%s'" % r),
                    else:
                        print f % r,
                print

        else:
            for record in subtable[subset]:
                if typechar[0] == "F":
                    print format_line[0] % (record.real, record.imag)
                elif typechar[0] == "?":
                    if record: print format_line[0] % "True"
                    else: print format_line[0] % "False"
                elif typechar[0] == "S":
                    print format_line[0] % ("'%s'" % record)

                else:
                    print format_line[0] % record
                    
    def histogram(self, expr, cuts=None, weights=None, numbins=utilities.binning, lowhigh=utilities.calcrange_quartile, use_cache=True, **kwds):
        """Draw and return a histogram based on the expression and cuts.

        Arguments:
           expr (string): expression to evaluate in the namespace of
           the table and plot

           cuts (string): expression for filtering out unwanted data

           weights (string): optional expression for the weight of
           each data entry

           numbins (int or function): number of bins or a function
           that returns an optimized number of bins, given data, low,
           and high

           lowhigh ((low, high) or function): range of the histogram or
           a function that returns an optimized range given the data

           use_cache (bool): if True, keep track of all preselected
           subtables (it is likely that the user will want them again)

           `**kwds`: any other arguments are passed to the Histogram
           constructor
        """
        if numbins is Auto: numbins = utilities.binning
        if lowhigh is Auto: lowhigh = utilities.calcrange_quartile

        data = self(expr, cuts)
        if isinstance(data, tuple):
            raise ContainerException, "The expr must return one-dimensional data (no commas!)"

        if weights is not None:
            dataweight = self(weights, cuts)
            if isinstance(data, tuple):
                raise ContainerException, "The weights must return one-dimensional data (no commas!)"
        else:
            dataweight = numpy.ones(len(data), numpy.float)

        if len(data) > 0 and data.dtype.char in numpy.typecodes["Character"] + "SU":
            bins = numpy.unique(data)
            bins.sort()
            kwds2 = {"xlabel": expr}
            kwds2.update(kwds)
            output = HistogramCategorical(bins, data, dataweight, **kwds2)
            
        elif len(data) == 0 or data.dtype.char in numpy.typecodes["Float"] + numpy.typecodes["AllInteger"]:
            if isinstance(lowhigh, (tuple, list)) and len(lowhigh) == 2 and isinstance(lowhigh[0], (numbers.Number, numpy.number)) and isinstance(lowhigh[1], (numbers.Number, numpy.number)):
                low, high = lowhigh
            elif callable(lowhigh):
                low, high = lowhigh(data, kwds.get("xlog", False))
            else:
                raise ContainerException, "The 'lowhigh' argument must be a function or (low, high) tuple."

            if isinstance(numbins, (int, long)):
                pass
            elif callable(numbins):
                numbins = numbins(data, low, high)
            else:
                raise ContainerException, "The 'numbins' argument must be a function or an int."

            if numbins < 1: numbins = 1
            if low >= high: low, high = 0., 1.

            kwds2 = {"xlabel": expr}
            kwds2.update(kwds)
            output = Histogram(numbins, low, high, data, dataweight, **kwds2)

        else:
            raise ContainerException, "Unrecognized data type: %s (%s)" % (data.dtype.name, data.dtype.char)

        return output

    def timeseries(self, expr, cuts=None, ex=None, ey=None, exl=None, eyl=None, limit=1000, use_cache=True, **kwds):
        """Draw and return a scatter-plot based on the expression and cuts.

        Arguments:
           expr (string): expression to evaluate in the namespace of
           the table and plot

           cuts (string): expression for filtering out unwanted data

           ex (string): optional expression for x error bars (in seconds)

           ey (string): optional expression for y error bars

           exl (string): optional expression for x lower error bars (in seconds)

           eyl (string): optional expression for y lower error bars

           limit (int or `None`): set an upper limit on the number of
           points that will be drawn

           use_cache (bool): if True, keep track of all preselected
           subtables (it is likely that the user will want them again)

           `**kwds`: any other arguments are passed to the TimeSeries
           constructor
        """
        return self.scatter(expr, cuts, ex, ey, exl, eyl, limit=limit, timeseries=True, use_cache=use_cache, **kwds)

    def scatter(self, expr, cuts=None, ex=None, ey=None, exl=None, eyl=None, limit=1000, timeseries=False, use_cache=True, **kwds):
        """Draw and return a scatter-plot based on the expression and cuts.

        Arguments:
           expr (string): expression to evaluate in the namespace of
           the table and plot

           cuts (string): expression for filtering out unwanted data

           ex (string): optional expression for x error bars

           ey (string): optional expression for y error bars

           exl (string): optional expression for x lower error bars

           eyl (string): optional expression for y lower error bars

           limit (int or `None`): set an upper limit on the number of
           points that will be drawn

           timeseries (bool): if True, produce a TimeSeries, rather
           than a Scatter

           use_cache (bool): if True, keep track of all preselected
           subtables (it is likely that the user will want them again)

           `**kwds`: any other arguments are passed to the Scatter
           constructor
        """
        fields = re.split(self._comma, expr)
        data = self(expr, cuts)

        # convert one-dimensional complex data into two-dimensional real data
        if not isinstance(data, tuple) and data.dtype.char in numpy.typecodes["Complex"]:
            data = numpy.real(data), numpy.imag(data)

        if not isinstance(data, tuple) or len(data) != 2:
            raise ContainerException, "The expr must return two-dimensional data (include a comma!)"
        xdata, ydata = data

        if ex is not None:
            ex = self(ex, cuts)
            if isinstance(ex, tuple):
                raise ContainerException, "The ex must return one-dimensional data"

        if ey is not None:
            ey = self(ey, cuts)
            if isinstance(ey, tuple):
                raise ContainerException, "The ey must return one-dimensional data"

        if exl is not None:
            exl = self(exl, cuts)
            if isinstance(exl, tuple):
                raise ContainerException, "The exl must return one-dimensional data"

        if eyl is not None:
            eyl = self(eyl, cuts)
            if isinstance(eyl, tuple):
                raise ContainerException, "The eyl must return one-dimensional data"

        if timeseries:
            if xdata.dtype.char in numpy.typecodes["Float"] + numpy.typecodes["AllInteger"]:
                kwds2 = {"xlabel": fields[0], "ylabel": fields[1], "informat": None, "limit": limit, "connector": "xsort"}
                kwds2.update(kwds)
                output = TimeSeries(x=xdata, y=ydata, ex=ex, ey=ey, exl=exl, eyl=eyl, **kwds2)

            elif xdata.dtype.char in numpy.typecodes["Character"] + "Sa":
                if ex is None and ey is None and exl is None and eyl is None:
                    kwds2 = {"xlabel": fields[0], "ylabel": fields[1], "limit": limit, "connector": "xsort"}
                else:
                    kwds2 = {"xlabel": fields[0], "ylabel": fields[1], "limit": limit, "connector": None, "marker": "circle"}
                kwds2.update(kwds)
                output = TimeSeries(x=xdata, y=ydata, ex=ex, ey=ey, exl=exl, eyl=eyl, **kwds2)

            else:
                raise ContainerException, "Unsupported data type for x of TimeSeries: %s" % xdata.dtype.name

        else:
            kwds2 = {"xlabel": fields[0], "ylabel": fields[1]}
            kwds2.update(kwds)
            output = Scatter(x=xdata, y=ydata, ex=ex, ey=ey, exl=exl, eyl=eyl, limit=limit, **kwds2)

        return output

def inspect(*files, **kwds):
    """Load an InspectTable from a file or a collection of files recognized by UniTable.

    If a single fileName is provided, `InspectTable.load` is called to
    read it into memory.

    If multiple fileNames are provided, an `InspectTable` is built
    from the concatenation of all files (using the `extend` method).

    Keyword arguments are passed to each `load` method.
    """

    output = InspectTable()
    first = True
    for f in files:
        if first:
            output.load(f, **kwds)
            first = False
        else:
            output.extend(InspectTable().load(f, **kwds))
    return output
