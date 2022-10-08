
import pdal
import sys


import argparse
import sys
import numpy as np
import trimesh

import shapefile
from shapefile import TRIANGLE_STRIP, TRIANGLE_FAN, RING, OUTER_RING, FIRST_RING

# python vcd/extract-cluster.py clustered.laz --cluster_dimension=DBScan

# https://pypi.org/project/alphashape/
# https://trimsh.org/examples.quick_start.html


def add_polygon(shpfile, mesh):
    shpfile.multipatch(mesh.triangles, partTypes=[RING]* len(mesh.triangles)) # one type for each part
    shpfile.record(mesh.volume, mesh.area)

def create_shapefile(filename, crs):
    w = shapefile.Writer(filename)
    w.field('volume', 'N', decimal=2)
    w.field('area', 'N', decimal=2)

    # Save CRS WKT
    with open(filename+'.prj', 'w') as f:
        f.write(crs)


    # Save CRS WKT
    with open(filename+'.prj', 'w') as f:
        f.write(crs)

    return w


def extract_crs(pipeline):
    """Extract CRS from a PDAL pipeline for readers.las output as ESRI WKT1 for shapefile output"""

    from pyproj import CRS
    from pyproj.enums import WktVersion

    metadata = pipeline.metadata['metadata']

    if 'readers.las' in metadata:
        wkt = metadata['readers.las']['comp_spatialreference']
    elif 'readers.bpf' in metadata:
        raise NotImplementedError
    else:
        wkt = ''

    crs = CRS(wkt)
    output = crs.to_wkt(WktVersion.WKT1_ESRI)
    return output

def extract_clusters(args):
    pipeline = pdal.Reader(filename = args.input)
    pipeline |= pdal.Filter.groupby(dimension = args.cluster_dimension)

    e = pipeline.execute()
    print (f'Extracted {len(pipeline.arrays)} clusters')

    filename = f"{args.cluster_dimension}"
    wkt_esri = extract_crs(pipeline)
    shpfile = create_shapefile(filename, wkt_esri)

    for array in pipeline.arrays:
        add_cluster(shpfile, array, args)

    shpfile.close()


def add_cluster(shpfile, arr, args):

    if len(arr) < 5:
        cluster_id = arr[0][args.cluster_dimension]
        print (f"Not enough points to cluster {cluster_id}. We have {len(arr)} and need 5")
        sys.exit(1)

    x = arr['X']
    y = arr['Y']
    z = arr['Z']
    hag = arr['HeightAboveGround']


    points = np.vstack((x,y,z)).T

    print (f'computing Delaunay of {len(points)} points')

    pc = trimesh.points.PointCloud(points)

    hull = pc.convex_hull

    add_polygon(shpfile, hull)




if __name__ == '__main__':
    parser = argparse.ArgumentParser(description = 'Extract cluster with given ID from LAZ file')
    parser.add_argument('input', help='Input file to read')
    parser.add_argument('--cluster_dimension', default="ClusterID", help='Dimension to use for selection')
    args = parser.parse_args()

    extract_clusters(args)


