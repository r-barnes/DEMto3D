"""
A collection of functions to generate a 3D stl
model using various data sets.
"""

import functools
import math
import numpy as np
from struct import pack
from . import writefacets
from multiprocessing import Pool

def CalculateRow(heightmap, y, h_scale):
    facets = bytearray()
    height = heightmap.shape[0] - 1
    width  = heightmap.shape[1] - 1
    facets += writefacets.writeEastFacet(x=0,     y=y, heightmap=heightmap, hs=h_scale)
    facets += writefacets.writeWestFacet(x=width, y=y, heightmap=heightmap, hs=h_scale)
    for x in range(width):
        if y == 0:
            facets += writefacets.writeNorthFacet(x=x, y=y,   heightmap=heightmap, hs=h_scale)
        elif y == height-1:
            facets += writefacets.writeSouthFacet(x=x, y=y+1, heightmap=heightmap, hs=h_scale)
        facets += writefacets.writeBottomFacet(x=x, y=y, z=0, hs=h_scale)
        facets += writefacets.writeTopFacet   (x=x, y=y, hs=h_scale, heightmap=heightmap)
    return facets

def generate_from_heightmap_array(heightmap, destination, hsize=1, vsize=1, base=0, hsep=0.6, padsize=0.75, objectname="DEM 3D Model", multiprocessing=True):
    #A binary STL file has an 80-character header (which is generally ignored,
    #but should never begin with "solid" because that may lead some software to
    #assume that this is an ASCII STL file). 
    if len(objectname)>80:
        raise Exception("STL object name must be 80 characters or less!")


    if isinstance(heightmap,list):
        h_scale          = hsize/heightmap[0].shape[1]
        separation_array = np.zeros((math.ceil(hsep/h_scale), heightmap[0].shape[1]))
        heightmap_new    = [heightmap[0]]
        for hm in heightmap[1:]:
            heightmap_new += [separation_array, hm]
        heightmap = np.concatenate(heightmap_new, axis=0)
    else:
        h_scale = hsize/heightmap.shape[1]
        separation_array = np.zeros((math.ceil(hsep/h_scale), heightmap[0].shape[1]))

    heightmap -= heightmap.min()       #Set base elevation to 0
    heightmap *= vsize/heightmap.max() #Scale heightmap to fit in vsize arbitrary units
    heightmap += base                  #Add the indicated amount of base (in arbitrary units)

    pad_array = np.zeros((math.ceil(padsize/h_scale), heightmap.shape[1]))+heightmap.max()  #Should be ~0.75 inches
    heightmap = np.concatenate((pad_array, separation_array+base, heightmap, separation_array+base, pad_array), axis=0)

    #Pad the heightmap so that it joins the polygons at the sides of the base.
    # heightmap = np.pad(heightmap, ((1,1),(1,1)), mode='constant', constant_values=0)

    percentComplete = 0
    height = heightmap.shape[0] - 1
    width  = heightmap.shape[1] - 1
    with open(destination, 'wb') as f:
        # Write the number of facets
        numTopBottomFacets  = 4 * width * height
        numNorthSouthFacets = 4 * width 
        numEastWestFacets   = 4 * height 

        if multiprocessing:
            pool   = Pool()
            facets = pool.starmap(CalculateRow, [(heightmap,y,h_scale) for y in range(height)])
            facets = b''.join(facets)
        else:
            facets = bytearray()
            # Generate the bottom plane.
            for y in range(height):
                if int(float(y) / height * 100) != percentComplete:
                    percentComplete = int(float(y) / height * 100)
                    print("Writing STL File... {0}% Complete".format(percentComplete))
                facets += CalculateRow(heightmap, y, h_scale)

        # Write the file header
        f.write(pack('80s', objectname.encode()))
        #Following the header is a 4-byte little-endian unsigned integer
        #indicating the number of triangular facets in the file. Following that
        #is data describing each triangle in turn. The file simply ends after
        #the last triangle.
        f.write(pack('<i', numTopBottomFacets + numNorthSouthFacets + numEastWestFacets))

        f.write(facets)

    # Finished writing to file
    print("File saved as: " + destination)
