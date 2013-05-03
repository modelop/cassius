# Standard Python packages
import subprocess, os
try:
    import xml.etree.cElementTree as ElementTree
except ImportError:
    import xml.etree.cElementTree as ElementTree

# Special dependencies
import numpy # sudo apt-get install python-numpy

# Cassius interdependencies
import cassius.mathtools
import cassius.utilities
import cassius.color
import cassius.containers

class ScorePlane:
    """Calls AugustusPMMLConsumer on all points in a plane of feature-space and returns the result for plotting.

    Arguments:
       pmmlModel (string): name of the PMML model to evaluate

       unitable (InspectTable): dataset to overlay on the scored plane

       featureX (string or `None`): name of the feature to plot on the
       X axis (attempts to guess if `None`)

       xmin, xmax (numbers or `None`): minimum and maximum X values
       (guesses from the data if `None`)

       featureY (string or `None`): name of the feature to plot on the
       Y axis (attempts to guess if `None`)

       ymin, ymax (numbers or `None`): minimum and maximum Y values
       (guesses from the data if `None`)

       othervalue (dict): option values of the features that are not
       plotted as {"feature1": value1, "feature2": value2} (if
       unspecified, the mean value is used)

       cuts (string or `None`): cuts to apply as an arbitrary
       expression or `None` for no cuts

       numbins (int): number of bins in x and y (total number is bins**2)

       limit (int or `None`): limit the number of data points in each
       category to plot

       configFileName (string): configuration file for AugustusPMMLConsumer

       planeFileName (string): file of values to score

       outputFileName (string): output file from AugustusPMMLConsumer

    Behavior:
       Constructor only configures the object; no action is taken
       until `configure` or `score` are called.
    """

    def __init__(self, pmmlModel, unitable, featureX=None, xmin=None, xmax=None, featureY=None, ymin=None, ymax=None, othervalue={}, cuts=None, numbins=300, limit=1000, configFileName="/tmp/consume.xml", planeFileName="/tmp/plane.csv", outputFileName="/tmp/scores.xml"):
        self.pmmlModel, self.unitable, self.featureX, self.xmin, self.xmax, self.featureY, self.ymin, self.ymax, self.othervalue, self.cuts, self.numbins, self.limit, self.configFileName, self.planeFileName, self.outputFileName = pmmlModel, unitable, featureX, xmin, xmax, featureY, ymin, ymax, othervalue, cuts, numbins, limit, configFileName, planeFileName, outputFileName

    def score(self, dryrun=False):
        """Creates configuration files and runs AugustusPMMLConsumer.

        Arguments:
           dryrun (bool): if True, only set up the configuration
           files; don't run AugustusPMMLConsumer

        Sets the following member data:
           plot (Overlay): the final plot, call `view(scoreplane.plot)`

           regionplot (RegionMap): just the pixel-map of scored regions

           scatterplots (list of Scatter): the data points with each
           category in a separate plot

           legend (Legend): plot legend

           stdout (string): standard output from AugustusPMMLConsumer

           stderr (string): standard error from AugustusPMMLConsumer

           scores (ElementTree): output of AugustusPMMLConsumer,
           parsed from the XML
        """

        # 0. Preliminaries
        def findModel(pmml):
            for m in "MiningModel", "TreeModel", "ClusteringModel":
                if pmml.find(m) is not None:
                    return pmml.find(m)

        def findFeatures(pmmlModel):
            pmml = ElementTree.ElementTree(file=pmmlModel)
            optype = {}
            for child in pmml.find("DataDictionary"):
                if child.tag == "DataField":
                    optype[child.attrib["name"]] = child.attrib["optype"]

            continuous_features, categorical_features = [], []
            for child in findModel(pmml).find("MiningSchema"):
                if child.tag == "MiningField" and child.attrib.get("usageType") != "predicted":
                    if optype[child.attrib["name"]] == "continuous":
                        continuous_features.append(child.attrib["name"])
                    elif optype[child.attrib["name"]] == "categorical":
                        categorical_features.append(child.attrib["name"])
            return continuous_features, categorical_features

        continuous_features, categorical_features = findFeatures(self.pmmlModel)

        if self.featureX is None:
            for feature in continuous_features:
                if feature != self.featureY:
                    self.featureX = feature
                    break
        if self.featureY is None:
            for feature in continuous_features:
                if feature != self.featureX:
                    self.featureY = feature
                    break
        if self.featureX is None or self.featureY is None:
            raise ValueError, "There must be at least two continuous features in the PMML file."
        otherfields = []
        othervalues = []

        for feature in continuous_features + categorical_features:
            if feature != self.featureX and feature != self.featureY:
                if feature in self.othervalue:
                    otherfields.append(feature)
                    othervalues.append(self.othervalue[feature])

                else:
                    otherfields.append(feature)
                    if self.cuts is None:
                        low, high = cassius.utilities.calcrange_quartile(self.unitable.field(feature))
                        if low == high:
                            low, high = min(self.unitable.field(feature)), max(self.unitable.field(feature))
                            if low == high:
                                raise ValueError, "Feature %s does not have any dynamic range: %g %g" % (feature, low, high)

                        cuts = "(%g < %s) & (%s < %g)" % (low, feature, feature, high)
                    else:
                        low, high = cassius.utilities.calcrange_quartile(self.unitable(feature, self.cuts))
                        if low == high:
                            low, high = min(self.unitable.field(feature)), max(self.unitable(feature, self.cuts))
                            if low == high:
                                raise ValueError, "Feature %s with cuts \"%s\" does not have any dynamic range: %g %g" % (feature, self.cuts, low, high)

                        cuts = "(%g < %s) & (%s < %g)" % (low, feature, feature, high)
                        cuts += " & (%s)" % self.cuts

                    if feature in continuous_features:
                        othervalues.append(cassius.mathtools.mean(self.unitable(feature, cuts)))
                    else:
                        othervalues.append(cassius.mathtools.ubiquitous(self.unitable(feature, cuts)))

        def categoryLabel(pmmlModel):
            pmml = ElementTree.ElementTree(file=pmmlModel)
            def recurse(node):
                if node.tag == "MiningField" and node.attrib.get("usageType") == "predicted":
                    raise StopIteration, node.attrib.get("name")
                for child in node.getchildren():
                    recurse(child)
            try:
                recurse(pmml.getroot())
            except StopIteration, name:
                return str(name)
            raise RuntimeError, "Predicted field not found in PMML."

        clusteringModel = ElementTree.ElementTree(file=self.pmmlModel).getroot().find("ClusteringModel")
        if clusteringModel is None:
            try:
                clusteringModel = ElementTree.ElementTree(file=self.pmmlModel).getroot().find("MiningModel").find("Segmentation").find("Segment").find("ClusteringModel")
            except AttributeError:
                pass
        
        if clusteringModel is not None:
            numberOfClusters = int(clusteringModel.attrib["numberOfClusters"])
            categories = ["category_%02d" % i for i in range(numberOfClusters)]
        else:
            predictedField = categoryLabel(self.pmmlModel)
            categories = numpy.unique(self.unitable.field(predictedField))
        
        categories.sort()
        category_lookup = dict(map(lambda (x, y): (y, x), enumerate(categories)))

        # 1. Create scatter-plots of the original data to overlay on the Augustus output
        self.scatterplots = []
        fillcolors = cassius.color.lightseries(len(categories))
        
        if clusteringModel:
            self.scatterplots.append(self.unitable.scatter("%s, %s" % (self.featureX, self.featureY),
                                                           (self.cuts if self.cuts is not None else ""),
                                                           markercolor="black",
                                                           markeroutline=None,
                                                           limit=self.limit,
                                                           xlabel=self.featureX,
                                                           ylabel=self.featureY))
                                                           
        else:
            for category, color in zip(categories, fillcolors):
                self.scatterplots.append(self.unitable.scatter("%s, %s" % (self.featureX, self.featureY),
                                                               "(%s) & (%s == '%s')" % ((self.cuts if self.cuts is not None else True), predictedField, category),
                                                               markercolor=cassius.color.darken(color),
                                                               markeroutline="black",
                                                               limit=self.limit,
                                                               xlabel=self.featureX,
                                                               ylabel=self.featureY,
                                                               ))

        fillcolors = map(cassius.color.lighten, fillcolors) # even lighter

        # 2. Make a configuration file for AugustusPMMLConsumer
        def addelement(base, childtag, **attrib):
            child = ElementTree.Element(childtag)
            for name, value in attrib.items():
                child.set(name, value)
            base.append(child)
            return child
        pmmlDeployment = ElementTree.Element("pmmlDeployment")
        logging = addelement(pmmlDeployment, "logging")
        addelement(logging, "toStandardOutput")
        inputModel = addelement(pmmlDeployment, "inputModel")
        addelement(inputModel, "fromFile", name=self.pmmlModel)
        inputData = addelement(pmmlDeployment, "inputData")
        addelement(inputData, "fromFile", name=self.planeFileName, type="UniTable")
        addelement(inputData, "readOnce")
        output = addelement(pmmlDeployment, "output")
        report = addelement(output, "report", name="Scores")
        addelement(report, "toFile", name=self.outputFileName)
        outputRow = addelement(report, "outputRow", name="Event")
        addelement(outputRow, "outputColumn", name="x", fieldName=self.featureX)
        addelement(outputRow, "outputColumn", name="y", fieldName=self.featureY)
        addelement(outputRow, "score", name="Score")
        ElementTree.ElementTree(pmmlDeployment).write(self.configFileName)

        # 3. Create a RegionMap object to represent the output
        if self.xmin is None or self.xmax is None or self.ymin is None or self.ymax is None:
            xmin, ymin, xmax, ymax = cassius.containers.Overlay(*self.scatterplots).ranges()
            if self.xmin is not None: xmin = self.xmin
            if self.xmax is not None: xmax = self.xmax
            if self.ymin is not None: ymin = self.ymin
            if self.ymax is not None: ymax = self.ymax
            width = xmax - xmin; height = ymax - ymin
            if self.xmin is None: xmin -= 0.2*width
            if self.xmax is None: xmax += 0.2*width
            if self.ymin is None: ymin -= 0.2*height
            if self.ymax is None: ymax += 0.4*height
        else:
            xmin, ymin, xmax, ymax = self.xmin, self.ymin, self.xmax, self.ymax
        self.regionplot = cassius.containers.RegionMap(self.numbins, xmin, xmax, self.numbins, ymin, ymax, categories, None, colors=fillcolors, bordercolor="black")

        # 4. Create a data file of points on the plane to score
        planeFile = file(self.planeFileName, "w")
        planeFile.write("%s,%s," % (self.featureX, self.featureY))
        planeFile.write(",".join(otherfields))
        if clusteringModel is not None:
            planeFile.write("\n")
        else:
            planeFile.write("," + predictedField + "\n")
        for i in xrange(self.regionplot.xbins):
            for j in xrange(self.regionplot.ybins):
                planeFile.write("%g,%g," % self.regionplot.center(i, j))
                planeFile.write(",".join(map(str, othervalues)))
                if clusteringModel is not None:
                    planeFile.write("\n")
                else:
                    planeFile.write(",dummy\n")
        del planeFile

        if not dryrun:
            # 5. Run AugustusPMMLConsumer
            try:
                os.remove(self.outputFileName)
            except OSError:
                pass
            AugustusPMMLConsumer = subprocess.Popen(["AugustusPMMLConsumer", "-c", self.configFileName], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            if AugustusPMMLConsumer.wait() != 0:
                raise RuntimeError, "AugustusPMMLConsumer failed: (stderr shown below)\n%s" % AugustusPMMLConsumer.stderr.read()
            self.stdout = AugustusPMMLConsumer.stdout.read()
            self.stderr = AugustusPMMLConsumer.stderr.read()

            # 6. Read the Augustus output
            self.scores = ElementTree.ElementTree(file=self.outputFileName)

            if clusteringModel is not None:
                categories = set()
                for score in self.scores.getroot().getchildren():
                    categories.add(score.find("Score").text)

                categories = list(categories)
                categories.sort()
                category_lookup = dict(map(lambda (x, y): (y, x), enumerate(categories)))

                self.regionplot.categories = categories

            scoreValues = numpy.empty((self.regionplot.xbins, self.regionplot.ybins), dtype=numpy.int)
            i = 0; j = 0
            for score in self.scores.getroot().getchildren():
                # x1, y1 = float(score.find("x").text), float(score.find("y").text)
                # x2, y2 = self.regionplot.center(i, j)
                # if abs(x1 - x2) > 1e-5 or abs(y1 - y2) > 1e-5:
                #     raise Exception, "Mismatch with input data: x = %g or %g, y = %g or %g" % (x1, x2, y1, y2)
                scoreValues[i,j] = category_lookup[score.find("Score").text]
                j += 1
                if j == self.regionplot.ybins:
                    j = 0
                    i += 1
            self.regionplot.categorizer = scoreValues

            # 7. Plot the results
            self.regionplot.xlabel = self.featureX
            self.regionplot.ylabel = self.featureY

            legend_data = []
            if clusteringModel is None:
                for i, category in enumerate(categories):
                    legend_data.append([category, cassius.containers.Style(marker="circle",
                                                                           markercolor=self.scatterplots[i].markercolor,
                                                                           markeroutline="black",
                                                                           fillcolor=fillcolors[i])])
            for field, value in zip(otherfields, othervalues):
                try:
                    legend_data.append([field, cassius.mathtools.str_sigfigs(value, 2)])
                except TypeError:
                    legend_data.append([field, value])

            if len(legend_data) > 0:
                self.legend = cassius.containers.Legend(legend_data, justify="lr", colwid=[0.7, 0.3])
                plots = [self.regionplot] + self.scatterplots + [self.legend]
            else:
                self.legend = None
                plots = [self.regionplot] + self.scatterplots
            
            self.plot = cassius.containers.Overlay(*plots, frame=0)
