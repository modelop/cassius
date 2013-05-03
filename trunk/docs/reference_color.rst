.. automodule:: cassius.color

Manipulating color
------------------

Color representations
^^^^^^^^^^^^^^^^^^^^^

All function arguments that take a color argument (e.g. ``linecolor``,
``fillcolor``, ``markercolor``) can accept the name of a CSS color
string, an RGB hexidecimal color string, or a color object.  If a
string is given, the string will be written directly into the SVG
output, for the SVG renderer to interpret.  If a color object is
given, the object will be converted to a string by Cassius.  Whether
or not this makes a difference depends on the external SVG renderer
(it shouldn't).

Color classes are ``RGB`` (red-green-blue), ``HLS``
(hue-lightness-saturation), and ``HSV`` (hue-saturation-value).  Each
represents a color as three numbers in a different color space.
Conversions between color spaces are performed by type-casting.  All
three classes descend from a ``cassius.color.AbstractColor`` superclass.

Parameter values in color spaces are normalized to unit intervals, and
are floating point numbers (*not* integers from 0 to 255).

.. container::

   An example of color space conversion::

      >>> RGB(0.1, 0.2, 0.3)
      RGB(0.1, 0.2, 0.3)
      >>> HLS(RGB(0.1, 0.2, 0.3))
      HLS(0.583333, 0.2, 0.5)
      >>> RGB(HLS(RGB(0.1, 0.2, 0.3)))
      RGB(0.1, 0.2, 0.3)

Color objects can represent translucent colors with the ``opacity``
member; colors represented by strings have 100% opacity.

.. container::

   ::

      >>> from cassius import *
      >>> from random import gauss

      >>> background = Histogram(100, 0., 1., data=[gauss(0.7, 0.2) for i in xrange(10000)], fillcolor="lightblue")
      >>> foreground = Histogram(100, 0., 1., data=[gauss(0.5, 0.3) for i in xrange(10000)], fillcolor=RGB("red", opacity=0.5))

      >>> view(Overlay(background, foreground, frame=0))

   .. image:: PLOTS/Color_opacity.png

.. autoclass:: RGB
.. autoclass:: HLS
.. autoclass:: HSV

Color transformations
^^^^^^^^^^^^^^^^^^^^^

The following functions apply operations on colors.  For instance, if
two datasets are related, that relationship can be represented by
lighter and darker variants of the same color scheme.

.. container::

   The color of the diamond is a darkened version of the background color.

   ::

      >>> from cassius import *
      >>> everywhere = Region(MoveTo(-Infinity, -Infinity),
      ...                     EdgeTo(Infinity, -Infinity),
      ...                     EdgeTo(Infinity, Infinity),
      ...                     EdgeTo(-Infinity, Infinity),
      ...                     ClosePolygon())
      >>> diamond = Region(MoveTo(0, -1),
      ...                  EdgeTo(1, 0),
      ...                  EdgeTo(0, 1),
      ...                  EdgeTo(-1, 0),
      ...                  ClosePolygon())

      >>> diamond.fillcolor = darken(diamond.fillcolor)

      >>> view(Overlay(everywhere, diamond))

   .. image:: PLOTS/Color_darken.png

.. autofunction:: lighten
.. autofunction:: darken
.. autofunction:: truncated_shift
.. autofunction:: asymptotic_shift

Generation of color series
^^^^^^^^^^^^^^^^^^^^^^^^^^

The following functions generate series of smoothly varying colors,
for representing smooth relationships in data.  Gradients are usually
used in 2-D plots, darkseries and lightseries are usually used as
line/marker colors and fill colors, respectively.

All of the following functions are deterministic (not based on random
numbers).

.. autofunction:: gradient

.. container::

   A demonstration of three nice gradients (in the catologue below as
   "blues", "fire", and "rainbow", respectively).

   ::

      >>> from cassius import *
      >>> import numpy, copy

      >>> colorfield1 = ColorField(100, 0., 1., 1, 0., 1.)
      >>> colorfield1.values = numpy.array([[float(x)] for x in range(100)])
      >>> colorfield2 = copy.deepcopy(colorfield1)
      >>> colorfield3 = copy.deepcopy(colorfield1)

      >>> colorfield1.tocolor = gradient([0., 1.], [RGB("white"), RGB("blue")])

      >>> colorfield2.tocolor = gradient([0., 0.15, 0.30, 0.40, 0.60, 1.],
      ...                                [RGB(0., 0., 0.), RGB(0.5, 0., 0.), RGB(1., 0., 0.),
      ...                                 RGB(1., 0.2, 0.), RGB(1., 1., 0.), RGB(1., 1., 1.)])

      >>> colorfield3.tocolor = gradient([0., 0.34, 0.61, 0.84, 1.],
      ...                                [RGB(0., 0., 0.51), RGB(0., 0.81, 1.), RGB(0.87, 1., 0.12),
      ...                                 RGB(1., 0.2, 0.), RGB(0.51, 0., 0.)])

      >>> view(Layout(3, 1, colorfield1, colorfield2, colorfield3), bottommargin=0.2)

   .. image:: PLOTS/Color_gradients.png

.. autofunction:: darkseries
.. autofunction:: lightseries

.. container::

   A typical use for ``lightseries``: fill colors for histograms.

   ::

      >>> from cassius import *

      >>> for x in lightseries(5):
      ...    print repr(x)
      ... 
      RGB(0.986012, 1, 0.300619)
      RGB(0.877133, 0.676665, 1)
      RGB(0.303333, 1, 0.4566)
      RGB(1, 0.478323, 0.572225)
      RGB(0.48196, 0.782423, 1)

      >>> from random import gauss
      >>> histograms = [Histogram(100, 0., 1., data=[gauss(0.3, 0.3) for i in xrange(10000)]),
      ...               Histogram(100, 0., 1., data=[gauss(0.7, 0.3) for i in xrange(10000)]),
      ...               Histogram(100, 0., 1., data=[gauss(0.4, 0.2) for i in xrange(10000)]),
      ...               Histogram(100, 0., 1., data=[gauss(0.9, 0.2) for i in xrange(10000)]),
      ...               Histogram(100, 0., 1., data=[gauss(0.2, 0.1) for i in xrange(10000)])]

      >>> view(Stack(*histograms, fillcolors=lightseries(5)))

   .. image:: PLOTS/Color_lightseries.png

Catologues of colors and gradients
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

The following data members are tables of standard colors and
gradients.  Both are dictionaries whose keys are names and values are
colors or gradient functions.

The difference between

::

   >>> plot.fillcolor = "lightblue"

and

::

   >>> plot.fillcolor = colors["lightblue"]

is that the latter is an ``RGB`` color object, converted by Cassius
into a hexidecimal string in the SVG.  In the first case, "lightblue"
is put into the SVG output, for the external SVG renderer to
interpret.  The ``colors`` table is derived from the CSS standard, so
if all SVG renderers are operating correctly, the resulting colors
produced by the two cases would be the same.

.. autodata:: colors

.. container::

   A listing of all colors.  (Capitalized and lower-case versions of
   each name point to the same ``RGB`` object.)  This list was derived
   from `CSS Color Names <http://www.w3schools.com/css/css_colornames.asp>`_ and is
   not likely to change in future versions.

   ::
      
      >>> names = colors.keys()
      >>> names.sort()
      >>> names
      ['AliceBlue', 'AntiqueWhite', 'Aqua', 'Aquamarine', 'Azure', 'Beige',
       'Bisque', 'Black', 'BlanchedAlmond', 'Blue', 'BlueViolet', 'Brown',
       'BurlyWood', 'CadetBlue', 'Chartreuse', 'Chocolate', 'Coral',
       'CornflowerBlue', 'Cornsilk', 'Crimson', 'Cyan', 'DarkBlue',
       'DarkCyan', 'DarkGoldenRod', 'DarkGray', 'DarkGreen', 'DarkGrey',
       'DarkKhaki', 'DarkMagenta', 'DarkOliveGreen', 'DarkOrchid',
       'DarkRed', 'DarkSalmon', 'DarkSeaGreen', 'DarkSlateBlue',
       'DarkSlateGray', 'DarkSlateGrey', 'DarkTurquoise', 'DarkViolet',
       'Darkorange', 'DeepPink', 'DeepSkyBlue', 'DimGray', 'DimGrey',
       'DodgerBlue', 'FireBrick', 'FloralWhite', 'ForestGreen', 'Fuchsia',
       'Gainsboro', 'GhostWhite', 'Gold', 'GoldenRod', 'Gray', 'Green',
       'GreenYellow', 'Grey', 'HoneyDew', 'HotPink', 'IndianRed', 'Indigo',
       'Ivory', 'Khaki', 'Lavender', 'LavenderBlush', 'LawnGreen',
       'LemonChiffon', 'LightBlue', 'LightCoral', 'LightCyan',
       'LightGoldenRodYellow', 'LightGray', 'LightGreen', 'LightGrey',
       'LightPink', 'LightSalmon', 'LightSeaGreen', 'LightSkyBlue',
       'LightSlateGray', 'LightSlateGrey', 'LightSteelBlue', 'LightYellow',
       'Lime', 'LimeGreen', 'Linen', 'Magenta', 'Maroon',
       'MediumAquaMarine', 'MediumBlue', 'MediumOrchid', 'MediumPurple',
       'MediumSeaGreen', 'MediumSlateBlue', 'MediumSpringGreen',
       'MediumTurquoise', 'MediumVioletRed', 'MidnightBlue', 'MintCream',
       'MistyRose', 'Moccasin', 'NavajoWhite', 'Navy', 'OldLace', 'Olive',
       'OliveDrab', 'Orange', 'OrangeRed', 'Orchid', 'PaleGoldenRod',
       'PaleGreen', 'PaleTurquoise', 'PaleVioletRed', 'PapayaWhip',
       'PeachPuff', 'Peru', 'Pink', 'Plum', 'PowderBlue', 'Purple', 'Red',
       'RosyBrown', 'RoyalBlue', 'SaddleBrown', 'Salmon', 'SandyBrown',
       'SeaGreen', 'SeaShell', 'Sienna', 'Silver', 'SkyBlue', 'SlateBlue',
       'SlateGray', 'SlateGrey', 'Snow', 'SpringGreen', 'SteelBlue', 'Tan',
       'Teal', 'Thistle', 'Tomato', 'Turquoise', 'Violet', 'Wheat', 'White',
       'WhiteSmoke', 'Yellow', 'YellowGreen', 'aliceblue', 'antiquewhite',
       'aqua', 'aquamarine', 'azure', 'beige', 'bisque', 'black',
       'blanchedalmond', 'blue', 'blueviolet', 'brown', 'burlywood',
       'cadetblue', 'chartreuse', 'chocolate', 'coral', 'cornflowerblue',
       'cornsilk', 'crimson', 'cyan', 'darkblue', 'darkcyan',
       'darkgoldenrod', 'darkgray', 'darkgreen', 'darkgrey', 'darkkhaki',
       'darkmagenta', 'darkolivegreen', 'darkorange', 'darkorchid',
       'darkred', 'darksalmon', 'darkseagreen', 'darkslateblue',
       'darkslategray', 'darkslategrey', 'darkturquoise', 'darkviolet',
       'deeppink', 'deepskyblue', 'dimgray', 'dimgrey', 'dodgerblue',
       'firebrick', 'floralwhite', 'forestgreen', 'fuchsia', 'gainsboro',
       'ghostwhite', 'gold', 'goldenrod', 'gray', 'green', 'greenyellow',
       'grey', 'honeydew', 'hotpink', 'indianred', 'indigo', 'ivory',
       'khaki', 'lavender', 'lavenderblush', 'lawngreen', 'lemonchiffon',
       'lightblue', 'lightcoral', 'lightcyan', 'lightgoldenrodyellow',
       'lightgray', 'lightgreen', 'lightgrey', 'lightpink', 'lightsalmon',
       'lightseagreen', 'lightskyblue', 'lightslategray', 'lightslategrey',
       'lightsteelblue', 'lightyellow', 'lime', 'limegreen', 'linen',
       'magenta', 'maroon', 'mediumaquamarine', 'mediumblue',
       'mediumorchid', 'mediumpurple', 'mediumseagreen', 'mediumslateblue',
       'mediumspringgreen', 'mediumturquoise', 'mediumvioletred',
       'midnightblue', 'mintcream', 'mistyrose', 'moccasin', 'navajowhite',
       'navy', 'oldlace', 'olive', 'olivedrab', 'orange', 'orangered',
       'orchid', 'palegoldenrod', 'palegreen', 'paleturquoise',
       'palevioletred', 'papayawhip', 'peachpuff', 'peru', 'pink', 'plum',
       'powderblue', 'purple', 'red', 'rosybrown', 'royalblue',
       'saddlebrown', 'salmon', 'sandybrown', 'seagreen', 'seashell',
       'sienna', 'silver', 'skyblue', 'slateblue', 'slategray', 'slategrey',
       'snow', 'springgreen', 'steelblue', 'tan', 'teal', 'thistle',
       'tomato', 'turquoise', 'violet', 'wheat', 'white', 'whitesmoke',
       'yellow', 'yellowgreen']

.. autodata:: gradients

.. container::

   A listing of all gradients.  New gradients will likely be added in
   future versions.

   ::
      
      >>> names = gradients.keys()
      >>> names.sort()
      >>> names
      ['antiblues', 'antifire', 'antigrayscale', 'antigreens',
      'antigreyscale', 'antireds', 'blues', 'fire', 'grayscale', 'greens',
      'greyscale', 'lightrainbow', 'rainbow', 'reds']
