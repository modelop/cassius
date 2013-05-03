cassius
=======

Cassius is a plotting toolset for the Augustus statistical modeling package.


The front-end (user) interface is designed to be intuitive: common tasks should be easy and all
tasks should be possible. It follows the brief syntactical style of Python and, unlike many plotting
toolkits, does not depend on a global state that would make copying script segments unreliable.

The back-end (graphical output) interface is designed to be flexible: the primary output format is
scalable SVG, which can be converted to a broad range of vector and raster formats, but other form


    from cassius import *

    # load the data
    dataset = inspect("wiki_Frontpage_dataset.csv")

    # take a quick look at it, to get familiar with the fields
    dataset.scan()

    # top_plot
    timeseriesX = dataset.timeseries("tx,x", linecolor="blue",
                                     informat="%m/%d/%Y-%H:%M:%S", outformat="%b %d")
    timeseriesX.xlabel = None
    timeseriesX.ylabel = "x or y"
    
    timeseriesY = dataset.timeseries("ty,y", ey="ey", limit=200, informat="%m/%d/%Y-%H:%M:%S")
    curveY = Curve("10*cos(x * 2*pi/(60*60*24*7)) + 30", linecolor="red")
    
    legend = Legend([["timeseriesX", timeseriesX],
                     ["timeseriesY", timeseriesY],
                     ["curveY", curveY]],
                    justify="cc", width=0.3, colwid=[0.7, 0.3], x=0., y=1., anchor="tl")
    
    top_plot = Overlay(timeseriesX, timeseriesY, curveY, legend, frame=0)
    
    # bottom_left_plot
    categoricalHist = dataset.histogram("category", fillcolor="yellow",
                                        leftmargin=0.23, bottommargin=0.17, xlabeloffset=0.17)
    
    bottom_left_plot = Overlay(Grid(horiz=regular(200.)), categoricalHist, frame=-1)
    
    # bottom_right_plot
    histX = dataset.histogram("x", numbins=100, lowhigh=(15, 45), fillcolor=RGB("blue", opacity=0.5),
                              ymax=600., rightmargin=0.1, bottommargin=0.17, xlabeloffset=0.17)
    histX.xlabel = "x or y"
    
    histY = dataset.histogram("y", numbins=100, lowhigh=(15, 45), fillcolor=lighten("red"))
    
    legend2 = Legend([[None, None, "mean"],
                      [histX, "histX", str_sigfigs(histX.mean(), 3)],
                      [histY, "histY", str_sigfigs(histY.mean(), 3)]],
                     justify="ccr", width=0.6, colwid=[0.3, 0.4, 0.3])
    
    bottom_right_plot = Overlay(histY, histX, legend2, frame=1)
    
    # combining everything into one image
    everything = Layout(2, 1, top_plot, Layout(1, 2, bottom_left_plot, bottom_right_plot))
    
    # view(everything)
    draw(everything, fileName="wiki_Frontpage_output.svg")
    
