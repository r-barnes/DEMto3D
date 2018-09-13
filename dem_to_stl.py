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
parser.add_argument("-s", "--scale",   dest="scale", type=float, default=1, help="Scale vertical height by this value.")
parser.add_argument("--max",      type=float, default=np.inf,  help="Clip to this maximum value.")
parser.add_argument("--min",      type=float, default=-np.inf, help="Clip to this minimum value.")
parser.add_argument("--base",     type=float, default=0,       help="Add this value everywhere to make a thicker base.")
parser.add_argument("-p", "--parallel", action="store_true",   help="Run STL generation in parallel")
parser.add_argument("-c", "--combine", type=str, default="sep", help="Way to combine multiple files. Options are: sep, vstack")
parser.add_argument("--hscale", type=float, default=1.0, help="Scale horizontal axes by this value")
parser.add_argument("--cdist", type=int, default=0, help="Separation pixels between stacked DEMs")
parser.add_argument("destination", help="Save the resulting file as destination.tif", metavar="DESTINATION")
parser.add_argument("sourcefile", nargs='+', help="Read data from SOURCEFILE", metavar="SOURCEFILE")
args = parser.parse_args()

filetype = args.sourcefile[-3:]

files    = [gdal.Open(x) for x in args.sourcefile]
bands    = [x.GetRasterBand(1) for x in files]
no_datas = [x.GetNoDataValue() for x in bands]
srcdatas = [x.ReadAsArray() for x in bands]


#allowed_types = {gdal.GDT_Byte,gdal.GDT_Int16,gdal.GDT_Int32,gdal.GDT_UInt16,gdal.GDT_UInt32,gdal.GDT_Float32,gdal.GDT_Float64}
#if not srcband.DataType in allowed_types:
#  raise Exception("This datatype is not supported. Please file a bug report on RichDEM.")


if args.combine=='vstack':
  srcdatas_new     = None
  separation_array = np.zeros((args.cdist, srcdatas[0].shape[1]))
  for srcdata in srcdatas:
    if srcdatas_new is None:
      srcdatas_new = srcdata.copy()
    else:
      srcdatas_new = np.concatenate((srcdatas_new, separation_array, srcdata), axis=0)
  srcdatas = [srcdatas_new]
  args.destination = [args.destination]
elif args.combine=='sep':
  args.destination = [x+".stl" for x in args.sourcefile]
else:
  raise Exception("Unknown args.combine value")

for i,srcdata in enumerate(srcdatas):
  srcdata = np.clip(srcdata, args.min, args.max)

  sigma   = [1, 1]
  srcdata = sp.ndimage.filters.gaussian_filter(srcdata, sigma, mode='constant')

  srcdata = args.scale*srcdata
  srcdata = srcdata+args.base

  pad_array     = np.zeros((20, srcdatas[0].shape[1]))+(np.max(srcdata)-np.min(srcdata)) #Should be ~0.75 inches
  channel_array = np.zeros((10, srcdatas[0].shape[1])) #Should be 0.6 inches
  srcdata       = np.concatenate((pad_array, channel_array, srcdata, channel_array, pad_array), axis=0)

  stlgenerator.generate_from_heightmap_array(srcdata, args.destination[i], h_scale=args.hscale, multiprocessing=args.parallel)
