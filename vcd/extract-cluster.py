
import pdal
import sys


import argparse
import sys
from scipy.spatial import Delaunay, ConvexHull
import numpy as np
import meshio

# python vcd/extract-cluster.py clustered.laz --cluster_dimension=DBScan 2972

def scale(a, bounds=200):
    return np.interp(a, (a.min(), a.max()), (-bounds, +bounds))

def extract_cluster(args):
    pipeline = pdal.Reader(filename = args.input)
    pipeline |= pdal.Filter.range(limits=f"{args.cluster_dimension}[{args.cluster_id}:{args.cluster_id}]")

    e = pipeline.execute()
    arr = pipeline.arrays[0]

    if not len(arr):
        print (f"Cluster {args.cluster_id} does not have any points")
        sys.exit(1)

    x = arr['X']
    y = arr['Y']
    z = arr['Z']
    hag = arr['HeightAboveGround']


    points = np.vstack((x,y,z)).T
    print (f'computing Delaunay of {len(points)} points')


    # https://stackoverflow.com/a/21343991/498396
    tri = Delaunay(points)

    # compute the convex hull of the points

    meshio.write(f"{args.cluster_dimension}-{args.cluster_id}.ply", mesh=meshio.Mesh(points=points, cells = [("quad", tri.simplices)]))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description = 'Extract cluster with given ID from LAZ file')
    parser.add_argument('input', help='Input file to read')
    parser.add_argument('cluster_id', type=int, help='ID of the cluster to extract')
    parser.add_argument('--cluster_dimension', default="ClusterID", help='Dimension to use for selection')
    args = parser.parse_args()

    extract_cluster(args)


