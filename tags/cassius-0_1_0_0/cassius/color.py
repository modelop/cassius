# Standard Python packages
import colorsys
import math

# Special dependencies
import numpy

class AbstractColor:
    pass

class RGB(AbstractColor):
    """A color in RGB (red-green-blue) representation.

    Signatures::

       RGB(r, g, b)    r, g, b are floating-point numbers between 0. and 1.

       RGB(rgb)        rgb is another RGB color representation

       RGB(hls)        hls is a color in HLS (hue-lightness-saturation) representation

       RGB(hsv)        hsv is a color in HSV (hue-saturation-value) representation

       RGB("name")     "name" is a CSS named color string

       RGB(\"#xxxxxx\")  \"#xxxxxx\" is a string in hexidecimal RGB space

    Keyword arguments:
       opacity (number between 0. and 1.)    opacity

    Behavior:

       Comparisons are value-based (two color objects are equal if
       they represent the same color).

       Can be cast as another color type or as a string (will return hex string).
    """
    def __init__(self, *args, **kwds):
        self.opacity = 1.

        if len(args) == 3:
            self.r, self.g, self.b = args

        elif len(args) == 1 and isinstance(args[0], RGB):
            self.r, self.g, self.b = args[0].r, args[0].g, args[0].b
            self.opacity = args[0].opacity

        elif len(args) == 1 and isinstance(args[0], HLS):
            self.r, self.g, self.b = colorsys.hls_to_rgb(args[0].h, args[0].l, args[0].s)
            self.opacity = args[0].opacity

        elif len(args) == 1 and isinstance(args[0], HSV):
            self.r, self.g, self.b = colorsys.hsv_to_rgb(args[0].h, args[0].s, args[0].v)
            self.opacity = args[0].opacity

        elif len(args) == 1 and isinstance(args[0], basestring) and args[0][0] != "#":
            color = colors[args[0]]
            self.r, self.g, self.b = color.r, color.g, color.b

        elif len(args) == 1 and isinstance(args[0], basestring) and args[0][0] == "#":
            r = int(args[0][1:3], 16)
            g = int(args[0][3:5], 16)
            b = int(args[0][5:7], 16)
            self.r, self.g, self.b = r/255., g/255., b/255.

        else:
            raise TypeError, "RGB constructor arguments do not match any signature"

        if "opacity" in kwds:
            self.opacity = kwds["opacity"]
            del kwds["opacity"]

        if len(kwds) > 0:
            raise TypeError, "Unrecognized keyword arguments: %s" % str(kwds.keys())

    def __eq__(self, other):
        if isinstance(other, RGB):
            return self.r == other.r and self.g == other.g and self.b == other.b
        else:
            return self == RGB(other)

    def __hash__(self):
        return (self.r, self.g, self.b).__hash__()

    def __repr__(self):
        return "RGB(%g, %g, %g)" % (self.r, self.g, self.b)

    def ints(self):
        r = int(math.floor(self.r*255))
        if r >= 256: r = 255
        if r < 0.: r = 0

        g = int(math.floor(self.g*255))
        if g >= 256: g = 255
        if g < 0: g = 0

        b = int(math.floor(self.b*255))
        if b >= 256: b = 255
        if b < 0: b = 0

        a = int(math.floor(self.opacity*255))
        if a >= 256: a = 255
        if a < 0: a = 0

        return r, g, b, a

    def vals(self):
        return self.r, self.g, self.b, self.opacity

    def __str__(self):
        r, g, b, a = self.ints()
        if a == 255:
            return "#%02x%02x%02x" % (r, g, b)
        else:
            return "#%02x%02x%02x%02x" % (r, g, b, a)

class HLS(AbstractColor):
    """A color in HLS (hue-lightness-saturation) representation.

    Signatures::

       HLS(h, l, s)    h, l, s are floating-point numbers between 0. and 1.

       HLS(rgb)        rgb is a color in RGB (red-green-blue) representation

       HLS(hls)        hls is another HLS color representation

       HLS(hsv)        hsv is a color in HSV (hue-saturation-value) representation

       RGB("name")     "name" is a CSS named color string

       RGB(\"#xxxxxx\")  \"#xxxxxx\" is a string in hexidecimal RGB space

    Keyword arguments:
       opacity (number between 0. and 1.)    opacity

    Behavior:

       Comparisons are value-based (two color objects are equal if
       they represent the same color).

       Can be cast as another color type or as a string (will return hex string).
    """
    def __init__(self, *args, **kwds):
        self.opacity = 1.

        if len(args) == 3:
            self.h, self.l, self.s = args

        elif len(args) == 1 and isinstance(args[0], RGB):
            self.h, self.l, self.s = colorsys.rgb_to_hls(args[0].r, args[0].g, args[0].b)
            self.opacity = args[0].opacity

        elif len(args) == 1 and isinstance(args[0], HLS):
            self.h, self.l, self.s = args[0].h, args[0].l, args[0].s
            self.opacity = args[0].opacity

        elif len(args) == 1 and isinstance(args[0], HSV):
            self.h, self.l, self.s = colorsys.rgb_to_hls(*colorsys.hsv_to_rgb(args[0].h, args[0].s, args[0].v))
            self.opacity = args[0].opacity

        elif len(args) == 1 and isinstance(args[0], basestring) and args[0][0] != "#":
            color = colors[args[0]]
            self.h, self.l, self.s = colorsys.rgb_to_hls(color.r, color.g, color.b)

        elif len(args) == 1 and isinstance(args[0], basestring) and args[0][0] == "#":
            r = int(args[0][1:3], 16)
            g = int(args[0][3:5], 16)
            b = int(args[0][5:7], 16)
            self.h, self.l, self.s = colorsys.rgb_to_hls(r/255., g/255., b/255.)

        else:
            raise TypeError, "HLS constructor arguments do not match any signature"

        if "opacity" in kwds:
            self.opacity = kwds["opacity"]
            del kwds["opacity"]

        if len(kwds) > 0:
            raise TypeError, "Unrecognized keyword arguments: %s" % str(kwds.keys())

    def __eq__(self, other):
        if isinstance(other, HLS):
            return self.h == other.h and self.l == other.l and self.s == other.s
        else:
            return self == HLS(other)

    def __hash__(self):
        return (self.h, self.l, self.s).__hash__()

    def __repr__(self):
        return "HLS(%g, %g, %g)" % (self.h, self.l, self.s)

    def vals(self):
        return self.h, self.l, self.s, self.opacity

    def __str__(self):
        return str(RGB(self))

class HSV(AbstractColor):
    """A color in HSV (hue-saturation-value) representation.

    Signatures::

       HSV(h, s, v)    h, s, v are floating-point numbers between 0. and 1.

       HSV(rgb)        rgb is a color in RGB (red-green-blue) representation

       HSV(hls)        hls is a color in HLS (hue-lightness-saturation) representation

       HSV(hsv)        hsv is another HSV color representation

       RGB("name")     "name" is a CSS named color string

       RGB(\"#xxxxxx\")  \"#xxxxxx\" is a string in hexidecimal RGB space

    Keyword arguments:
       opacity (number between 0. and 1.)    opacity

    Behavior:

       Comparisons are value-based (two color objects are equal if
       they represent the same color).

       Can be cast as another color type or as a string (will return hex string).
    """
    def __init__(self, *args, **kwds):
        self.opacity = 1.

        if len(args) == 3:
            self.h, self.s, self.v = args

        elif len(args) == 1 and isinstance(args[0], RGB):
            self.h, self.s, self.v = colorsys.rgb_to_hsv(args[0].r, args[0].g, args[0].b)
            self.opacity = args[0].opacity

        elif len(args) == 1 and isinstance(args[0], HLS):
            self.h, self.s, self.v = colorsys.rgb_to_hsv(*colorsys.hls_to_rgb(args[0].h, args[0].l, args[0].s))
            self.opacity = args[0].opacity

        elif len(args) == 1 and isinstance(args[0], HSV):
            self.h, self.s, self.v = args[0].h, args[0].s, args[0].v
            self.opacity = args[0].opacity

        elif len(args) == 1 and isinstance(args[0], basestring) and args[0][0] != "#":
            color = colors[args[0]]
            self.h, self.s, self.v = colorsys.rgb_to_hsv(color.r, color.g, color.b)

        elif len(args) == 1 and isinstance(args[0], basestring) and args[0][0] == "#":
            r = int(args[0][1:3], 16)
            g = int(args[0][3:5], 16)
            b = int(args[0][5:7], 16)
            self.h, self.s, self.v = colorsys.rgb_to_hsv(r/255., g/255., b/255.)

        else:
            raise TypeError, "HSV constructor arguments do not match any signature"

        if "opacity" in kwds:
            self.opacity = kwds["opacity"]
            del kwds["opacity"]

        if len(kwds) > 0:
            raise TypeError, "Unrecognized keyword arguments: %s" % str(kwds.keys())

    def __eq__(self, other):
        if isinstance(other, HSV):
            return self.h == other.h and self.s == other.s and self.v == other.v
        else:
            return self == HSV(other)

    def __hash__(self):
        return (self.h, self.s, self.v).__hash__()

    def __repr__(self):
        return "HSV(%g, %g, %g)" % (self.h, self.s, self.v)

    def vals(self):
        return self.h, self.s, self.v, self.opacity

    def __str__(self):
        return str(RGB(self))

def truncated_shift(value, shift):
    value += shift
    if value > 1.: return 1.
    if value < 0.: return 0.
    return value

def asymptotic_shift(value, shift):
    # cannot change from infinity (absorbing state)
    if value < 1e-5 or value > 1. - 1e-5: return value
    # convert from (0, 1) to an infinite interval
    value = math.tan(math.pi * (value - 0.5))
    # shift
    value += shift
    # convert back
    value = math.atan(value) / math.pi + 0.5
    return value

def lighten(color, amount=1., method=asymptotic_shift):
    if isinstance(color, basestring):
        color = RGB(color)

    originalclass = color.__class__
    hls = HLS(color)
    hls.l = method(hls.l, amount)

    return color.__class__(hls)

def darken(color, amount=1., method=asymptotic_shift):
    return lighten(color, -amount, method)

########################################################## colors

def _make_colors_list():
    colors = {
        "AliceBlue": RGB("#F0F8FF"),
        "AntiqueWhite": RGB("#FAEBD7"),
        "Aqua": RGB("#00FFFF"),
        "Aquamarine": RGB("#7FFFD4"),
        "Azure": RGB("#F0FFFF"),
        "Beige": RGB("#F5F5DC"),
        "Bisque": RGB("#FFE4C4"),
        "Black": RGB("#000000"),
        "BlanchedAlmond": RGB("#FFEBCD"),
        "Blue": RGB("#0000FF"),
        "BlueViolet": RGB("#8A2BE2"),
        "Brown": RGB("#A52A2A"),
        "BurlyWood": RGB("#DEB887"),
        "CadetBlue": RGB("#5F9EA0"),
        "Chartreuse": RGB("#7FFF00"),
        "Chocolate": RGB("#D2691E"),
        "Coral": RGB("#FF7F50"),
        "CornflowerBlue": RGB("#6495ED"),
        "Cornsilk": RGB("#FFF8DC"),
        "Crimson": RGB("#DC143C"),
        "Cyan": RGB("#00FFFF"),
        "DarkBlue": RGB("#00008B"),
        "DarkCyan": RGB("#008B8B"),
        "DarkGoldenRod": RGB("#B8860B"),
        "DarkGray": RGB("#A9A9A9"),
        "DarkGrey": RGB("#A9A9A9"),
        "DarkGreen": RGB("#006400"),
        "DarkKhaki": RGB("#BDB76B"),
        "DarkMagenta": RGB("#8B008B"),
        "DarkOliveGreen": RGB("#556B2F"),
        "Darkorange": RGB("#FF8C00"),
        "DarkOrchid": RGB("#9932CC"),
        "DarkRed": RGB("#8B0000"),
        "DarkSalmon": RGB("#E9967A"),
        "DarkSeaGreen": RGB("#8FBC8F"),
        "DarkSlateBlue": RGB("#483D8B"),
        "DarkSlateGray": RGB("#2F4F4F"),
        "DarkSlateGrey": RGB("#2F4F4F"),
        "DarkTurquoise": RGB("#00CED1"),
        "DarkViolet": RGB("#9400D3"),
        "DeepPink": RGB("#FF1493"),
        "DeepSkyBlue": RGB("#00BFFF"),
        "DimGray": RGB("#696969"),
        "DimGrey": RGB("#696969"),
        "DodgerBlue": RGB("#1E90FF"),
        "FireBrick": RGB("#B22222"),
        "FloralWhite": RGB("#FFFAF0"),
        "ForestGreen": RGB("#228B22"),
        "Fuchsia": RGB("#FF00FF"),
        "Gainsboro": RGB("#DCDCDC"),
        "GhostWhite": RGB("#F8F8FF"),
        "Gold": RGB("#FFD700"),
        "GoldenRod": RGB("#DAA520"),
        "Gray": RGB("#808080"),
        "Grey": RGB("#808080"),
        "Green": RGB("#008000"),
        "GreenYellow": RGB("#ADFF2F"),
        "HoneyDew": RGB("#F0FFF0"),
        "HotPink": RGB("#FF69B4"),
        "IndianRed": RGB("#CD5C5C"),
        "Indigo": RGB("#4B0082"),
        "Ivory": RGB("#FFFFF0"),
        "Khaki": RGB("#F0E68C"),
        "Lavender": RGB("#E6E6FA"),
        "LavenderBlush": RGB("#FFF0F5"),
        "LawnGreen": RGB("#7CFC00"),
        "LemonChiffon": RGB("#FFFACD"),
        "LightBlue": RGB("#ADD8E6"),
        "LightCoral": RGB("#F08080"),
        "LightCyan": RGB("#E0FFFF"),
        "LightGoldenRodYellow": RGB("#FAFAD2"),
        "LightGray": RGB("#D3D3D3"),
        "LightGrey": RGB("#D3D3D3"),
        "LightGreen": RGB("#90EE90"),
        "LightPink": RGB("#FFB6C1"),
        "LightSalmon": RGB("#FFA07A"),
        "LightSeaGreen": RGB("#20B2AA"),
        "LightSkyBlue": RGB("#87CEFA"),
        "LightSlateGray": RGB("#778899"),
        "LightSlateGrey": RGB("#778899"),
        "LightSteelBlue": RGB("#B0C4DE"),
        "LightYellow": RGB("#FFFFE0"),
        "Lime": RGB("#00FF00"),
        "LimeGreen": RGB("#32CD32"),
        "Linen": RGB("#FAF0E6"),
        "Magenta": RGB("#FF00FF"),
        "Maroon": RGB("#800000"),
        "MediumAquaMarine": RGB("#66CDAA"),
        "MediumBlue": RGB("#0000CD"),
        "MediumOrchid": RGB("#BA55D3"),
        "MediumPurple": RGB("#9370D8"),
        "MediumSeaGreen": RGB("#3CB371"),
        "MediumSlateBlue": RGB("#7B68EE"),
        "MediumSpringGreen": RGB("#00FA9A"),
        "MediumTurquoise": RGB("#48D1CC"),
        "MediumVioletRed": RGB("#C71585"),
        "MidnightBlue": RGB("#191970"),
        "MintCream": RGB("#F5FFFA"),
        "MistyRose": RGB("#FFE4E1"),
        "Moccasin": RGB("#FFE4B5"),
        "NavajoWhite": RGB("#FFDEAD"),
        "Navy": RGB("#000080"),
        "OldLace": RGB("#FDF5E6"),
        "Olive": RGB("#808000"),
        "OliveDrab": RGB("#6B8E23"),
        "Orange": RGB("#FFA500"),
        "OrangeRed": RGB("#FF4500"),
        "Orchid": RGB("#DA70D6"),
        "PaleGoldenRod": RGB("#EEE8AA"),
        "PaleGreen": RGB("#98FB98"),
        "PaleTurquoise": RGB("#AFEEEE"),
        "PaleVioletRed": RGB("#D87093"),
        "PapayaWhip": RGB("#FFEFD5"),
        "PeachPuff": RGB("#FFDAB9"),
        "Peru": RGB("#CD853F"),
        "Pink": RGB("#FFC0CB"),
        "Plum": RGB("#DDA0DD"),
        "PowderBlue": RGB("#B0E0E6"),
        "Purple": RGB("#800080"),
        "Red": RGB("#FF0000"),
        "RosyBrown": RGB("#BC8F8F"),
        "RoyalBlue": RGB("#4169E1"),
        "SaddleBrown": RGB("#8B4513"),
        "Salmon": RGB("#FA8072"),
        "SandyBrown": RGB("#F4A460"),
        "SeaGreen": RGB("#2E8B57"),
        "SeaShell": RGB("#FFF5EE"),
        "Sienna": RGB("#A0522D"),
        "Silver": RGB("#C0C0C0"),
        "SkyBlue": RGB("#87CEEB"),
        "SlateBlue": RGB("#6A5ACD"),
        "SlateGray": RGB("#708090"),
        "SlateGrey": RGB("#708090"),
        "Snow": RGB("#FFFAFA"),
        "SpringGreen": RGB("#00FF7F"),
        "SteelBlue": RGB("#4682B4"),
        "Tan": RGB("#D2B48C"),
        "Teal": RGB("#008080"),
        "Thistle": RGB("#D8BFD8"),
        "Tomato": RGB("#FF6347"),
        "Turquoise": RGB("#40E0D0"),
        "Violet": RGB("#EE82EE"),
        "Wheat": RGB("#F5DEB3"),
        "White": RGB("#FFFFFF"),
        "WhiteSmoke": RGB("#F5F5F5"),
        "Yellow": RGB("#FFFF00"),
        "YellowGreen": RGB("#9ACD32"),
        }

    # find duplicates and only include the original; this way, user
    # modifications to a color affects alternate spellings
    reverse = dict(map(lambda (x, y): (y, x), colors.items()))
    for color in colors.keys():
        colors[color] = colors[reverse[colors[color]]]

    for name, value in colors.items():
        colors[name.lower()] = value

    return colors

#: Table of CSS colors in `RGB` format; keys include both capitalized
#: and lower-case versions of the names and all variations in spelling
#: (but only one reference for each).
colors = _make_colors_list()

########################################################## color series

def gradient(stops, colors, name=None):
    if len(stops) != len(colors):
        raise ValueError, "The 'stops' and 'colors' must be the same length."

    if len(stops) < 2 or stops[0] != 0. or stops[-1] != 1.:
        raise ValueError, "The 'stops' array must begin with 0. and end with 1."

    val = stops[0]
    for stop in stops[1:]:
        if not (val < stop):
            raise ValueError, "The 'stops' array must be monatonically increasing."
        val = stop

    for color in colors[1:]:
        if color.__class__ is not colors[0].__class__:
            raise ValueError, "The 'colors' array must be homogeneous (all the same type of color objects)."

    if not isinstance(stops, numpy.ndarray):
        stops = numpy.array(stops, dtype=numpy.float)

    if isinstance(colors[0], RGB):
        fastcolors = numpy.empty((len(colors), 4))
        for i in xrange(len(colors)):
            r, g, b, a = colors[i].r*255, colors[i].g*255, colors[i].b*255, colors[i].opacity*255
            if r < 0.: r = 0.
            if r > 255.: r = 255.
            if g < 0.: g = 0.
            if g > 255.: g = 255.
            if b < 0.: b = 0.
            if b > 255.: b = 255.
            if a < 0.: a = 0.
            if a > 255.: a = 255.

            fastcolors[i] = (r, g, b, a)
            
        def colorseries(value, low, high):
            v = (value-low)/(high-low)
            if v <= 0.:
                return tuple(fastcolors[0])
            elif v >= 1.:
                return tuple(fastcolors[-1])
            else:
                for i in xrange(len(stops) - 1):
                    if stops[i] < v <= stops[i+1]:
                        break

                vv = (v - stops[i])/(stops[i+1] - stops[i])

                a1, b1, c1, d1 = fastcolors[i]
                a2, b2, c2, d2 = fastcolors[i+1]
                a = vv * (a2 - a1) + a1
                b = vv * (b2 - b1) + b1
                c = vv * (c2 - c1) + c1
                d = vv * (d2 - d1) + d1

                return int(math.floor(a)), int(math.floor(b)), int(math.floor(c)), int(math.floor(d))

    else:
        def colorseries(value, low, high):
            v = (value-low)/(high-low)
            if v <= 0.:
                return RGB(colors[0]).ints()
            elif v >= 1.:
                return RGB(colors[-1]).ints()
            else:
                for i in xrange(len(stops) - 1):
                    if stops[i] < v <= stops[i+1]:
                        break

                vv = (v - stops[i])/(stops[i+1] - stops[i])

                a1, b1, c1, d1 = colors[i].vals()
                a2, b2, c2, d2 = colors[i+1].vals()
                a = vv * (a2 - a1) + a1
                b = vv * (b2 - b1) + b1
                c = vv * (c2 - c1) + c1
                d = vv * (d2 - d1) + d1

                return RGB(colors[0].__class__(a, b, c, opacity=d)).ints()

    if name is not None:
        colorseries.func_name = name
    return colorseries

#: Table of gradient functions for one-component `Colorfields`;
#: all are functions that accept a value, minimum, and maximum, and
#: return a 4-tuple of integers (r,g,b,a)
gradients = {
    "grayscale": gradient([0., 1.], [RGB("white"), RGB("black")], "grayscale"),
    "antigrayscale": gradient([0., 1.], [RGB("black"), RGB("white")], "antigrayscale"),
    "reds": gradient([0., 1.], [RGB("white"), RGB("red")], "reds"),
    "antireds": gradient([0., 1.], [RGB("red"), RGB("white")], "antireds"),
    "greens": gradient([0., 1.], [RGB("white"), RGB("green")], "greens"),
    "antigreens": gradient([0., 1.], [RGB("green"), RGB("white")], "antigreens"),
    "blues": gradient([0., 1.], [RGB("white"), RGB("blue")], "blues"),
    "antiblues": gradient([0., 1.], [RGB("blue"), RGB("white")], "antiblues"),

    "rainbow": gradient([0., 0.34, 0.61, 0.84, 1.], [RGB(0., 0., 0.51), RGB(0., 0.81, 1.), RGB(0.87, 1., 0.12), RGB(1., 0.2, 0.), RGB(0.51, 0., 0.)], "rainbow"),
    "lightrainbow": gradient([0., 0.34, 0.61, 0.84, 1.], [RGB(0., 0., 0.51), RGB(0., 0.81, 1.), RGB(0.87, 1., 0.12), RGB(1., 0.2, 0.), RGB(1., 0., 0.)], "lightrainbow"),

    "fire": gradient([0., 0.15, 0.30, 0.40, 0.60, 1.], [RGB(0., 0., 0.), RGB(0.5, 0., 0.), RGB(1., 0., 0.), RGB(1., 0.2, 0.), RGB(1., 1., 0.), RGB(1., 1., 1.)], "fire"),
    "antifire": gradient([0., 0.15, 0.30, 0.40, 0.60, 1.], [RGB(1., 1., 1.), RGB(1., 1., 0.), RGB(1., 0.2, 0.), RGB(1., 0., 0.), RGB(0.5, 0., 0.), RGB(0., 0., 0.)], "antifire"),
    }

gradients["greyscale"] = gradients["grayscale"]
gradients["antigreyscale"] = gradients["antigrayscale"]

### auto-generate sequences of distinguishable colors

# darkcolors = [colors["DarkRed"], colors["Navy"], colors["DarkGreen"], colors["Purple"], colors["SaddleBrown"]]
# lightcolors = [colors["Tomato"], colors["DeepSkyBlue"], colors["LimeGreen"], colors["MediumOrchid"], colors["GoldenRod"]]

def darkseries(N, alternating=True, phase=0.05):
    if not (0. <= phase < 1.):
        raise ValueError, "The 'phase' must be in the interval [0., 1.)."
    def lightness(hue):
        return 0.5 - 0.3*math.exp(-(hue-0.3)**2/2./0.2**2) - 0.3*math.exp(-(hue-0.83)**2/2./0.05**2) - 0.1*math.exp(-(hue-0.53)**2/2./0.05**2) - 0.1*math.exp(-(hue-0.)**2/2./0.05**2) - 0.1*math.exp(-(hue-1.)**2/2./0.05**2)
    output = []
    for hue in map(lambda x: x/float(N), range(N)):
        hue += phase
        if hue > 1.: hue -= 1.
        output.append(HLS(hue, lightness(hue), 1.))
    if alternating:
        output.reverse()
        firsthalf = output[:(N//2)]
        secondhalf = output[(N//2):]
        output = []
        while len(firsthalf) + len(secondhalf) > 0:
            try:
                output.append(secondhalf.pop())
            except IndexError:
                pass
            try:
                output.append(firsthalf.pop())
            except IndexError:
                pass
    return map(RGB, output)

def lightseries(N, alternating=True, phase=0.17):
    if not (0. <= phase < 1.):
        raise ValueError, "The 'phase' must be in the interval [0., 1.)."
    def lightness(hue):
        return 0.65 + 0.15*math.exp(-(hue-0.67)**2/2./0.1**2) + 0.2*math.exp(-(hue-0.83)**2/2./0.05**2) + 0.1*math.exp(-(hue-0.)**2/2./0.05**2) + 0.1*math.exp(-(hue-1.)**2/2./0.05**2)
    output = []
    for hue in map(lambda x: x/float(N), range(N)):
        hue += phase
        if hue > 1.: hue -= 1.
        output.append(HLS(hue, lightness(hue), 1.))
    if alternating:
        output.reverse()
        firsthalf = output[:(N//2)]
        secondhalf = output[(N//2):]
        output = []
        while len(firsthalf) + len(secondhalf) > 0:
            try:
                output.append(secondhalf.pop())
            except IndexError:
                pass
            try:
                output.append(firsthalf.pop())
            except IndexError:
                pass
    return map(RGB, output)
