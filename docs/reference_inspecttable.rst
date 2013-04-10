.. automodule:: cassius.containers

Interactive data exploration
----------------------------

.. note::

   Examples on this page use a data file from `Augustus 0.4.3.1.tar.gz
   <http://code.google.com/p/augustus/downloads/detail?name=Augustus-0.4.3.1.tar.gz>`_.
   To reproduce the examples, download Augustus and unpack it with

   ::

      linux> tar -xzvf Augustus-0.4.3.1.tar.gz

   if you have not done so already.

The UniTable module of Augustus provides a uniform interface to a
variety of data formats.  The `InspectTable` class in Cassius is
a subclass of `UniTable` with functions for making plots quickly and
interactively.

.. container::

   Let's take a first look at the highway data.

   ::

      >>> from cassius import *
      >>> highway = inspect("Augustus-0.4.3.1/examples/highway/real/data/scoring.csv")

      >>> # names of the columns in the dataset
      >>> highway.keys()
      ['fielddeviceid', 'locationtimestamp', 'devicestatus', 'datastatus', 'locstatus', 'lastupdatetime', 'volume', 'speed', 'occupancy']

      >>> # number of rows in the dataset
      >>> len(highway)
      188529

      >>> # scan is similar to running the CSV file through the unix command `head`
      >>> # but it is more flexible (see below)
      >>> highway.scan()
      fielddevicei locationtime devicestatus   datastatus    locstatus lastupdateti       volume        speed    occupancy
      ====================================================================================================================
      'IL-TESTTSC-   1174330073 'NON_OPERATI 'FIELD_DATA_ 'LOCATION_RE 1175058600000            0            0            0
      'IL-TESTTSC-   1174330073 'NON_OPERATI 'FIELD_DATA_ 'LOCATION_RE 1175058600000            0            0            0
      'IL-TESTTSC-   1174330073 'NON_OPERATI 'FIELD_DATA_ 'LOCATION_RE 1175058600000            0            0            0
      'IL-TESTTSC-   1174330073 'NON_OPERATI 'FIELD_DATA_ 'LOCATION_RE 1175058600000            0            0            0
      'IL-TESTTSC-   1174330073 'NON_OPERATI 'FIELD_DATA_ 'LOCATION_RE 1175058600000            0            0            0
      'IL-TESTTSC-   1174330073 'OPERATIONAL 'FIELD_DATA_ 'LOCATION_RE 1175058600000           78      22.2683      2.75029
      'IL-TESTTSC-   1174330073 'OPERATIONAL 'FIELD_DATA_ 'LOCATION_RE 1175058600000          219       24.431      7.25412
      'IL-TESTTSC-   1174330073 'OPERATIONAL 'FIELD_DATA_ 'LOCATION_RE 1175058600000           87      17.0116       3.7582
      'IL-TESTTSC-   1174330073 'OPERATIONAL 'FIELD_DATA_ 'LOCATION_RE 1175058600000           61      18.4633      2.71703
      'IL-TESTTSC-   1174330073 'OPERATIONAL 'FIELD_DATA_ 'LOCATION_RE 1175058600000           99      16.9542      4.30594

      >>> # fielddeviceid, devicestatus, and locstatus are categorical variables, denoted by strings
      >>> # find out how many unique values they have and print them, if there aren't too many
      >>> len(highway.unique("fielddeviceid"))
      807
      >>> highway.unique("devicestatus")
      set(['OPERATIONAL', 'NON_OPERATIONAL'])
      >>> highway.unique("locstatus")
      set(['LOCATION_RESOLVED_AUTO', 'LOCATION_NOT_VALIDATED'])

      >>> # print out volume, speed, and occupancy for operational devices only
      >>> highway.scan("volume,speed,occupancy", "devicestatus == 'OPERATIONAL'", subset=slice(0,30))
            volume        speed    occupancy
      ======================================
                78      22.2683      2.75029
               219       24.431      7.25412
                87      17.0116       3.7582
                61      18.4633      2.71703
                99      16.9542      4.30594
               120      17.2242      5.35947
               120      17.5372      5.34889
               141      23.9993      4.45129
               126      38.2997      4.53586
               108       23.074      4.08331
                79       23.983      2.85801
               123      32.2037      2.64779
               114      23.0159      4.44238
               147      24.4657      5.23031
                87      22.6874      3.09446
               105      17.0226       4.9266
                76      23.1242      2.87617
                57      18.5211      3.77619
                56      20.5718      3.63001
                50       20.468      2.97221
               180      18.1613      7.54412
               135      21.0205      4.67562
                99       23.998      4.23589
                85      25.8025      3.55291
                79           26      3.27255
               144      30.4688      3.19768
               123      25.7166        3.446
               162      25.0943      4.52048
               162      26.0056      4.41675
               168      24.2139         5.05

      >>> # make a histogram of speeds for operational devices (with speed != NaN)
      >>> view(highway.histogram("speed",
      ...                        "(devicestatus == 'OPERATIONAL')  &  (speed > 0.)",
      ...                        lowhigh=(0., 100.)))

   .. image::
      PLOTS/Inspect_example1.png

   That's interesting: there's a little peak at 60 MPH, while most
   measurements are around 30 MPH.  Could it be a confederacy of
   speeders or just a special road with a higher speed limit?

   There are 807 field devices.  We can plot them as a categorical
   histogram, but then we can't read the horizontal axis because their
   titles overlap.  When we ask for speeds greater than 55 MPH, we do
   see one fielddeviceid tower above the rest.

   ::

      >>> view(highway.histogram("fielddeviceid", "speed > 55."),
      ...      height=500, bottommargin=0.15, xlabeloffset=0.15)

   .. image::
      PLOTS/Inspect_example2_1.png

   To get a better view, we can use `HistogramCategorical.top` to
   combine all but the largest bin into one bin called "other".  Now
   we can read the fielddeviceid: it's the Edens (a highway running
   through Chicago, along Lake Michigan).

   ::

      >>> view(highway.histogram("fielddeviceid", "speed > 55.").top(1),
      ...      height=500, bottommargin=0.15, xlabeloffset=0.15)

   .. image::
      PLOTS/Inspect_example2.png

   The speed distribution for cars on the Edens is well-defined.  By
   inverting the requirement, you can see that it is completely
   responsible for the peak at 60 MPH.

   ::

      >>> view(highway.histogram("speed",
      ...                        "(devicestatus == 'OPERATIONAL')  &  (speed > 0.)  & (fielddeviceid == 'IL-TESTTSC-EDENS-S-1037')",
      ...                        lowhigh=(0., 100.)))

   .. image::
      PLOTS/Inspect_example3.png

.. autofunction:: inspect

.. autoclass:: InspectTable
   :members: __call__, scan, unique, histogram, timehist, scatter, timeseries

.. container::

   An example with a `TimeSeries`::

      >>> from cassius import *
      >>> highway = inspect("Augustus-0.4.3.1/examples/highway/real/data/scoring.csv")

      >>> # a plot with all of the fielddeviceids
      >>> all = highway.timeseries("lastupdatetime, volume",
      ...                          "(volume > 0)  &  (devicestatus == 'OPERATIONAL')",
      ...                          outformat="%b %y")
      ...

      >>> # a plot with only one fielddeviceid
      >>> one = highway.timeseries("lastupdatetime, volume",
      ...                          "(volume > 0)  &  (devicestatus == 'OPERATIONAL')  &  (fielddeviceid == 'IL-TESTTSC-EDENS-S-1037')",
      ...                          outformat="%b %y")

      >>> view(Layout(2, 1, all, one), ymin=0, ymax=1000, bottommargin=0.2, xlabeloffset=0.2)
      
   .. image::
      PLOTS/Inspect_example4.png

   The volume increased, but not just because they added field
   devices.  Looking at only one field device, we see the same trend.
