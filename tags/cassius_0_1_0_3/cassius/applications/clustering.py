import math
import numpy
import numpy.linalg

import cassius.containers as containers
import cassius.mathtools as mathtools
import cassius.color as color
from cassius.containers import Auto

import augustus.core.pmml41 as pmml

def _autoAxis(values):
    originN, xscale, xbasis, yscale, ybasis = mathtools.principleComponents(values)
    
    [xorigin], [yorigin] = (numpy.matrix([xbasis, ybasis]) * numpy.matrix(originN).T).tolist()
    xmin = xorigin - 3.*xscale
    xmax = xorigin + 3.*xscale
    ymin = yorigin - 3.*yscale
    ymax = yorigin + 3.*yscale

    return xbasis, ybasis, originN, xorigin, xmin, xmax, yorigin, ymin, ymax

def _replaceParams(values, xbasis, ybasis, origin, xmin, xmax, ymin, ymax):
    replacements = list(_autoAxis(values))

    if xbasis is not Auto: replacements[0] = xbasis
    if ybasis is not Auto: replacements[1] = ybasis
    if xmin is not Auto: replacements[4] = xmin
    if xmax is not Auto: replacements[5] = xmax
    if ymin is not Auto: replacements[7] = ymin
    if ymax is not Auto: replacements[8] = ymax

    xbasis, ybasis, originN, xorigin, xmin, xmax, yorigin, ymin, ymax = replacements

    if origin is Auto:
        origin = numpy.matrix(originN).T - (numpy.matrix([xbasis, ybasis]).I * numpy.matrix([[xorigin], [yorigin]]))
        origin = origin.T.tolist()[0]

    return xbasis, ybasis, origin, xmin, xmax, ymin, ymax

def _replaceLabel(basis, features):
    if features is None:
        features = [None] * len(basis)

    elif len(features) != len(basis):
        raise containers.ContainerException, "Length of feature names (%d) must equal the number of cluster fields (%d)" % (len(features), len(basis))

    maxBasis = max(map(abs, basis))
    label = []
    for i, (coefficient, feature) in enumerate(zip(basis, features)):
        if abs(coefficient) > 0.01 * maxBasis:
            term = "%g " % mathtools.round_sigfigs(coefficient, 2)
            term = term.replace("-", u"\u2212")
            if feature is None:
                term += "x%s" % unichr(0x2080 + i)
            else:
                term += feature
            label.append(term)
    label = " + ".join(label)
    return label

def ClusterModelMap(model, xbasis=Auto, ybasis=Auto, origin=Auto, xbins=300, xmin=Auto, xmax=Auto, xlabel=Auto, ybins=300, ymin=Auto, ymax=Auto, ylabel=Auto, colors=Auto, bordercolor="black", smooth=True, features=None, **kwds):
    if Auto in (xbasis, ybasis, origin, xmin, xmax, ymin, ymax):
        values = [i.value for i in model.cluster]
        xbasis, ybasis, origin, xmin, xmax, ymin, ymax = \
                _replaceParams(values, xbasis, ybasis, origin, xmin, xmax, ymin, ymax)

    if features is None:
        features = [i["field"] for i in model.matches(pmml.ClusteringField)]

    if xlabel is Auto: xlabel = _replaceLabel(xbasis, features)
    if ylabel is Auto: ylabel = _replaceLabel(ybasis, features)

    if len(xbasis) != model.numberOfFields or len(ybasis) != model.numberOfFields or len(origin) != model.numberOfFields:
        raise containers.ContainerException, "The xbasis (%d), ybasis (%d), and origin (%d) must have the same dimension as the model, which is %d" % (len(xbasis), len(ybasis), len(origin), model.numberOfFields)
    N = model.numberOfFields

    validationResults = model.validate()
    if validationResults is not None:
        raise RuntimeError, "PMML model not valid: %s at treeindex %s" % (validationResults[0], tuple(validationResults[1]))

    if not model["modelClass"] == "centerBased":
        raise NotImplementedError, "ClusterModelMap has only been implemented for 'centerBased' ClusteringModels (see attribute 'modelClass')"

    if not model.child(pmml.ComparisonMeasure)["kind"] == "distance":
        raise NotImplementedError, "ClusterModelMap has only been implemented for 'distance' ComparisonMeasures (see attribute 'kind')"

    categories = list(model.ids)

    projection = numpy.matrix([xbasis, ybasis])
    antiProjection = projection.I
    origin = numpy.matrix(origin).T

    categorizer = lambda x, y: model.closestCluster(((antiProjection * numpy.matrix([[x], [y]])) + origin).A.reshape(N).tolist())[0]

    kwds.update({"xlabel": xlabel, "ylabel": ylabel})
    return containers.RegionMap(xbins, xmin, xmax, ybins, ymin, ymax, categories, categorizer, colors, bordercolor, smooth, **kwds)
    
def ClusterDataScatter(values, xbasis=Auto, ybasis=Auto, origin=Auto, xmin=Auto, xmax=Auto, xlabel=Auto, ymin=Auto, ymax=Auto, ylabel=Auto, maxDistance=None, metric=Auto, limit=None, features=None, **kwds):
    if Auto in (xbasis, ybasis, origin, xmin, xmax, ymin, ymax):
        xbasis, ybasis, origin, xmin, xmax, ymin, ymax = \
                _replaceParams(values, xbasis, ybasis, origin, xmin, xmax, ymin, ymax)

    if xlabel is Auto: xlabel = _replaceLabel(xbasis, features)
    if ylabel is Auto: ylabel = _replaceLabel(ybasis, features)

    if len(xbasis) != len(values[0]) or len(ybasis) != len(values[0]) or len(origin) != len(values[0]):
        raise containers.ContainerException, "The xbasis (%d), ybasis (%d), and origin (%d) must have the same dimension as the data, which is %d (first item, at least...)" % (len(xbasis), len(ybasis), len(origin), len(values[0]))
    N = len(values[0])
    values = numpy.array(values)

    projection = numpy.matrix([xbasis, ybasis])
    origin = numpy.matrix(origin).T

    if maxDistance is not None and len(values) > 0:
        antiProjection = projection.I
        squish = antiProjection * projection  # squish it onto the plane: this is not the identity because antiProjection is a right-inverse

        planeValues = numpy.apply_along_axis(lambda value: ((squish * (numpy.matrix(value).T - origin)) + origin).A.reshape(N), 1, values)

        if metric is Auto:
            # default to an optimized euclidean
            distances = numpy.apply_along_axis(lambda value: math.sqrt(numpy.sum(value**2)), 1, values - planeValues)
        else:
            zero = numpy.zeros(N)
            distances = numpy.apply_along_axis(lambda value: metric(value, zero), 1, values - planeValues)

        values = values[distances < maxDistance]

    if len(values) > 0:
        values = numpy.apply_along_axis(lambda value: (projection * (numpy.matrix(value).T - origin)).A.reshape(2), 1, values)

    kwds.update({"xmin": xmin, "xmax": xmax, "xlabel": xlabel, "ymin": ymin, "ymax": ymax, "ylabel": ylabel, "limit": limit})
    return containers.Scatter(values, ("x", "y"), **kwds)

def ClusterOverlay(model, values, xbasis=Auto, ybasis=Auto, origin=Auto, xbins=300, xmin=Auto, xmax=Auto, xlabel=Auto, ybins=300, ymin=Auto, ymax=Auto, ylabel=Auto, maxDistance=None, metric=Auto, limit=None, colors=Auto, bordercolor="black", smooth=True, features=None, **kwds):
    if Auto in (xbasis, ybasis, origin, xmin, xmax, ymin, ymax):
        xbasis, ybasis, origin, xmin, xmax, ymin, ymax = \
                _replaceParams(values, xbasis, ybasis, origin, xmin, xmax, ymin, ymax)

    if features is None:
        features = [i["field"] for i in model.matches(pmml.ClusteringField)]

    if xlabel is Auto: xlabel = _replaceLabel(xbasis, features)
    if ylabel is Auto: ylabel = _replaceLabel(ybasis, features)

    modelMap = ClusterModelMap(model, xbasis, ybasis, origin, xbins, xmin, xmax, xlabel, ybins, ymin, ymax, ylabel, colors, bordercolor, smooth)
    dataScatter = ClusterDataScatter(values, xbasis, ybasis, origin, xmin, xmax, xlabel, ymin, ymax, ylabel, maxDistance, metric, limit)

    colors = modelMap.colors
    if colors is Auto:
        colors = color.lightseries(len(modelMap.categories), alternating=False)
    fields = [[dataScatter, "data"]]
    for col, category in zip(colors, modelMap.categories):
        fields.append([containers.Style(linecolor=bordercolor, fillcolor=col), category])
    legend = containers.Legend(fields, colwid=[0.3, 0.7], justify="cl")

    return containers.Overlay(0, modelMap, dataScatter, legend)
