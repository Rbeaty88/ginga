#! /usr/bin/env python
#
from distutils.core import setup
from ginga.version import version
import os

srcdir = os.path.dirname(__file__)

try:  # Python 3.x
    from distutils.command.build_py import build_py_2to3 as build_py
except ImportError:  # Python 2.x
    from distutils.command.build_py import build_py

def read(fname):
    buf = open(os.path.join(srcdir, fname), 'r').read()
    return buf

# not yet working...
def get_docs():
    docdir = os.path.join(srcdir, 'doc')
    res = []
    # ['../../doc/Makefile', 'doc/conf.py', 'doc/*.rst',
    #                              'doc/manual/*.rst', 'doc/figures/*.png']    
    return res

setup(
    name = "ginga",
    version = version,
    author = "Eric Jeschke",
    author_email = "eric@naoj.org",
    description = ("An astronomical (FITS) image viewer and toolkit."),
    long_description = read('README.txt'),
    license = "BSD",
    keywords = "FITS image viewer astronomy",
    url = "http://ejeschke.github.com/ginga",
    packages = ['ginga',
                # Gtk version
                'ginga.cairow', 'ginga.gtkw', 'ginga.gtkw.plugins',
                'ginga.gtkw.tests',
                # Qt version
                'ginga.qtw', 'ginga.qtw.plugins', 'ginga.qtw.tests',
                # Tk version (widget only)
                'ginga.tkw', 'ginga.aggw',
                # Matplotlib version
                'ginga.mplw',
                # Common stuff
                'ginga.misc', 'ginga.misc.plugins',
                # Misc
                'ginga.util', 'ginga.icons', 'ginga.doc'
                ],
    package_data = { 'ginga.icons': ['*.ppm', '*.png'],
                     'ginga.gtkw': ['gtk_rc'],
                     #'ginga.doc': get_docs(),
                     'ginga.doc': ['manual/*.html'],
                     },
    scripts = ['scripts/ginga', 'scripts/grc'],
    classifiers = [
        "License :: OSI Approved :: BSD License",
        "Operating System :: MacOS :: MacOS X",
        "Operating System :: Microsoft :: Windows",
        "Operating System :: POSIX",
        "Topic :: Scientific/Engineering :: Astronomy",
    ],
    cmdclass={'build_py': build_py}
)

