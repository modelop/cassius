.. automodule:: cassius.applications.ScorePlane

ScorePlane: plot AugustusPMMLConsumer output
--------------------------------------------

Tutorial: developing a consumer workflow
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

The easiest way to develop a workflow is to work on a small part of it
interactively and gradually add features.  Feedback from the data and
partial calculations allow the user to catch misconceptions and
correct them early, avoiding a lot of wasted development.  Part of
this process is becoming familiar with the data and what various
optimization engines can say about it.  The `ScorePlane` application
overlays data on scored Augustus output, to show how a given PMML
model relates to the data (usually training data).

This tutorial shows how to explore the `Iris.csv` dataset scored by a
binary decision tree.  The tools are not specific to decision trees:
we could use any model that Augustus can consume.

The first step should usually be to look at the data themselves, to
get an intuitive sense of how the entries are distributed.  In the
example below, we load the data into an `InspectTable` (subclass of
`UniTable`) and plot it in various ways:
   * `tmp1` (top-left): just a scatter-plot of `PETAL_LENGTH`
     vs. `PETAL_WIDTH`, later fitted to `a + x*b`
   * `tmp2` (top-right): the same scatter-plot with a cut selecting
     each category and labeled with different colors
   * `tmp3` (bottom-left): a stacked histogram of `PETAL_LENGTH` for
     each category
   * `tmp4` (bottom-right): a stacked histogram of `PETAL_LENGTH +
     (PETAL_WIDTH - -0.366514)/(0.416419)`, where the parameters were
     determined from the quick fit.

The interface of an `InspectTable` is `table.plottype(expression,
cuts)` for all plot types.

.. container::

   ::
 
      >>> from cassius import *

      >>> unitable = inspect("Iris.csv")

      >>> tmp1 = unitable.scatter("PETAL_LENGTH, PETAL_WIDTH")
      >>> view(tmp1)

      >>> tmp2 = Overlay(unitable.scatter("PETAL_LENGTH, PETAL_WIDTH", "CATEGORY == 'Iris-setosa'", markercolor="red"),
      >>>                unitable.scatter("PETAL_LENGTH, PETAL_WIDTH", "CATEGORY == 'Iris-versicolor'", markercolor="blue"),
      >>>                unitable.scatter("PETAL_LENGTH, PETAL_WIDTH", "CATEGORY == 'Iris-virginica'", markercolor="green"))
      >>> view(tmp2)

      >>> tmp3 = Stack(unitable.histogram("PETAL_LENGTH", "CATEGORY == 'Iris-setosa'", numbins=20, lowhigh=(0., 8.), fillcolor=lighten("red")),
      >>>              unitable.histogram("PETAL_LENGTH", "CATEGORY == 'Iris-versicolor'", numbins=20, lowhigh=(0., 8.), fillcolor=lighten("blue")),
      >>>              unitable.histogram("PETAL_LENGTH", "CATEGORY == 'Iris-virginica'", numbins=20, lowhigh=(0., 8.), fillcolor=lighten("green")))
      >>> view(tmp3)

      >>> line = Curve("a + x*b", parameters={"a": 0., "b": 0.})
      >>> line.fit(tmp1)

      >>> better_discriminator = "PETAL_LENGTH + (PETAL_WIDTH - %(a)g)/(%(b)g)" % line.parameters
      >>> print better_discriminator
      PETAL_LENGTH + (PETAL_WIDTH - -0.366514)/(0.416419)

      >>> tmp4 = Stack(unitable.histogram(better_discriminator, "CATEGORY == 'Iris-setosa'", numbins=20, lowhigh=(0., 16.), fillcolor=lighten("red")),
      >>>              unitable.histogram(better_discriminator, "CATEGORY == 'Iris-versicolor'", numbins=20, lowhigh=(0., 16.), fillcolor=lighten("blue")),
      >>>              unitable.histogram(better_discriminator, "CATEGORY == 'Iris-virginica'", numbins=20, lowhigh=(0., 16.), fillcolor=lighten("green")))
      >>> view(tmp4)

      >>> view(Layout(2, 2, Overlay(tmp1, line), tmp2, tmp3, tmp4))

   .. image:: PLOTS/ScorePlane_inspect1.png

.. note::
   The above example uses `Curve.fit` (non-linear function fitting)
   which has been turned off until we port non-linear optimization
   from Minuit/PyMinuit to SciPy.  That part of the example won't
   work.

These are not professional plots: the axes are not labeled and there
is no legend to identify which color corresponds to which category,
but they are not intended for presentation, just exploration.

Next, we study the binary decision tree that is supposed to model the
data.  The model was produced using AugustusTreeProducer with all four
features active (`PETAL_LENGTH`, `PETAL_WIDTH`, `SEPAL_LENGTH`,
`SEPAL_WIDTH`), with a maximum tree depth of four.  No preprocessing
was performed: in particular, the linear transformation derived in the
example above would likly improve the trees, if it had been used.

The `ScorePlane` object calls AugustusPMMLConsumer on all points in a
two-dimensional slice of the feature space and presents the output by
coloring the plane, with the dataset overlaid in the same color
scheme.  It is located in the `cassius.applications` subpackage.

.. container::

   ::

      >>> from cassius.applications.ScorePlane import ScorePlane

      >>> augustus = ScorePlane("iris_binarytree_15.pmml", unitable,
                                featureX="PETAL_LENGTH", featureY="PETAL_WIDTH")
      >>> augustus.score()
      >>> view(augustus.plot)

   .. image:: PLOTS/ScorePlane_output1.png

At a glance, we can already see that the decision tree has been
overtrained to the dataset: the green and blue slivers at `PETAL_WIDTH
= 1.6` exist only to reach a few data points.  The `SEPAL_LENGTH 5.8`
AND `SEPAL_WIDTH 3.1` in the legend indicate that we are looking at
the slice that has these two sepal parameters (the mean of the data
points in these two projections).

We can look at the feature space at a different angle by plotting
`PETAL_WIDTH` vs. `SEPAL_LENGTH`.

.. container::

   ::

      >>> augustus = ScorePlane("iris_binarytree_15.pmml", unitable,
                                featureX="SEPAL_LENGTH", featureY="PETAL_WIDTH")
      >>> augustus.score()
      >>> view(augustus.plot)

   .. image:: PLOTS/ScorePlane_output2.png

The same outlying Iris-virginica data point that created a finger-like
extension in `PETAL_LENGTH` has also created such a region in
`SEPAL_LENGTH`.  If this were a real analysis session, the next step
would be to try to minimize this effect.

In addition to rotating our view 90 degrees (above), we can also shift
our view: the plot below shows the same axes, but for `PETAL_LENGTH =
1.5` instead of `3.8`.

.. container::

   ::

      >>> augustus = ScorePlane("iris_binarytree_15.pmml", unitable,
                                featureX="SEPAL_LENGTH",
                                featureY="PETAL_WIDTH",
                                othervalue={"PETAL_LENGTH": 1.5})
      >>> augustus.score()
      >>> view(augustus.plot)

   .. image:: PLOTS/ScorePlane_output3.png

The plot above gives the misleading impression that all of the data
were scored as Iris-setosa.  This is why the default values of
features not plotted are set to the mean of the datasets.  Instead of
setting the `PETAL_LENGTH` explicitly, we could select our data with
`cuts = "PETAL_LENGTH < 4"`.  With this cut, the mean `PETAL_LENGTH`
is `1.8`, and it is clear why the model claims this region for
Iris-setosa.  (Refer to the plots of `PETAL_LENGTH` vs. `PETAL_WIDTH`
above.)

.. container::

   ::

      >>> augustus = ScorePlane("iris_binarytree_15.pmml", unitable,
                                featureX="SEPAL_LENGTH", xmin=3.8,
                                featureY="PETAL_WIDTH",
                                cuts="PETAL_LENGTH < 4.")
      >>> augustus.score()
      >>> view(augustus.plot)

   .. image:: PLOTS/ScorePlane_output4.png

.. todo::

   Perhaps this should access Augustus through Python calls, rather
   than calling it as a subprocess.  It's slower than I would have
   expected, part of the issue is writing the temporary CSV-based
   `planeFile`, but a much larger part is in executing
   AugustusPMMLConsumer itself (possibly due to reading the CSV?).

   If a "back-door" to Augustus is ever made, this script should
   retain the ability to generate configuration files as an
   introductory template for more involved work.

Python interface
^^^^^^^^^^^^^^^^

The Python interface (used in the tutorial above) is intended for interactive
use or embedding in other Python scripts.  See below for a
command-line interface.

.. autoclass:: ScorePlane
   :members: score

Command-line interface
^^^^^^^^^^^^^^^^^^^^^^

The command-line interface is for embedding in shell scripts.  It is a
thin wrapper of the Python interface.

::

usage: CassiusScorePlane [-h] [--xmin XMIN] [--xmax XMAX] [--ymin YMIN]
                         [--ymax YMAX] [--at [AT [AT ...]]]
                         [--configFileName CONFIGFILENAME]
                         [--planeFileName PLANEFILENAME]
                         [--outputFileName OUTPUTFILENAME]
                         csv pmml svg featureX featureY

Plots AugustusPMMLConsumer output overlaid by data for two features.
AugustusPMMLConsumer must be on the PATH.

positional arguments:
  csv                   data points to plot as a CSV file
  pmml                  scored regions to plot as a PMML file
  svg                   fileName for SVG plot to create/overwrite
  featureX              feature to plot on the horizontal (X) axis
  featureY              feature to plot on the vertical (Y) axis

optional arguments:
  -h, --help            show this help message and exit
  --xmin XMIN           minimum X value to score/plot
  --xmax XMAX           maximum X value to score/plot
  --ymin YMIN           minimum Y value to score/plot
  --ymax YMAX           maximum Y value to score/plot
  --at [AT [AT ...]]    values for the features that are not drawn as a space-
                        delimited list: feature1 value1 feature2 value2...
  --configFileName CONFIGFILENAME
                        configuration file name for AugustusPMMLConsumer job
  --planeFileName PLANEFILENAME
                        points on the plane to score
  --outputFileName OUTPUTFILENAME
                        file name for AugustusPMMLConsumer output
