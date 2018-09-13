"""
A collection of functions to generate a 3D stl
model using various data sets.
"""

import functools
import numpy as np
from struct import pack
from . import writefacets
from multiprocessing import Pool

def CalculateRow(heightmap, y, h_scale):
    facets = bytearray()
    height = heightmap.shape[0] - 1
    width  = heightmap.shape[1] - 1
    facets += writefacets.writeEastFacet(0, y, 0, h_scale)
    facets += writefacets.writeWestFacet(width, y, 0, h_scale)
    for x in range(width):
        if y == 0:
            facets += writefacets.writeNorthFacet(x, y, 0, h_scale)
        if y == height-1:
            facets += writefacets.writeSouthFacet(x, y+1, 0, h_scale)
        facets += writefacets.writeBottomFacet(x, y, 0, h_scale)
        facets += writefacets.writeTopFacet(x, y, h_scale, heightmap)
    return facets

def generate_from_heightmap_array(heightmap, destination, h_scale=1, objectname="DEM 3D Model", multiprocessing=True):
    #A binary STL file has an 80-character header (which is generally ignored,
    #but should never begin with "solid" because that may lead some software to
    #assume that this is an ASCII STL file). 
    if len(objectname)>80:
        raise Exception("STL object name must be 80 characters or less!")

    #Pad the heightmap so that it joins the polygons at the sides of the base.
    heightmap = np.pad(heightmap, ((1,1),(1,1)), mode='constant', constant_values=0)

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
