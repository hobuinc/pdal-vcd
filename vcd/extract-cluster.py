
import pdal
import sys


import argparse
import sys
import numpy as np
import trimesh

# https://github.com/GeospatialPython/pyshp
import shapefile
from shapefile import TRIANGLE_STRIP, TRIANGLE_FAN, RING, OUTER_RING, FIRST_RING

# python vcd/extract-cluster.py clustered.laz --cluster_dimension=DBScan

# http://downloads.esri.com/support/whitepapers/ao_/J9749_MultiPatch_Geometry_Type.pdf
# https://github.com/mikedh/trimesh
# https://trimsh.org/examples.quick_start.html


def add_polygon(shpfile, mesh, cluster_id):
    shpfile.multipatch(mesh.triangles, partTypes=[TRIANGLE_STRIP]* len(mesh.triangles)) # one type for each part
    shpfile.record(mesh.volume, mesh.area, cluster_id)

def create_shapefile(filename, crs):
    w = shapefile.Writer(filename)
    w.field('volume', 'N', decimal=2)
    w.field('area', 'N', decimal=2)
    w.field('clusterid', 'N')

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
        if (len(arr)):
            cluster_id = arr[0][args.cluster_dimension]
            print (f"Not enough points to cluster {cluster_id}. We have {len(arr)} and need 5")
        else:
            print (f"Cluster has no points!")

        sys.exit(1)

    x = arr['X']
    y = arr['Y']
    z = arr['Z']
    hag = arr['HeightAboveGround']
    cluster_id = arr[0][args.cluster_dimension]

    points = np.vstack((x,y,z)).T

    print (f'computing Delaunay of {len(points)} points')

    pc = trimesh.points.PointCloud(points)

    hull = pc.convex_hull

    # cull out some specific cluster IDs
    culls = [-1,0,1]

    if cluster_id not in culls:
        add_polygon(shpfile, hull, cluster_id)




if __name__ == '__main__':
    parser = argparse.ArgumentParser(description = 'Extract cluster with given ID from LAZ file')
    parser.add_argument('input', help='Input file to read')
    parser.add_argument('--cluster_dimension', default="ClusterID", help='Dimension to use for selection')
    args = parser.parse_args()

    extract_clusters(args)


