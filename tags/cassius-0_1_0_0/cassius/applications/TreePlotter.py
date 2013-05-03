import numpy

from cassius import *
from cassius.color import lighten

def dataFileName(config):
    def finddata(element):
        if element.tag == "data" and "file" in element.attrib:
            return element.attrib["file"]
        else:
            for child in element:
                search = finddata(child)
                if search is not None: return search
        return None
    return finddata(config.getroot())

def categoryLabel(pmml):
    for child in pmml.find("TreeModel").find("MiningSchema"):
        if child.tag == "MiningField" and child.attrib.get("usageType") == "predicted":
            return child.attrib["name"]

class Rect:
    def __init__(self, xmin, xmax, ymin, ymax):
        self.xmin, self.xmax, self.ymin, self.ymax = xmin, xmax, ymin, ymax

    def __repr__(self):
        xmin, xmax, ymin, ymax = self.xmin, self.xmax, self.ymin, self.ymax
        if xmin is None: xmin = "-oo"
        else: xmin = "%g" % xmin
        if xmax is None: xmax = "oo"
        else: xmax = "%g" % xmax
        if ymin is None: ymin = "-oo"
        else: ymin = "%g" % ymin
        if ymax is None: ymax = "oo"
        else: ymax = "%g" % ymax
        return "Rect(%s to %s, %s to %s)" % (xmin, xmax, ymin, ymax)

    def intersect(self, other):
        if self.xmin is None:
            xmin = other.xmin
        elif other.xmin is None:
            xmin = self.xmin
        else:
            xmin = max(self.xmin, other.xmin)

        if self.xmax is None:
            xmax = other.xmax
        elif other.xmax is None:
            xmax = self.xmax
        else:
            xmax = min(self.xmax, other.xmax)

        if self.ymin is None:
            ymin = other.ymin
        elif other.ymin is None:
            ymin = self.ymin
        else:
            ymin = max(self.ymin, other.ymin)

        if self.ymax is None:
            ymax = other.ymax
        elif other.ymax is None:
            ymax = self.ymax
        else:
            ymax = min(self.ymax, other.ymax)

        return Rect(xmin, xmax, ymin, ymax)

    def path(self):
        xmin, xmax, ymin, ymax = self.xmin, self.xmax, self.ymin, self.ymax
        if xmin is None: xmin = -Infinity
        if xmax is None: xmax = Infinity
        if ymin is None: ymin = -Infinity
        if ymax is None: ymax = Infinity
        return [MoveTo(xmin, ymin), EdgeTo(xmax, ymin), EdgeTo(xmax, ymax), EdgeTo(xmin, ymax), ClosePolygon()]

def describeTree(pmml, featureX, featureY, feature_means, categories):
    regions = {}
    for category in categories:
        regions[category] = []

    def recurse(node, rect):
        satisfies_others = True
        xmin, xmax, ymin, ymax = None, None, None, None

        predicate = node.find("SimplePredicate")
        if predicate is not None:
            if predicate.attrib["field"] == featureX:
                if predicate.attrib["operator"] == "lessOrEqual":
                    xmax = float(predicate.attrib["value"])
                elif predicate.attrib["operator"] == "greaterThan":
                    xmin = float(predicate.attrib["value"])

            elif predicate.attrib["field"] == featureY:
                if predicate.attrib["operator"] == "lessOrEqual":
                    ymax = float(predicate.attrib["value"])
                elif predicate.attrib["operator"] == "greaterThan":
                    ymin = float(predicate.attrib["value"])

            elif predicate.attrib["field"] in feature_means:
                mean = feature_means[predicate.attrib["field"]]
                cut = float(predicate.attrib["value"])
                if predicate.attrib["operator"] == "lessThan": satisfies_others = satisfies_others and mean < cut
                if predicate.attrib["operator"] == "lessOrEqual": satisfies_others = satisfies_others and mean <= cut
                if predicate.attrib["operator"] == "greaterThan": satisfies_others = satisfies_others and mean > cut
                if predicate.attrib["operator"] == "greaterOrEqual": satisfies_others = satisfies_others and mean >= cut

        if satisfies_others:
            rect = rect.intersect(Rect(xmin, xmax, ymin, ymax))

            if node.find("Node") is None:
                category = node.attrib["score"]
                regions[category].append(rect)

            else:
                for child in node:
                    if child.tag == "Node":
                        recurse(child, rect)

    recurse(pmml.find("TreeModel").find("Node"), Rect(None, None, None, None))
    return regions

def findFeatures(pmml):
    optype = {}
    for child in pmml.find("DataDictionary"):
        if child.tag == "DataField":
            optype[child.attrib["name"]] = child.attrib["optype"]

    continuous_features, categorical_features = [], []
    for child in pmml.find("TreeModel").find("MiningSchema"):
        if child.tag == "MiningField" and child.attrib.get("usageType") != "predicted":
            if optype[child.attrib["name"]] == "continuous":
                continuous_features.append(child.attrib["name"])
            elif optype[child.attrib["name"]] == "categorical":
                categorical_features.append(child.attrib["name"])
    return continuous_features, categorical_features

def all_categories(data, category_label):
    return numpy.unique(data.field(category_label))

def ranges_mask(data, ranges):
    ranges_mask = numpy.ones(len(data), dtype=numpy.bool)
    for feature, low, high in ranges:
        onemask = numpy.logical_and(low < data.field(feature), data.field(feature) < high)
        numpy.logical_and(ranges_mask, onemask, ranges_mask)
    return ranges_mask

def means(data, continuous_features, ranges_mask):
    output = {}
    for feature in continuous_features:
        selected_data = data.field(feature)[ranges_mask]
        if len(selected_data) > 0:
            output[feature] = numpy.sum(selected_data)/float(len(selected_data))
        else:
            output[feature] = None
    return output

def scatterplots(data, featureX, featureY, ranges_mask, categories, category_colors, category_markers, category_label="CATEGORY", markeroutline="black"):
    plots = []
    for category in categories:
        mask = numpy.logical_and(ranges_mask, data.field(category_label) == category)
        scatter = Scatter(x=data.field(featureX)[mask], y=data.field(featureY)[mask], limit=100, marker=category_markers[category], markercolor=category_colors[category], markeroutline=markeroutline)
        plots.append(scatter)

    return Overlay(*plots, xlabel=featureX, ylabel=featureY)

def regionplots(pmml, featureX, featureY, feature_means, categories, category_colors, lightening=3.):
    regions = describeTree(pmml, featureX, featureY, feature_means, categories)

    plots = []
    for category, rects in regions.items():
        plot = Region(*sum([i.path() for i in rects], []), fillcolor=lighten(category_colors[category], lightening))
        plots.append(plot)

    return Overlay(*plots, xlabel=featureX, ylabel=featureY)

def regionlegend(categories, category_colors, category_markers, featureX, featureY, continuous_features, feature_means):
    legend_data = []
    for category in categories:
        legend_data.append([category, Style(marker=category_markers[category],
                                            markercolor=category_colors[category],
                                            markeroutline="black",
                                            fillcolor=lighten(category_colors[category], 3.))])
    for feature in continuous_features:
        if feature != featureX and feature != featureY:
            legend_data.append([feature, str_sigfigs(feature_means[feature], 2)])

    return Legend(legend_data, justify="lc", colwid=[0.8, 0.2])



#######################################################
# for testing
#######################################################

# import xml.etree.ElementTree
# from augustus.kernel.unitable import UniTable
# from cassius.backends.svg import view

# data = UniTable().load(dataFileName(xml.etree.ElementTree.ElementTree(file="tree_iris_config_3.xml")))
# pmml = xml.etree.ElementTree.ElementTree(file="iris_binarytree_3.pmml")
# continuous_features, categorical_features = findFeatures(pmml)
# category_label = categoryLabel(pmml)

# categories = all_categories(data, category_label)
# category_colors = dict(zip(categories, ["red", "blue", "green", "purple", "yellow", "gray", "fuchsia", "white"]))
# category_markers = dict(zip(categories, ["circle", "circle", "circle", "circle", "circle", "circle", "circle", "circle"]))

# ranges = ranges_mask(data, [])
# feature_means = means(data, continuous_features, ranges)

# scatterplot = scatterplots(data=data,
#                            featureX="SEPAL_LENGTH",
#                            featureY="SEPAL_WIDTH",
#                            ranges_mask=ranges,
#                            categories=categories,
#                            category_colors=category_colors,
#                            category_markers=category_markers,
#                            category_label=category_label,
#                            markeroutline="black",
#                            )

# regionplot = regionplots(pmml, "SEPAL_LENGTH", "SEPAL_WIDTH", feature_means, categories, category_colors)

# legend = regionlegend(categories, category_colors, category_markers, "SEPAL_LENGTH", "SEPAL_WIDTH", continuous_features, feature_means)

# view(Overlay(regionplot, scatterplot, legend, frame=-2))
