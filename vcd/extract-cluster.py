
import pdal
import sys


import argparse

from scipy.spatial import Delaunay
import matplotlib.pyplot as plt
import numpy as np
from mayavi import mlab


def scale(a, bounds=200):
    return np.interp(a, (a.min(), a.max()), (-bounds, +bounds))


def extract_cluster(args):
    pipeline = pdal.Reader(filename = args.input)
    pipeline |= pdal.Filter.range(limits=f"{args.cluster_dimension}[{int(args.cluster_id)}:{int(args.cluster_id)}]")

    e = pipeline.execute()
    arr = pipeline.arrays[0]

    x = arr['X']
    y = arr['Y']
    z = arr['Z']
    hag = arr['HeightAboveGround']


    points = np.vstack((x,y,z)).T


    tri = Delaunay(points)

    # some how plot the thing
    fig = mlab.figure(1, bgcolor=(1, 0.7, 1), fgcolor=(0.5, 0.5, 0.5))

    # Generate triangular Mesh:
    tmesh = mlab.triangular_mesh(x, y, z, tri.vertices,
                                 scalars=y, colormap='jet')
    mlab.show()

    import pdb;pdb.set_trace()

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description = 'Extract cluster with given ID from LAZ file')
    parser.add_argument('input', help='Input file to read')
    parser.add_argument('cluster_id', help='ID of the cluster to extract')
    parser.add_argument('--cluster_dimension', default="ClusterID", help='Dimension to use for selection')
    args = parser.parse_args()

    extract_cluster(args)


