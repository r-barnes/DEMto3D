#!/usr/bin/env python3

"""
This program will generate a binary STL file with
a variable number of facets.
"""

import argparse
import numpy as np
from osgeo import gdal
from stltools import stlgenerator
import scipy as sp
import scipy.ndimage

gdal.UseExceptions()

# Command Line Options
parser = argparse.ArgumentParser(description="Generate an STL from a DEM file.")
parser.add_argument("-q", "--quality", dest="quality", default=2, help="The resolution of the resulting BMP. 1 will match the source resolution.")
parser.add_argument("--vsize",    type=float, default=1,          help="Height of DEM in the output in arbitrary units.")
parser.add_argument("--max",      type=float, default=np.inf,     help="Clip input data to this maximum value.")
parser.add_argument("--min",      type=float, default=-np.inf,    help="Clip input data to this minimum value.")
parser.add_argument("--base",     type=float, default=0,          help="Add this value in arbitrary units everywhere to make a thicker base.")
parser.add_argument("-p", "--parallel", action="store_true",      help="Run STL generation in parallel")
parser.add_argument("-c", "--combine", type=str, default="sep",   help="Way to combine multiple files. Options are: sep, vstack")
parser.add_argument("-r", "--rotate",  action="store_true",       help="Transpose the input data")
parser.add_argument("--hsize", type=float, default=1.0,           help="Width of the narrowest axis of the piece in arbitrary units")
parser.add_argument("--cdist", type=int, default=0, help="Separation pixels between stacked DEMs")
parser.add_argument("destination", help="Save the resulting file as destination.tif", metavar="DESTINATION")
parser.add_argument("sourcefile", nargs='+', help="Read data from SOURCEFILE", metavar="SOURCEFILE")
args = parser.parse_args()

filetype = args.sourcefile[-3:]

allowed_types = {gdal.GDT_Byte,gdal.GDT_Int16,gdal.GDT_Int32,gdal.GDT_UInt16,gdal.GDT_UInt32,gdal.GDT_Float32,gdal.GDT_Float64}

files    = [gdal.Open(x) for x in args.sourcefile]
bands    = [x.GetRasterBand(1) for x in files]
no_datas = [x.GetNoDataValue() for x in bands]
srcdata  = [x.ReadAsArray() for x in bands]
dtypes   = [x.DataType in allowed_types for x in bands]

if not all(dtypes):
  raise Exception("One of the inputs had an unsupported datatype!")

for i in range(len(srcdata)):
  srcdata[i] = np.clip(srcdata[i], args.min, args.max)
  sigma      = [1, 1]
  srcdata[i] = sp.ndimage.filters.gaussian_filter(srcdata[i], sigma, mode='constant')





if args.combine=='vstack':
  stlgenerator.generate_from_heightmap_array(srcdata, args.destination+".stl", hsize=args.hsize, vsize=args.vsize, base=args.base, multiprocessing=args.parallel)
elif args.combine=='sep':
  args.destination = [x+".stl" for x in args.sourcefile]
  for i in range(len(srcdata)):
    stlgenerator.generate_from_heightmap_array(srcdata[i], args.destination[i], hsize=args.hsize, vsize=args.vsize, base=args.base, multiprocessing=args.parallel)
else:
  raise Exception("Unknown args.combine value")
