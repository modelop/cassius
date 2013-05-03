#!/usr/bin/env python

from distutils.core import setup, Extension
from distutils.command.build_ext import build_ext
import os

from cassius import __version__

class my_build_ext(build_ext):
    def build_extension(self, extension):
        try:
            build_ext.build_extension(self, extension)
        except:
            print "*******************************************************************************************"
            print
            print "  Could not build _svgview; the \"view(object)\" function will not work."
            print "  Use \"draw(object, fileName='...')\" instead, or get the dependencies:"
            print
            print "  sudo apt-get install python-dev libgtk2.0-dev libglib2.0-dev librsvg2-dev libcairo2-dev"
            print
            print "*******************************************************************************************"

def viewer_pkgconfig():
    def drop_whitespace(word): return word != "\n" and word != ""
    return filter(drop_whitespace, os.popen("pkg-config --cflags --libs gtk+-2.0 gthread-2.0 librsvg-2.0").read().split(" "))

viewer_extension = Extension(os.path.join("cassius", "_svgview"),
                             [os.path.join("cassius", "_svgview.c")], {},
                             libraries=["cairo", "rsvg-2"],
                             extra_compile_args=viewer_pkgconfig(),
                             extra_link_args=viewer_pkgconfig())

setup(name="cassius",
      version=__version__,
      description="Cassius the Plotter",
      author="Open Data Group",
      author_email="info@opendatagroup.com",
      url="none",
      packages=["cassius", "cassius.applications", "cassius.backends"],
      scripts=["applications/CassiusTreePlotter", "applications/CassiusScorePlane"],
      cmdclass={"build_ext": my_build_ext},
      ext_modules=[viewer_extension],
     )
