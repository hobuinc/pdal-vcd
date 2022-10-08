
import pdal
import sys


import argparse
import sys
import numpy as np
import trimesh

import shapefile
from shapefile import TRIANGLE_STRIP, TRIANGLE_FAN, RING, OUTER_RING, FIRST_RING

# python vcd/extract-cluster.py clustered.laz --cluster_dimension=DBScan 2972

# https://pypi.org/project/alphashape/
# https://trimsh.org/examples.quick_start.html

def scale(a, bounds=200):
    return np.interp(a, (a.min(), a.max()), (-bounds, +bounds))


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

def extract_cluster(args):
    pipeline = pdal.Reader(filename = args.input)
    pipeline |= pdal.Filter.range(limits=f"{args.cluster_dimension}[{args.cluster_id}:{args.cluster_id}]")

    e = pipeline.execute()
    arr = pipeline.arrays[0]

    if len(arr) < 5:
        print (f"Not enough points to cluster {args.cluster_id}. We have {len(arr)} and need 5")
        sys.exit(1)

    x = arr['X']
    y = arr['Y']
    z = arr['Z']
    hag = arr['HeightAboveGround']


    points = np.vstack((x,y,z)).T
    wkt_esri = extract_crs(pipeline)

    print (f'computing Delaunay of {len(points)} points')

    pc = trimesh.points.PointCloud(points)

    filename = f"{args.cluster_dimension}-{args.cluster_id}"
    hull = pc.convex_hull

    shpfile = create_shapefile(filename, wkt_esri)

    add_polygon(shpfile, hull)
    shpfile.close()




if __name__ == '__main__':
    parser = argparse.ArgumentParser(description = 'Extract cluster with given ID from LAZ file')
    parser.add_argument('input', help='Input file to read')
    parser.add_argument('cluster_id', type=int, help='ID of the cluster to extract')
    parser.add_argument('--cluster_dimension', default="ClusterID", help='Dimension to use for selection')
    args = parser.parse_args()

    extract_cluster(args)


