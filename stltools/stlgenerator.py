"""
A collection of functions to generate a 3D stl
model using various data sets.
"""

from struct import pack
from . import writefacets

def generate_from_heightmap_array(heightmap, destination):
    # Pad the heightmap so that it joins the polygons
    # at the sides of the base.
    for row in heightmap:
        row.append(1)
        row.insert(0,1)
    heightmap.insert(0, [1 for x in heightmap[0]])
    heightmap.append(heightmap[0][:])

    percentComplete = 0
    height = len(heightmap) - 1
    width  = len(heightmap[0]) - 1
    with open(destination, 'wb') as f:
        # Write the file header
        f.write(pack('80s', "Generic cube shape.".encode()))
        # Write the number of facets
        numTopBottomFacets  = width * height * 4
        numNorthSouthFacets = width * 4
        numEastWestFacets   = height * 4
        f.write(pack('i', numTopBottomFacets + numNorthSouthFacets + numEastWestFacets))

        # Generate the bottom plane.
        for y in range(height):
            if int(float(y) / height * 100) != percentComplete:
                percentComplete = int(float(y) / height * 100)
                print("Writing STL File... {0}% Complete".format(percentComplete))
            writefacets.writeEastFacet(f, 0, y, 0)
            writefacets.writeWestFacet(f, width, y, 0)
            for x in range(width):
                if y == 0:
                    writefacets.writeNorthFacet(f, x, y, 0)
                if y == height-1:
                    writefacets.writeSouthFacet(f, x, y+1, 0)
                writefacets.writeBottomFacet(f, x, y, 0)
                writefacets.writeTopFacet(f, x, y, heightmap)

        # Finished writing to file
        f.close()
        print("File saved as: " + destination)
