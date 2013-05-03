# Standard Python packages
import random
import math
import subprocess
import codecs
import numbers
import base64, StringIO

### maybe someday convert to cElementTree output rather than string concatenation
# try:
#     import xml.etree.cElementTree as ElementTree
# except ImportError:
#     import xml.etree.cElementTree as ElementTree

# Special dependencies
import PIL.Image # sudo apt-get install python-imaging

# Cassius interdependencies
import mathtools
import utilities
import color
import containers

try:
    import _svgview
except ImportError:
    _svgview = None

#: Default values for view/draw keyword arguments.
#:
#: To replace a value in a single invocation of view/draw, just
#: pass a keyword argument.
#:
#: To replace a value in a whole Cassius session, do the following::
#:
#:    >>> import cassius.svgdraw
#:    >>> cassius.svgdraw.defaults["height"] = 500
defaults = {
    "width": 1000,
    "height": 1000,
    "background": True,
    }

#: Default values for frame arguments.
#:
#: To replace a value for a single plotable object or a single
#: invocation of view/draw, just pass a keyword argument.
#:
#: To replace a value in a whole Cassius session, do the following::
#:
#:    >>> import cassius.svgdraw
#:    >>> cassius.svgdraw.default_frameargs["textscale"] = 1.3
default_frameargs = {
    "leftmargin": 0.12,
    "rightmargin": 0.05,
    "topmargin": 0.05,
    "bottommargin": 0.08,
    "textscale": 1.,
    "xlabel": None,
    "ylabel": None,
    "rightlabel": None,
    "toplabel": None,
    "xlabeloffset": 0.08,
    "ylabeloffset": -0.10,
    "rightlabeloffset": 0.,
    "toplabeloffset": 0.,
    "xlog": False,
    "ylog": False,
    "xticks": containers.Auto,
    "yticks": containers.Auto,
    "rightticks": containers.Auto,
    "topticks": containers.Auto,
    "show_topticklabels": containers.Auto,
    "show_rightticklabels": containers.Auto,
    "xmin": containers.Auto,
    "ymin": containers.Auto,
    "xmax": containers.Auto,
    "ymax": containers.Auto,
    "xmargin": 0.1,
    "ymargin": 0.1,
    }

# represents an SVG document filled by drawing commands
class SVG:
    def __init__(self, width, height, background):
        self.width, self.height = width, height

        self.header = """<?xml version="1.0" standalone="no"?>
<!DOCTYPE svg PUBLIC "-//W3C//DTD SVG 1.1//EN" "http://www.w3.org/Graphics/SVG/1.1/DTD/svg11.dtd">
<svg style="stroke-linejoin:miter; stroke:black; stroke-width:2.5; text-anchor:middle; fill:none" xmlns="http://www.w3.org/2000/svg" font-family="Helvetica, Arial, FreeSans, Sans, sans, sans-serif" width="%(width)dpx" height="%(height)dpx" version="1.1" xmlns:xlink="http://www.w3.org/1999/xlink" viewBox="0 0 %(width)d %(height)d">
""" % vars()
        self.footer = "</svg>\n"

        self.names = {}
        self.defs = {}
        self.body = []
        if background:
            self.body.append("""<rect id="background" x="0" y="0" width="%(width)g" height="%(height)g" stroke="none" fill="white" />""" % vars())

    def uniquename(self, base):
        if base not in self.names:
            self.names[base] = 0
        else:
            self.names[base] += 1
        return "%s_%d" % (base, self.names[base])

    def write(self, fileName):
        f = codecs.open(fileName, "w", "utf-8")

        f.write(self.header)

        if len(self.defs) > 0:
            f.write("<defs>\n")

            keys = self.defs.keys()
            keys.sort()  # for readability
            for key in keys:
                f.write(self.defs[key]); f.write("\n")

            f.write("</defs>\n")

        f.write("<g id=\"whole_document\">\n")
        for line in self.body:
            f.write(line); f.write("\n")
        f.write("</g>\n")

        f.write(self.footer)

    def tostring(self):
        f = StringIO.StringIO()
        f.write(self.header)
        if len(self.defs) > 0:
            f.write("<defs>")
            for value in self.defs.values():
                f.write(value)
            f.write("</defs>")
        for line in self.body:
            f.write(line)
        f.write(self.footer)
        return f.getvalue()

# this is what the user calls
def view(obj, **kwds):
    """Render a drawable object and put it in an interactive window.

    Requires the '_svgview' module.  If the '_svgview' module has not been compiled, use \"draw(object, fileName='...')\" instead.
    """

    if _svgview is None:
        raise RuntimeError, "The '_svgview' extension module has not been compiled; use \"draw(object, fileName='...')\" instead."

    svg = kwds.get("svg", None)
    
    # actual drawing is done in internal subcommands
    try:
        subcommand = eval("_draw_%s" % obj.__class__.__name__)
    except NameError:
        raise NotImplementedError, "A '_draw_%s' function has not been implemented in backends.svg" % obj.__class__.__name__

    if svg is None:
        # set the defaults (if not already overridden with explicit keyword arguments)
        for arg, value in defaults.items():
            if arg not in kwds:
                kwds[arg] = value
        # the following are derived arguments
        svg = SVG(kwds["width"], kwds["height"], kwds["background"])
        kwds["svg"] = svg
        kwds["x1"], kwds["y1"], kwds["x2"], kwds["y2"] = 0., 0., float(kwds["width"]), float(kwds["height"])

        # run the command and view the SVG
        subcommand(obj, **kwds)
        _svgview.str(svg.tostring())
    else:
        # not working on a new SVG; add to the existing one
        subcommand(obj, **kwds)

# this is what the user calls
def draw(obj, **kwds):
    """Render a drawable object and save it to an SVG file.

    Required keyword argument: fileName (string).  The fileName should
    include an \".svg\" suffix.
    """

    svg = kwds.get("svg", None)
    
    # actual drawing is done in internal subcommands
    try:
        subcommand = eval("_draw_%s" % obj.__class__.__name__)
    except NameError:
        raise NotImplementedError, "A '_draw_%s' function has not been implemented in backends.svg" % obj.__class__.__name__

    if svg is None:
        try:
            fileName = kwds["fileName"]
        except KeyError:
            raise TypeError, "The 'svgdraw.draw' function requires fileName='...'"

        # set the defaults (if not already overridden with explicit keyword arguments)
        for arg, value in defaults.items():
            if arg not in kwds:
                kwds[arg] = value
        # the following are derived arguments
        svg = SVG(kwds["width"], kwds["height"], kwds["background"])
        kwds["svg"] = svg
        kwds["x1"], kwds["y1"], kwds["x2"], kwds["y2"] = 0., 0., float(kwds["width"]), float(kwds["height"])

        # run the command and write the SVG
        subcommand(obj, **kwds)
        svg.write(fileName)
    else:
        # not working on a new SVG; add to the existing one
        subcommand(obj, **kwds)

# this draws a PDF by invoking inkscape on an intermediary SVG file
def drawpdf(obj, fileName, tmpFileName="/tmp/tmp.svg", **kwds):
    """Render a drawable object as a temporary SVG, then call \"inkscape\" to convert it to PDF.

    Note: the \"inkscape\" command must be installed on your system to
    use this command.
    """

    kwds["fileName"] = tmpFileName
    draw(obj, **kwds)
    proc = subprocess.Popen(["inkscape", tmpFileName, "--export-pdf=" + fileName])
    proc.wait()

###################################################### utilities

def _svgopacity(obj):
    if isinstance(obj, color.AbstractColor):
        return obj.opacity
    else:
        return 1.

def _svgcolor(obj):
    if obj is None:
        return "none"
    elif isinstance(obj, basestring):
        return obj
    else:
        return str(obj)

def _svglinestyle(obj, linewidth=1.):
    if obj is None or obj == "solid":
        return ""
    elif obj == "dashed":
        return _svglinestyle((15.*linewidth, 15.*linewidth))
    elif obj == "dotted":
        return _svglinestyle((3.*linewidth, 3.*linewidth))

    elif isinstance(obj, (list, tuple)):
        allnumbers = True
        for i in obj:
            if not isinstance(i, numbers.Number):
                allnumbers = False
                break
        if allnumbers:
            return " ".join(map(str, obj))

    else:
        return obj

def _svglinewidth(obj):
    return obj*3.

def _svgmarkersize(obj):
    return obj*7.5

def _transformX(x, wx1, wx2, xmin, xmax, xlog):
    if xlog:
        return wx1 + (math.log10(x) - math.log10(xmin))*(wx2 - wx1)/(math.log10(xmax) - math.log10(xmin))
    else:
        return wx1 + (x - xmin)*(wx2 - wx1)/(xmax - xmin)

def _transformY(y, wy1, wy2, ymin, ymax, ylog):
    if ylog:
        return wy2 - (math.log10(y) - math.log10(ymin))*(wy2 - wy1)/(math.log10(ymax) - math.log10(ymin))
    else:
        return wy2 - (y - ymin)*(wy2 - wy1)/(ymax - ymin)

###################################################### draw_frame

def _get_frameargs(obj, **kwds):
    output = obj._frameargs()

    try:
        subcommand = eval("_frameargs_prehook_%s" % obj.__class__.__name__)
    except NameError:
        subcommand = None
    if subcommand is not None:
        output = subcommand(obj, output, **kwds)

    # framearg precedence:
    #     1. draw(..., framearg=something)
    #     2. draw(obj(..., framearg=something))
    #     3. default_frameargs[framearg] = something
    for i in default_frameargs:
        if i in kwds:
            output[i] = kwds[i]                    #1
        else:
            if i in output: pass                   #2   (it's already in there)
            else:
                output[i] = default_frameargs[i]   #3

    if output["leftmargin"] is None: output["leftmargin"] = 0.
    if output["rightmargin"] is None: output["rightmargin"] = 0.
    if output["topmargin"] is None: output["topmargin"] = 0.
    if output["bottommargin"] is None: output["bottommargin"] = 0.
    if output["xmargin"] is None: output["xmargin"] = 0.
    if output["ymargin"] is None: output["ymargin"] = 0.

    if output["xmin"] is containers.Auto or output["ymin"] is containers.Auto or output["xmax"] is containers.Auto or output["ymax"] is containers.Auto:
        def goget(attrib, default):
            out = output.get(attrib, default)
            if isinstance(out, numbers.Number):
                return out
            else:
                return default
        xmin, ymin, xmax, ymax = obj.ranges(output["xlog"], output["ylog"])
        xmargin = output["xmargin"]*(goget("xmax", xmax) - goget("xmin", xmin))
        ymargin = output["ymargin"]*(goget("ymax", ymax) - goget("ymin", ymin))
        xmin = xmin - xmargin
        xmax = xmax + xmargin
        ymin = ymin - ymargin
        ymax = ymax + ymargin
        if output["xmin"] is containers.Auto: output["xmin"] = xmin
        if output["ymin"] is containers.Auto: output["ymin"] = ymin
        if output["xmax"] is containers.Auto: output["xmax"] = xmax
        if output["ymax"] is containers.Auto: output["ymax"] = ymax

    if output["xticks"] is None:
        output["xticks"] = {}
    elif callable(output["xticks"]):
        output["xticks"] = output["xticks"](output["xmin"], output["xmax"])
    elif output["xticks"] is containers.Auto:
        if output["xlog"]:
            output["xticks"] = utilities.tickmarks(logbase=10)(output["xmin"], output["xmax"])
        else:
            output["xticks"] = utilities.tickmarks()(output["xmin"], output["xmax"])
    elif callable(output["xticks"]):
        vals = output["xticks"](output["xmin"], output["xmax"])
        output["xticks"] = dict(map(lambda x: (x, unumber(x)), vals))
    elif isinstance(output["xticks"], (tuple, list)) and len(output["xticks"]) == 2 and callable(output["xticks"][0]) and callable(output["xticks"][1]):
        if output["xticks"][0].func_name == "timeticks" and output["xticks"][1].func_name == "timeminiticks":
            major = output["xticks"][0](output["xmin"], output["xmax"])
            minor = output["xticks"][1](output["xmin"], output["xmax"])
        else:
            major = dict(map(lambda x: (x, unumber(x)), output["xticks"][0](output["xmin"], output["xmax"])))
            minor = dict(map(lambda x: (x, None), output["xticks"][1](output["xmin"], output["xmax"])))
        minor.update(major)
        output["xticks"] = minor

    if output["yticks"] is None:
        output["yticks"] = {}
    elif callable(output["yticks"]):
        output["yticks"] = output["yticks"](output["ymin"], output["ymax"])
    elif output["yticks"] is containers.Auto:
        if output["ylog"]:
            output["yticks"] = utilities.tickmarks(logbase=10)(output["ymin"], output["ymax"])
        else:
            output["yticks"] = utilities.tickmarks()(output["ymin"], output["ymax"])
    elif callable(output["yticks"]):
        vals = output["yticks"](output["ymin"], output["ymax"])
        output["yticks"] = dict(map(lambda x: (x, unumber(x)), vals))
    elif isinstance(output["yticks"], (tuple, list)) and len(output["yticks"]) == 2 and callable(output["yticks"][0]) and callable(output["yticks"][1]):
        major = dict(map(lambda x: (x, unumber(x)), output["yticks"][0](output["ymin"], output["ymax"])))
        minor = dict(map(lambda x: (x, None), output["yticks"][1](output["ymin"], output["ymax"])))
        minor.update(major)
        output["yticks"] = minor

    if output["topticks"] is None:
        output["topticks"] = {}
    elif output["topticks"] is containers.Auto:
        output["topticks"] = output["xticks"]
        if output["show_topticklabels"] is containers.Auto:
            output["show_topticklabels"] = False
    else:
        if output["show_topticklabels"] is containers.Auto:
            output["show_topticklabels"] = True

    if output["rightticks"] is None:
        output["rightticks"] = {}
    elif output["rightticks"] is containers.Auto:
        output["rightticks"] = output["yticks"]
        if output["show_rightticklabels"] is containers.Auto:
            output["show_rightticklabels"] = False
    else:
        if output["show_rightticklabels"] is containers.Auto:
            output["show_rightticklabels"] = True

    try:
        subcommand = eval("_frameargs_posthook_%s" % obj.__class__.__name__)
    except NameError:
        subcommand = None
    if subcommand is not None:
        output = subcommand(obj, output, **kwds)

    return output

def _get_window(**kwds):
    x1, y1, x2, y2, f = kwds["x1"], kwds["y1"], kwds["x2"], kwds["y2"], kwds["frameargs"]
    wx1, wx2 = x1 + f["leftmargin"]*(x2 - x1), x2 - f["rightmargin"]*(x2 - x1)
    wy1, wy2 = y1 + f["topmargin"]*(y2 - y1), y2 - f["bottommargin"]*(y2 - y1)
    return wx1, wy1, wx2, wy2

def _draw_frame(**kwds):
    svg, x1, y1, x2, y2 = kwds["svg"], kwds["x1"], kwds["y1"], kwds["x2"], kwds["y2"]
    f = kwds["frameargs"]
    
    wx1, wy1, wx2, wy2 = _get_window(**kwds)
    windowwidth, windowheight = wx2 - wx1, wy2 - wy1
    font_size = f["textscale"]*30.

    xmin, ymin, xmax, ymax = f["xmin"], f["ymin"], f["xmax"], f["ymax"]
    xlog, ylog = f["xlog"], f["ylog"]

    framename = svg.uniquename("frame")
    svg.body.append(u"""<g id="%(framename)s">""" % vars())
    svg.body.append(u"""    <rect id="%(framename)s_border" x="%(wx1)g" y="%(wy1)g" width="%(windowwidth)g" height="%(windowheight)g" />""" % vars())

    # bottom-axis label and ticks
    if f["xlabel"] is not None:
        tx, ty, text = wx1 + (wx2 - wx1)/2., wy2 + f["xlabeloffset"]*windowheight, f["xlabel"]
        svg.body.append(u"""    <text id="%(framename)s_bottomlabel" font-size="%(font_size)g" transform="translate(%(tx)g, %(ty)g)" text-anchor="middle" dominant-baseline="middle" stroke="none" fill="black">%(text)s</text>""" % vars())

    svg.body.append(u"""    <g id="%(framename)s_bottomticks">""" % vars())
    tickend, minitickend, textmid = wy2 - 20., wy2 - 10., wy2 + 30.
    for x, label in f["xticks"].items():
        hpos = _transformX(x, wx1, wx2, xmin, xmax, xlog)
        if label is not None:
            svg.body.append(u"""        <path d="M %(hpos)g %(wy2)g L %(hpos)g %(tickend)g" />""" % vars())
            svg.body.append(u"""        <text font-size="%(font_size)g" transform="translate(%(hpos)g, %(textmid)g)" text-anchor="middle" dominant-baseline="middle" stroke="none" fill="black">%(label)s</text>""" % vars())
        else:
            svg.body.append(u"""        <path d="M %(hpos)g %(wy2)g L %(hpos)g %(minitickend)g" />""" % vars())

    svg.body.append(u"""    </g>""")

    # left-axis label and ticks
    if f["ylabel"] is not None:
        tx, ty, text = wx1 + f["ylabeloffset"]*windowwidth, wy1 + (wy2 - wy1)/2., f["ylabel"]
        svg.body.append(u"""    <text id="%(framename)s_leftlabel" font-size="%(font_size)g" transform="translate(%(tx)g, %(ty)g) rotate(-90)" text-anchor="middle" dominant-baseline="middle" stroke="none" fill="black">%(text)s</text>""" % vars())

    svg.body.append(u"""    <g id="%(framename)s_leftticks">""" % vars())
    tickend, minitickend, textmid = wx1 + 20., wx1 + 10., wx1 - 10.
    for y, label in f["yticks"].items():
        vpos = _transformY(y, wy1, wy2, ymin, ymax, ylog)
        vpostext = vpos + 10.
        if label is not None:
            svg.body.append(u"""        <path d="M %(wx1)g %(vpos)g L %(tickend)g %(vpos)g" />""" % vars())
            svg.body.append(u"""        <text font-size="%(font_size)g" transform="translate(%(textmid)g, %(vpostext)g)" text-anchor="end" dominant-baseline="middle" stroke="none" fill="black">%(label)s</text>""" % vars())
        else:
            svg.body.append(u"""        <path d="M %(wx1)g %(vpos)g L %(minitickend)g %(vpos)g" />""" % vars())

    svg.body.append(u"""    </g>""")

    # top-axis label and ticks
    if f["toplabel"] is not None:
        tx, ty, text = wx1 + (wx2 - wx1)/2., wy1 + f["toplabeloffset"]*windowheight, f["toplabel"]
        svg.body.append(u"""    <text id="%(framename)s_toplabel" font-size="%(font_size)g" transform="translate(%(tx)g, %(ty)g)" text-anchor="middle" dominant-baseline="middle" stroke="none" fill="black">%(text)s</text>""" % vars())

    svg.body.append(u"""    <g id="%(framename)s_topticks">""" % vars())
    tickend, minitickend, textmid = wy1 + 20., wy1 + 10., wy1 - 30.
    for x, label in f["topticks"].items():
        hpos = _transformX(x, wx1, wx2, xmin, xmax, xlog)
        if label is not None:
            svg.body.append(u"""        <path d="M %(hpos)g %(wy1)g L %(hpos)g %(tickend)g" />""" % vars())
            if f["show_topticklabels"]:
                svg.body.append(u"""        <text font-size="%(font_size)g" transform="translate(%(hpos)g, %(textmid)g)" text-anchor="middle" dominant-baseline="middle" stroke="none" fill="black">%(label)s</text>""" % vars())
        else:
            svg.body.append(u"""        <path d="M %(hpos)g %(wy1)g L %(hpos)g %(minitickend)g" />""" % vars())

    svg.body.append(u"""    </g>""")

    # right-axis label and ticks
    if f["rightlabel"] is not None:
        tx, ty, text = wx2 + f["rightlabeloffset"]*windowwidth, wy1 + (wy2 - wy1)/2., f["rightlabel"]
        svg.body.append(u"""    <text id="%(framename)s_rightlabel" font-size="%(font_size)g" transform="translate(%(tx)g, %(ty)g) rotate(90)" text-anchor="middle" dominant-baseline="middle" stroke="none" fill="black">%(text)s</text>""" % vars())

    svg.body.append(u"""    <g id="%(framename)s_rightticks">""" % vars())
    tickend, minitickend, textmid = wx2 - 20., wx2 - 10., wx2 + 10.
    for y, label in f["rightticks"].items():
        vpos = _transformY(y, wy1, wy2, ymin, ymax, ylog)
        vpostext = vpos + 10.
        if label is not None:
            svg.body.append(u"""        <path d="M %(wx2)g %(vpos)g L %(tickend)g %(vpos)g" />""" % vars())
            if f["show_rightticklabels"]:
                svg.body.append(u"""        <text font-size="%(font_size)g" transform="translate(%(textmid)g, %(vpostext)g)" text-anchor="start" dominant-baseline="middle" stroke="none" fill="black">%(label)s</text>""" % vars())
        else:
            svg.body.append(u"""        <path d="M %(wx2)g %(vpos)g L %(minitickend)g %(vpos)g" />""" % vars())

    svg.body.append(u"""    </g>""")
    
    svg.body.append(u"""</g>""")


###################################################### actions for particular classes

def _draw_NoneType(obj, **kwds):
    ### debugging code
    # svg, x1, y1, x2, y2 = kwds["svg"], kwds["x1"], kwds["y1"], kwds["x2"], kwds["y2"]
    # width = x2 - x1
    # height = y2 - y1
    # color = rgbcolor(random.gauss(0.5, 0.3), random.gauss(0.5, 0.3), random.gauss(0.5, 0.3))
    # svg.body.append(u"""<rect x="%(x1)g" y="%(y1)g" width="%(width)g" height="%(height)g" stroke="none" fill="%(color)s" />""" % vars())
    pass

def _draw_Layout(obj, **kwds):
    svg, x1, y1, x2, y2 = kwds["svg"], kwds["x1"], kwds["y1"], kwds["x2"], kwds["y2"]

    # TODO: possibly need to change the margins for different layouts
    #       by passing down a multiplier?
    width = (x2 - x1)/float(obj.ncols)
    height = (y2 - y1)/float(obj.nrows)
    for i in xrange(obj.nrows):
        kwds["y1"], kwds["y2"] = (y1 + i*height), (y1 + (i+1)*height)
        for j in xrange(obj.ncols):
            kwds["x1"], kwds["x2"] = (x1 + j*width), (x1 + (j+1)*width)
            draw(obj[i,j], **kwds)

def _draw_Overlay(obj, **kwds):
    svg, x1, y1, x2, y2 = kwds["svg"], kwds["x1"], kwds["y1"], kwds["x2"], kwds["y2"]

    drawframe = kwds.get("drawframe", True)

    def findframe(obj):
        if isinstance(obj, containers.Stack):
            obj._prepare()
            return findframe(obj._overlay)

        elif isinstance(obj, containers.Overlay):
            if "frame" in obj.__dict__ and obj.frame is not None:
                if obj.frame >= len(obj.plots):
                    raise containers.ContainerException, "Overlay.frame points to a non-existent plot (%d <= %d)" % (obj.frame, len(obj.plots))
                return findframe(obj.plots[obj.frame])
            else:
                return _get_frameargs(obj, **kwds)

        else:
            return _get_frameargs(obj, **kwds)

    foundframe = findframe(obj)  # to evaluate all Stacks
    if drawframe:
        kwds["frameargs"] = foundframe
        kwds["drawframe"] = False  # for the contained objects

    # flatten any Overlay nesting and draw Legends _above_ the frame
    def recurse(plotsin, nonlegends, legends):
        for plot in plotsin:
            if isinstance(plot, containers.Stack):
                recurse(plot._overlay.plots, nonlegends, legends)
            elif isinstance(plot, containers.Overlay):
                recurse(plot.plots, nonlegends, legends)
            elif isinstance(plot, containers.Legend):
                legends.append(plot)
            else:
                nonlegends.append(plot)

    nonlegends = []
    legends = []
    recurse(obj.plots, nonlegends, legends)

    for plot in nonlegends:
        draw(plot, **kwds)

    if drawframe: _draw_frame(**kwds)

    for plot in legends:
        draw(plot, **kwds)

def _draw_Stack(obj, **kwds):
    obj._prepare()
    draw(obj._overlay, **kwds)

def _frameargs_prehook_Histogram(obj, output, **kwds):
    if "ymin" not in output or output["ymin"] is None or output["ymin"] is containers.Auto:
        if "ylog" not in output or not output["ylog"]:
            output["ymin"] = 0.

    if "xmargin" not in output:
        output["xmargin"] = 0.

    return output

def _frameargs_prehook_HistogramAbstract(obj, output, **kwds):
    return _frameargs_prehook_Histogram(obj, output, **kwds)

def _frameargs_prehook_HistogramNonUniform(obj, output, **kwds):
    return _frameargs_prehook_Histogram(obj, output, **kwds)

def _frameargs_prehook_HistogramCategorical(obj, output, **kwds):
    return _frameargs_prehook_Histogram(obj, output, **kwds)

def _draw_HistogramAbstract(obj, **kwds):
    _draw_Histogram(obj, **kwds)

def _draw_Histogram(obj, **kwds):
    svg = kwds["svg"]
    if kwds.get("drawframe", True): kwds["frameargs"] = _get_frameargs(obj, **kwds)
    f = kwds["frameargs"]

    linewidth = _svglinewidth(obj.linewidth)
    linestyle = _svglinestyle(obj.linestyle, obj.linewidth)
    lineopacity = _svgopacity(obj.linecolor)
    linecolor = _svgcolor(obj.linecolor)
    fillopacity = _svgopacity(obj.fillcolor)
    fillcolor = _svgcolor(obj.fillcolor)

    wx1, wy1, wx2, wy2 = _get_window(**kwds)
    windowwidth, windowheight = wx2 - wx1, wy2 - wy1
    xmin, ymin, xmax, ymax, xlog, ylog = f["xmin"], f["ymin"], f["xmax"], f["ymax"], f["xlog"], f["ylog"]
    def t(x, y):
        return _transformX(x, wx1, wx2, xmin, xmax, xlog), _transformY(y, wy1, wy2, ymin, ymax, ylog)

    xepsilon = mathtools.epsilon * (xmax - xmin)
    yepsilon = mathtools.epsilon * (ymax - ymin)

    bins = obj.binedges()
    gap = obj.gap*(_transformX(xmax, wx1, wx2, xmin, xmax, xlog) - _transformX(xmin, wx1, wx2, xmin, xmax, xlog))/len(obj.bins)

    line = [] # in data coordinates
    pathdata = [] # in SVG coordinates with gaps
    for (binlow, binhigh), value in zip(bins, obj.values):
        if len(line) == 0:
            line.append((binlow, 0.))
            pathdata.append("M %g %g" % t(*line[-1]))

            if gap > mathtools.epsilon:
                line.append((binlow, 0.))
                x, y = t(*line[-1])
                x += gap/2.
                pathdata.append("L %g %g" % (x, y))

        elif abs(line[-1][0] - binlow) > xepsilon or gap > mathtools.epsilon:
            line.append((line[-1][0], 0.))
            line.append((binlow, 0.))

            if gap > mathtools.epsilon:
                x, y = t(*line[-2])
                x -= gap/2.
                pathdata.append("L %g %g" % (x, y))
                x, y = t(*line[-1])
                x += gap/2.
                pathdata.append("L %g %g" % (x, y))
            else:
                pathdata.append("L %g %g" % t(*line[-2]))
                pathdata.append("L %g %g" % t(*line[-1]))

        line.append((binlow, value))
        line.append((binhigh, value))

        if gap > mathtools.epsilon:
            x, y = t(*line[-2])
            x += gap/2.
            pathdata.append("L %g %g" % (x, y))
            x, y = t(*line[-1])
            x -= gap/2.
            pathdata.append("L %g %g" % (x, y))
        else:
            pathdata.append("L %g %g" % t(*line[-2]))
            pathdata.append("L %g %g" % t(*line[-1]))

    if gap > mathtools.epsilon:
        line.append((line[-1][0], 0.))
        x, y = t(*line[-1])
        x -= gap/2.
        pathdata.append("L %g %g" % (x, y))

    line.append((line[-1][0], 0.))
    pathdata.append("L %g %g" % t(*line[-1]))

    pathdata = " ".join(pathdata)

    plotname = svg.uniquename(obj.__class__.__name__)
    plotclipname = "%s_clip" % plotname

    svg.defs[plotclipname] = u"""    <clipPath id="%(plotclipname)s">
        <rect x="%(wx1)g" y="%(wy1)g" width="%(windowwidth)g" height="%(windowheight)g" />
    </clipPath>""" % vars()

    h = "#"
    svg.body.append(u"""<g id="%(plotname)s" clip-path="url(%(h)s%(plotclipname)s)">""" % vars())
    svg.body.append(u"""    <path d="%(pathdata)s" stroke-width="%(linewidth)g" stroke-dasharray="%(linestyle)s" stroke="%(linecolor)s" stroke-opacity="%(lineopacity)g" fill="%(fillcolor)s" fill-opacity="%(fillopacity)g" />""" % vars())
    svg.body.append(u"""</g>""")

    if kwds.get("drawframe", True): _draw_frame(**kwds)

def _draw_HistogramNonUniform(obj, **kwds):
    _draw_Histogram(obj, **kwds)

def _draw_HistogramCategorical(obj, **kwds):
    _draw_Histogram(obj, **kwds)

def _frameargs_posthook_HistogramCategorical(obj, output, **kwds):
    f = obj._frameargs()
    if f.get("xticks", containers.Auto) is containers.Auto:
        output["xticks"] = dict(enumerate(obj.bins))
    return output

def _draw_Scatter(obj, **kwds):
    svg = kwds["svg"]
    if kwds.get("drawframe", True): kwds["frameargs"] = _get_frameargs(obj, **kwds)
    f = kwds["frameargs"]

    obj._prepare(f["xmin"], f["ymin"], f["xmax"], f["ymax"])

    wx1, wy1, wx2, wy2 = _get_window(**kwds)
    windowwidth, windowheight = wx2 - wx1, wy2 - wy1
    xmin, ymin, xmax, ymax, xlog, ylog = f["xmin"], f["ymin"], f["xmax"], f["ymax"], f["xlog"], f["ylog"]
    def t(x, y):
        return _transformX(x, wx1, wx2, xmin, xmax, xlog), _transformY(y, wy1, wy2, ymin, ymax, ylog)

    plotname = svg.uniquename(obj.__class__.__name__)
    plotclipname = "%s_clip" % plotname
    plotmarkname = "%s_mark" % plotname

    svg.defs[plotclipname] = u"""    <clipPath id="%(plotclipname)s">
        <rect x="%(wx1)g" y="%(wy1)g" width="%(windowwidth)g" height="%(windowheight)g" />
    </clipPath>""" % vars()

    markeropacity = _svgopacity(obj.markercolor)
    markercolor = _svgcolor(obj.markercolor)
    markeroutlineopacity = _svgopacity(obj.markeroutline)
    markeroutline = _svgcolor(obj.markeroutline)

    # TODO: handle shapes other than circles (in a centralized way)
    if obj.marker == "circle":
        radius = _svgmarkersize(obj.markersize)
        svg.defs[plotmarkname] = u"""    <circle id="%(plotmarkname)s" cx="0" cy="0" r="%(radius)g" stroke="%(markeroutline)s" stroke-opacity="%(markeroutlineopacity)g" fill="%(markercolor)s" fill-opacity="%(markeropacity)g" />""" % vars()
    else:
        pass

    h = "#"
    svg.body.append(u"""<g id="%(plotname)s" clip-path="url(%(h)s%(plotclipname)s)">""" % vars())

    xindex = obj.index()["x"]
    yindex = obj.index()["y"]

    if obj.connector is not None:
        linewidth = _svglinewidth(obj.linewidth)
        linestyle = _svglinestyle(obj.linestyle, obj.linewidth)
        lineopacity = _svgopacity(obj.linecolor)
        linecolor = _svgcolor(obj.linecolor)

        pathdata = []
        if obj.connector == "xsort":
            limvals = obj._xlimited_values
        elif obj.connector == "ysort":
            limvals = obj._ylimited_values
        elif obj.connector == "unsorted":
            limvals = obj._xlimited_values
        for xval, yval in limvals:
            if len(pathdata) == 0:
                pathdata.append("M %g %g" % t(xval, yval))
            else:
                pathdata.append("L %g %g" % t(xval, yval))
        pathdata = " ".join(pathdata)

        svg.body.append(u"""    <path d="%(pathdata)s" stroke-width="%(linewidth)g" stroke-dasharray="%(linestyle)s" stroke="%(linecolor)s" stroke-opacity="%(lineopacity)g" fill="none" />""" % vars())

    if "ex" in obj.sig:
        lineopacity = _svgopacity(obj.linecolor)
        linecolor = _svgcolor(obj.linecolor)

        if "exl" in obj.sig: exlindex = obj.index()["exl"]
        else: exlindex = obj.index()["ex"]
        exindex = obj.index()["ex"]

        def down(x, y): return x, y - 5.
        def up(x, y): return x, y + 5.

        for value in obj._limited_values:
            x, y, exl, ex = value[xindex], value[yindex], abs(value[exlindex]), abs(value[exindex])
            pathdata = ["M %g %g" % t(x - exl, y),
                        "L %g %g" % t(x + ex, y),
                        "M %g %g" % down(*t(x - exl, y)),
                        "L %g %g" % up(*t(x - exl, y)),
                        "M %g %g" % down(*t(x + ex, y)),
                        "L %g %g" % up(*t(x + ex, y))]
            pathdata = " ".join(pathdata)
            svg.body.append(u"""    <path d="%(pathdata)s" stroke="%(linecolor)s" stroke-opacity="%(lineopacity)g" fill="none" />""" % vars())

    if "ey" in obj.sig:
        lineopacity = _svgopacity(obj.linecolor)
        linecolor = _svgcolor(obj.linecolor)

        if "eyl" in obj.sig: eylindex = obj.index()["eyl"]
        else: eylindex = obj.index()["ey"]
        eyindex = obj.index()["ey"]

        def down(x, y): return x - 5., y
        def up(x, y): return x + 5., y

        for value in obj._limited_values:
            x, y, eyl, ey = value[xindex], value[yindex], abs(value[eylindex]), abs(value[eyindex])
            pathdata = ["M %g %g" % t(x, y - eyl),
                        "L %g %g" % t(x, y + ey),
                        "M %g %g" % down(*t(x, y - eyl)),
                        "L %g %g" % up(*t(x, y - eyl)),
                        "M %g %g" % down(*t(x, y + ey)),
                        "L %g %g" % up(*t(x, y + ey))]
            pathdata = " ".join(pathdata)
            svg.body.append(u"""    <path d="%(pathdata)s" stroke="%(linecolor)s" stroke-opacity="%(lineopacity)g" fill="none" />""" % vars())

    if obj.marker is not None:
        for value in obj._limited_values:
            x, y = t(value[xindex], value[yindex])
            svg.body.append(u"""    <use x="%(x)g" y="%(y)g" xlink:href="%(h)s%(plotmarkname)s" />""" % vars())

    svg.body.append(u"""</g>""")

    if kwds.get("drawframe", True): _draw_frame(**kwds)

def _frameargs_posthook_Scatter(obj, output, **kwds):
    f = obj._frameargs()
    if f.get("xticks", containers.Auto) is containers.Auto and getattr(obj, "_xticks", None) is not None:
        output["xticks"] = obj._xticks
    if f.get("yticks", containers.Auto) is containers.Auto and getattr(obj, "_yticks", None) is not None:
        output["yticks"] = obj._yticks
    return output

def _draw_TimeSeries(obj, **kwds):
    _draw_Scatter(obj, **kwds)

def _frameargs_prehook_TimeSeries(obj, output, **kwds):
    if "xmin" in output and output["xmin"] is not None and output["xmin"] is not containers.Auto and isinstance(output["xmin"], basestring):
        output["xmin"] = obj.fromtimestring(output["xmin"])
    if "xmax" in output and output["xmax"] is not None and output["xmax"] is not containers.Auto and isinstance(output["xmax"], basestring):
        output["xmax"] = obj.fromtimestring(output["xmax"])
    return output

def _frameargs_posthook_TimeSeries(obj, output, **kwds):
    f = obj._frameargs()
    if "xticks" not in f or f["xticks"] is containers.Auto:
        xticks = output["xticks"]
        for value, name in xticks.items():
            if name is not None:
                xticks[value] = obj.totimestring(value)
        output["xticks"] = xticks
    return output

def _draw_ColorField(obj, **kwds):
    svg = kwds["svg"]
    if kwds.get("drawframe", True): kwds["frameargs"] = _get_frameargs(obj, **kwds)
    f = kwds["frameargs"]

    wx1, wy1, wx2, wy2 = _get_window(**kwds)
    windowwidth, windowheight = wx2 - wx1, wy2 - wy1
    xmin, ymin, xmax, ymax, xlog, ylog = f["xmin"], f["ymin"], f["xmax"], f["ymax"], f["xlog"], f["ylog"]

    xbins, ybins = obj.xbins(), obj.ybins()
    zmin, zmax = obj.zranges()
    if obj.zmin is not containers.Auto:
        zmin = obj.zmin
    if obj.zmax is not containers.Auto:
        zmax = obj.zmax

    image = PIL.Image.new("RGBA", (xbins, ybins), (0, 0, 0, 255))
    for i in xrange(xbins):
        for j in xrange(ybins):
            col = obj.tocolor(obj.values[i,j], zmin, zmax)
            if isinstance(col, color.RGB):
                col = col.ints()
            elif isinstance(col, (color.AbstractColor, basestring)):
                col = color.RGB(col).ints()

            image.putpixel((i, ybins-j-1), col)

    buff = StringIO.StringIO()
    image.save(buff, "PNG")
    encoded = base64.b64encode(buff.getvalue())

    if obj.smooth:
        smooth = "optimizeQuality"
    else:
        smooth = "optimizeSpeed"

    xpos = _transformX(obj.xmin, wx1, wx2, xmin, xmax, xlog)
    xpos2 = _transformX(obj.xmax, wx1, wx2, xmin, xmax, xlog)
    ypos = _transformY(obj.ymin, wy1, wy2, ymin, ymax, ylog)
    ypos2 = _transformY(obj.ymax, wy1, wy2, ymin, ymax, ylog)
    width = xpos2 - xpos
    height = ypos - ypos2

    plotname = svg.uniquename(obj.__class__.__name__)
    plotclipname = "%s_clip" % plotname

    svg.defs[plotclipname] = u"""    <clipPath id="%(plotclipname)s">
        <rect x="%(wx1)g" y="%(wy1)g" width="%(windowwidth)g" height="%(windowheight)g" />
    </clipPath>""" % vars()
    
    h = "#"
    svg.body.append(u"""<g id="%(plotname)s" clip-path="url(%(h)s%(plotclipname)s)">""" % vars())
    svg.body.append(u"""    <image xlink:href="data:image/png;base64,%(encoded)s" x="%(xpos)g" y="%(ypos2)g" width="%(width)g" height="%(height)g" image-rendering="%(smooth)s" preserveAspectRatio="none" />""" % vars())
    svg.body.append(u"""</g>""")

    if kwds.get("drawframe", True): _draw_frame(**kwds)

def _draw_Region(obj, **kwds):
    svg = kwds["svg"]
    if kwds.get("drawframe", True): kwds["frameargs"] = _get_frameargs(obj, **kwds)
    f = kwds["frameargs"]

    fillopacity = _svgopacity(obj.fillcolor)
    fillcolor = _svgcolor(obj.fillcolor)

    wx1, wy1, wx2, wy2 = _get_window(**kwds)
    windowwidth, windowheight = wx2 - wx1, wy2 - wy1
    xmin, ymin, xmax, ymax, xlog, ylog = f["xmin"], f["ymin"], f["xmax"], f["ymax"], f["xlog"], f["ylog"]

    plotname = svg.uniquename(obj.__class__.__name__)
    plotclipname = "%s_clip" % plotname

    svg.defs[plotclipname] = u"""    <clipPath id="%(plotclipname)s">
        <rect x="%(wx1)g" y="%(wy1)g" width="%(windowwidth)g" height="%(windowheight)g" />
    </clipPath>""" % vars()

    pathdata = []
    for command in obj.commands:
        if not isinstance(command, containers.RegionCommand):
            raise containers.ContainerException, "Commands passed to Region must all be RegionCommands (MoveTo, EdgeTo, ClosePolygon)"

        if isinstance(command, (containers.MoveTo, containers.EdgeTo)):
            x, y = command.x, command.y

            if isinstance(x, mathtools.InfiniteType):
                x = (wx1 + wx2)/2. + windowwidth/mathtools.epsilon * x._multiplier
            else:
                x = _transformX(x, wx1, wx2, xmin, xmax, xlog)

            if isinstance(y, mathtools.InfiniteType):
                y = (wy1 + wy2)/2. - windowwidth/mathtools.epsilon * y._multiplier
            else:
                y = _transformY(y, wy1, wy2, ymin, ymax, ylog)

            if isinstance(command, containers.MoveTo):
                pathdata.append("M %g %g" % (x, y))
            if isinstance(command, containers.EdgeTo):
                pathdata.append("L %g %g" % (x, y))

        elif isinstance(command, containers.ClosePolygon):
            pathdata.append("Z")

    pathdata = " ".join(pathdata)

    h = "#"
    svg.body.append(u"""<g id="%(plotname)s" clip-path="url(%(h)s%(plotclipname)s)">""" % vars())
    svg.body.append(u"""    <path d="%(pathdata)s" stroke-width="5." stroke="%(fillcolor)s" fill="%(fillcolor)s" fill-opacity="%(fillopacity)g" />""" % vars())
    svg.body.append(u"""</g>""")

    if kwds.get("drawframe", True): _draw_frame(**kwds)
    
def _draw_RegionMap(obj, **kwds):
    svg = kwds["svg"]
    if kwds.get("drawframe", True): kwds["frameargs"] = _get_frameargs(obj, **kwds)
    f = kwds["frameargs"]

    wx1, wy1, wx2, wy2 = _get_window(**kwds)
    windowwidth, windowheight = wx2 - wx1, wy2 - wy1
    xmin, ymin, xmax, ymax, xlog, ylog = f["xmin"], f["ymin"], f["xmax"], f["ymax"], f["xlog"], f["ylog"]

    obj._prepare()
    image = PIL.Image.new("RGBA", (obj.xbins, obj.ybins), (0, 0, 0, 255))
    for i in xrange(obj.xbins):
        for j in xrange(obj.ybins):
            image.putpixel((i, obj.ybins-j-1), obj._values[i][j])

    buff = StringIO.StringIO()
    image.save(buff, "PNG")
    encoded = base64.b64encode(buff.getvalue())
    
    xpos = _transformX(obj.xmin, wx1, wx2, xmin, xmax, xlog)
    xpos2 = _transformX(obj.xmax, wx1, wx2, xmin, xmax, xlog)
    ypos = _transformY(obj.ymin, wy1, wy2, ymin, ymax, ylog)
    ypos2 = _transformY(obj.ymax, wy1, wy2, ymin, ymax, ylog)
    width = xpos2 - xpos
    height = ypos - ypos2

    plotname = svg.uniquename(obj.__class__.__name__)
    plotclipname = "%s_clip" % plotname

    svg.defs[plotclipname] = u"""    <clipPath id="%(plotclipname)s">
        <rect x="%(wx1)g" y="%(wy1)g" width="%(windowwidth)g" height="%(windowheight)g" />
    </clipPath>""" % vars()
    
    h = "#"
    svg.body.append(u"""<g id="%(plotname)s" clip-path="url(%(h)s%(plotclipname)s)">""" % vars())
    svg.body.append(u"""    <image xlink:href="data:image/png;base64,%(encoded)s" x="%(xpos)g" y="%(ypos2)g" width="%(width)g" height="%(height)g" image-rendering="optimizeQuality" preserveAspectRatio="none" />""" % vars())
    svg.body.append(u"""</g>""")

    if kwds.get("drawframe", True): _draw_frame(**kwds)

def _draw_ConsumerRegionMap(obj, **kwds):
    _draw_RegionMap(obj, **kwds)

def _frameargs_prehook_Curve(obj, output, **kwds):
    obj._prepare(output.get("xlog", False))
    output = obj._scatter._frameargs()
    return output

def _draw_Curve(obj, **kwds):
    if "_scatter" not in obj.__dict__ or obj._scatter is None:
        if not kwds.get("drawframe", True):
            xmin = kwds["frameargs"]["xmin"]
            xmax = kwds["frameargs"]["xmax"]
            xlog = kwds["frameargs"]["xlog"]

        else:
            if "xlog" in kwds:
                xlog = kwds["xlog"]
            elif "xlog" in obj.__dict__:
                xlog = obj.xlog
            else:
                xlog = default_frameargs["xlog"]

            if "xmin" in kwds:
                xmin = kwds["xmin"]
            elif "xmin" in obj.__dict__:
                xmin = obj.xmin
            else:
                if xlog: xmin = 0.1
                else: xmin = 0.

            if "xmax" in kwds:
                xmax = kwds["xmax"]
            elif "xmax" in obj.__dict__:
                xmax = obj.xmax
            else:
                xmax = 1.

        obj._prepare(xmin=xmin, xmax=xmax, xlog=xlog)

    _draw_Scatter(obj._scatter, **kwds)
    obj._scatter = None

def _draw_Line(obj, **kwds):
    svg = kwds["svg"]
    if kwds.get("drawframe", True): kwds["frameargs"] = _get_frameargs(obj, **kwds)
    f = kwds["frameargs"]

    linewidth = _svglinewidth(obj.linewidth)
    linestyle = _svglinestyle(obj.linestyle, obj.linewidth)
    lineopacity = _svgopacity(obj.linecolor)
    linecolor = _svgcolor(obj.linecolor)

    wx1, wy1, wx2, wy2 = _get_window(**kwds)
    windowwidth, windowheight = wx2 - wx1, wy2 - wy1
    xmin, ymin, xmax, ymax, xlog, ylog = f["xmin"], f["ymin"], f["xmax"], f["ymax"], f["xlog"], f["ylog"]
    def t(x, y):
        return _transformX(x, wx1, wx2, xmin, xmax, xlog), _transformY(y, wy1, wy2, ymin, ymax, ylog)

    plotname = svg.uniquename(obj.__class__.__name__)
    plotclipname = "%s_clip" % plotname

    svg.defs[plotclipname] = u"""    <clipPath id="%(plotclipname)s">
        <rect x="%(wx1)g" y="%(wy1)g" width="%(windowwidth)g" height="%(windowheight)g" />
    </clipPath>""" % vars()

    pathdata = []
    if (isinstance(obj.x1, mathtools.InfiniteType) or isinstance(obj.y1, mathtools.InfiniteType)) and \
       (isinstance(obj.x2, mathtools.InfiniteType) or isinstance(obj.y2, mathtools.InfiniteType)):
        raise containers.ContainerException, "Only one of the two points can be at Infinity"

    elif isinstance(obj.x1, mathtools.InfiniteType) or isinstance(obj.y1, mathtools.InfiniteType):
        pathdata.append("M %g %g" % t(obj.x2, obj.y2))

        if isinstance(obj.x1, mathtools.InfiniteType):
            x = (wx1 + wx2)/2. + windowwidth/mathtools.epsilon * obj.x1._multiplier
        else:
            x = _transformX(obj.x1, wx1, wx2, xmin, xmax, xlog)

        if isinstance(obj.y1, mathtools.InfiniteType):
            y = (wy1 + wy2)/2. - windowwidth/mathtools.epsilon * obj.y1._multiplier
        else:
            y = _transformY(obj.y1, wy1, wy2, ymin, ymax, ylog)

        pathdata.append("L %g %g" % (x, y))

    elif isinstance(obj.x2, mathtools.InfiniteType) or isinstance(obj.y2, mathtools.InfiniteType):
        pathdata.append("M %g %g" % t(obj.x1, obj.y1))

        if isinstance(obj.x2, mathtools.InfiniteType):
            x = (wx1 + wx2)/2. + windowwidth/mathtools.epsilon * obj.x2._multiplier
        else:
            x = _transformX(obj.x2, wx1, wx2, xmin, xmax, xlog)

        if isinstance(obj.y2, mathtools.InfiniteType):
            y = (wy1 + wy2)/2. - windowwidth/mathtools.epsilon * obj.y2._multiplier
        else:
            y = _transformY(obj.y2, wy1, wy2, ymin, ymax, ylog)

        pathdata.append("L %g %g" % (x, y))

    else:
        pathdata.append("M %g %g L %g %g" % tuple(list(t(obj.x1, obj.y1)) + list(t(obj.x2, obj.y2))))

    pathdata = " ".join(pathdata)

    h = "#"
    svg.body.append(u"""<g id="%(plotname)s" clip-path="url(%(h)s%(plotclipname)s)">""" % vars())
    svg.body.append(u"""    <path d="%(pathdata)s" stroke-width="%(linewidth)g" stroke-dasharray="%(linestyle)s" stroke="%(linecolor)s" stroke-opacity="%(lineopacity)g" fill="none" />""" % vars())
    svg.body.append(u"""</g>""")

    if kwds.get("drawframe", True): _draw_frame(**kwds)

def _draw_Grid(obj, **kwds):
    svg = kwds["svg"]
    if kwds.get("drawframe", True): kwds["frameargs"] = _get_frameargs(obj, **kwds)
    f = kwds["frameargs"]

    linewidth = _svglinewidth(obj.linewidth)
    linestyle = _svglinestyle(obj.linestyle, obj.linewidth)
    lineopacity = _svgopacity(obj.linecolor)
    linecolor = _svgcolor(obj.linecolor)

    wx1, wy1, wx2, wy2 = _get_window(**kwds)
    windowwidth, windowheight = wx2 - wx1, wy2 - wy1
    xmin, ymin, xmax, ymax, xlog, ylog = f["xmin"], f["ymin"], f["xmax"], f["ymax"], f["xlog"], f["ylog"]
    def t(x, y):
        return _transformX(x, wx1, wx2, xmin, xmax, xlog), _transformY(y, wy1, wy2, ymin, ymax, ylog)

    obj._prepare(xmin, ymin, xmax, ymax)

    plotname = svg.uniquename(obj.__class__.__name__)
    plotclipname = "%s_clip" % plotname

    svg.defs[plotclipname] = u"""    <clipPath id="%(plotclipname)s">
        <rect x="%(wx1)g" y="%(wy1)g" width="%(windowwidth)g" height="%(windowheight)g" />
    </clipPath>""" % vars()

    pathdata = []
    for x in obj._vert:
        pathdata.append("M %g %g L %g %g" % tuple(list(t(x, ymin)) + list(t(x, ymax))))
    for y in obj._horiz:
        pathdata.append("M %g %g L %g %g" % tuple(list(t(xmin, y)) + list(t(xmax, y))))
    pathdata = " ".join(pathdata)

    h = "#"
    svg.body.append(u"""<g id="%(plotname)s" clip-path="url(%(h)s%(plotclipname)s)">""" % vars())
    svg.body.append(u"""    <path d="%(pathdata)s" stroke-width="%(linewidth)g" stroke-dasharray="%(linestyle)s" stroke="%(linecolor)s" stroke-opacity="%(lineopacity)g" fill="none" />""" % vars())
    svg.body.append(u"""</g>""")

    if kwds.get("drawframe", True): _draw_frame(**kwds)

def _draw_Legend(obj, **kwds):
    svg, svgwidth, svgheight = kwds["svg"], kwds["width"], kwds["height"]
    if kwds.get("drawframe", True): kwds["frameargs"] = _get_frameargs(obj, **kwds)
    f = kwds["frameargs"]

    linewidth = _svglinewidth(obj.linewidth)
    linestyle = _svglinestyle(obj.linestyle, obj.linewidth)
    lineopacity = _svgopacity(obj.linecolor)
    linecolor = _svgcolor(obj.linecolor)
    fillopacity = _svgopacity(obj.fillcolor)
    fillcolor = _svgcolor(obj.fillcolor)

    wx1, wy1, wx2, wy2 = _get_window(**kwds)
    windowwidth, windowheight = wx2 - wx1, wy2 - wy1

    obj._prepare()

    if obj.height is containers.Auto:
        # no top-padding
        # objheight = (2.*obj.padding + obj._rows*obj.baselineskip)*svgheight / windowheight
        objheight = (obj.padding + obj._rows*obj.baselineskip)*svgheight / windowheight
    else:
        objheight = obj.height

    width = obj.width * windowwidth
    height = objheight * windowheight
    x = wx1 + obj.x*windowwidth
    y = wy2 - obj.y*windowheight

    if obj._anchor[1] == "m": x -= width/2.
    elif obj._anchor[1] == "r": x -= width
    if obj._anchor[0] == "m": y -= height/2.
    elif obj._anchor[0] == "b": y -= height

    plotname = svg.uniquename(obj.__class__.__name__)
    plotclipname = "%s_clip" % plotname

    svg.defs[plotclipname] = u"""    <clipPath id="%(plotclipname)s">
        <rect x="%(x)g" y="%(y)g" width="%(width)g" height="%(height)g" />
    </clipPath>""" % vars()

    if kwds.get("drawframe", True): _draw_frame(**kwds)

    h = "#"
    svg.body.append(u"""<g id="%(plotname)s">""" % vars())
    svg.body.append(u"""    <rect x="%(x)g" y="%(y)g" width="%(width)g" height="%(height)g" stroke-width="%(linewidth)g" stroke-dasharray="%(linestyle)s" stroke="%(linecolor)s" stroke-opacity="%(lineopacity)g" fill="%(fillcolor)s" fill-opacity="%(fillopacity)g" />""" % vars())
    svg.body.append(u"""    <g id="%(plotname)s_content" clip-path="url(%(h)s%(plotclipname)s)">""" % vars())

    # no top-padding
    # penx, peny = x + obj.padding * svgwidth, y + obj.padding * svgheight
    penx, peny = x + obj.padding * svgwidth, y
    width -= 2. * obj.padding * svgwidth
    for i in range(len(obj._fields)):
        peny += obj.baselineskip * svgheight
        penxstart = penx
        for j in range(len(obj._fields[i])):
            drawable = obj._fields[i][j]
            drawn = False

            might_have_style = False
            try:
                drawable.__dict__
                might_have_style = True
            except AttributeError: pass

            if might_have_style:
                if "linecolor" in drawable.__dict__ and drawable.linecolor is not None:
                    lstyle = u" stroke-width=\"%g\" stroke-dasharray=\"%s\" stroke=\"%s\" stroke-opacity=\"%g\"" % (_svglinewidth(drawable.linewidth), _svglinestyle(drawable.linestyle, drawable.linewidth), _svgcolor(drawable.linecolor), _svgopacity(drawable.linecolor))
                else:
                    lstyle = u" stroke=\"none\""

                if "fillcolor" in drawable.__dict__ and drawable.fillcolor is not None:
                    drawable_fillopacity = _svgopacity(drawable.fillcolor)
                    drawable_fillcolor = _svgcolor(drawable.fillcolor)
                    rectwidth, rectheight = 1.5 * obj.baselineskip * svgheight, 0.75 * obj.baselineskip * svgheight
                    rectx, recty = penx, peny - rectheight
                    if obj._justify[j] == "l":
                        rectx += obj.padding * svgwidth
                    elif obj._justify[j] in ("m", "c"):
                        rectx += (obj._colwid[j] * width - rectwidth - obj.padding * svgwidth)/2.
                    elif obj._justify[j] == "r":
                        rectx += obj._colwid[j] * width - rectwidth - obj.padding * svgwidth

                    svg.body.append(u"""        <rect x="%(rectx)g" y="%(recty)g" width="%(rectwidth)g" height="%(rectheight)g"%(lstyle)s fill="%(drawable_fillcolor)s" fill-opacity="%(drawable_fillopacity)g" />""" % vars())
                    drawn = True

                elif "linecolor" in drawable.__dict__ and drawable.linecolor is not None:
                    withline = True
                    if isinstance(drawable, containers.Scatter) and \
                           len(set(drawable.sig).difference(set(["ex", "ey", "exl", "eyl"]))) == len(drawable.sig) and \
                           drawable.connector is None:
                               withline = False

                    if withline:
                        linelength = 1.5 * obj.baselineskip * svgheight
                        linex1, liney1 = penx, peny - 0.3 * obj.baselineskip * svgheight
                        if obj._justify[j] == "l":
                            linex1 += obj.padding * svgwidth
                        elif obj._justify[j] in ("m", "c"):
                            linex1 += (obj._colwid[j] * width - linelength - obj.padding * svgwidth)/2.
                        elif obj._justify[j] == "r":
                            linex1 += obj._colwid[j] * width - linelength - obj.padding * svgwidth
                        linex2, liney2 = linex1 + linelength, liney1

                        svg.body.append(u"""        <line x1="%(linex1)g" y1="%(liney1)g" x2="%(linex2)g" y2="%(liney2)g"%(lstyle)s />""" % vars())
                        drawn = True

                if "marker" in drawable.__dict__ and drawable.marker is not None:
                    # TODO: handle shapes other than circles (in a centralized way)
                    plotmarkname = svg.uniquename("%s_mark" % plotname)
                    radius, markeroutlineopacity, markeroutline, markeropacity, markercolor = _svgmarkersize(drawable.markersize), _svgopacity(drawable.markeroutline), _svgcolor(drawable.markeroutline), _svgopacity(drawable.markercolor), _svgcolor(drawable.markercolor)
                    svg.defs[plotmarkname] = u"""    <circle id="%(plotmarkname)s" cx="0" cy="0" r="%(radius)g" stroke="%(markeroutline)s" stroke-opacity="%(markeroutlineopacity)g" fill="%(markercolor)s" fill-opacity="%(markeropacity)g" />""" % vars()

                    linelength = 1.5 * obj.baselineskip * svgheight
                    withline = (("fillcolor" in drawable.__dict__ and drawable.fillcolor is not None) or
                                ("linecolor" in drawable.__dict__ and drawable.linecolor is not None))

                    if isinstance(drawable, containers.Scatter) and \
                           len(set(drawable.sig).difference(set(["ex", "ey", "exl", "eyl"]))) == len(drawable.sig) and \
                           drawable.connector is None:
                        withline = False

                    markx, marky = penx, peny - 0.375 * obj.baselineskip * svgheight
                    if obj._justify[j] == "l":
                        markx += obj.padding * svgwidth
                        if withline: markx += linelength / 2.
                    elif obj._justify[j] in ("m", "c"):
                        markx += (obj._colwid[j] * width - obj.padding * svgwidth)/2.
                    elif obj._justify[j] == "r":
                        markx += obj._colwid[j] * width - obj.padding * svgwidth
                        if withline: markx -= linelength / 2.

                    svg.body.append(u"""        <use x="%(markx)g" y="%(marky)g" xlink:href="%(h)s%(plotmarkname)s" />""" % vars())
                    drawn = True

            if not drawn and drawable is not None:
                astext = unicode(drawable)
                font_size = obj.textscale*30.
                if obj._justify[j] == "l":
                    placement = penx
                    text_anchor = "start"
                elif obj._justify[j] in ("m", "c"):
                    placement = penx + 0.5 * obj._colwid[j] * width
                    text_anchor = "middle"
                elif obj._justify[j] == "r":
                    placement = penx + obj._colwid[j] * width
                    text_anchor = "end"

                svg.body.append(u"""        <text font-size="%(font_size)g" transform="translate(%(placement)g, %(peny)g)" text-anchor="%(text_anchor)s" dominant-baseline="middle" stroke="none" fill="black">%(astext)s</text>""" % vars())

            penx += obj._colwid[j] * width
        penx = penxstart

    svg.body.append(u"""    </g>""")
    svg.body.append(u"""</g>""")
