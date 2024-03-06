import matplotlib.pyplot as plt
import numpy as np
# import csv
import pandas as pd
import cartopy.crs as ccrs
import cartopy.feature as cfeature
from sklearn.cluster import DBSCAN
import geopandas as gpd
from shapely.geometry import Polygon
from scipy.interpolate import splev, splprep
from shapely.geometry.polygon import Polygon
from shapely.geometry import mapping
from scipy.spatial import ConvexHull
import alphashape
from shapely.ops import cascaded_union, polygonize
import shapely.geometry as geometry
from scipy.spatial import Delaunay
import json






class PlottingService:
    def __init__(self):

        pass

    def plot_data(self, plot_points, data_fp, ax=None):

        with open(data_fp, 'r') as file:
            data = json.load(file)
        points = self.get_points(data)


        if not ax:  # In case ax is None or not passed
            fig, ax = plt.subplots(figsize=(15, 15), dpi =500, subplot_kw={'projection': ccrs.PlateCarree()})
        else:
            # Use the existing ax to clear and plot, no need to create a new fig, ax
            ax.clear()

        # fig, ax = plt.subplots(figsize=(10, 10), subplot_kw={'projection': ccrs.PlateCarree()})
        ax.add_feature(cfeature.COASTLINE, linewidth=0.25)
        ax.add_feature(cfeature.BORDERS, linewidth=0.25)
        ax.add_feature(cfeature.STATES, edgecolor = 'gray', linewidth=0.125)
        ax.add_feature(cfeature.LAKES, edgecolor='black',linewidth=0.25, zorder =100)
        ax.add_feature(cfeature.OCEAN, edgecolor='black',linewidth=0.25, zorder = 100)


        # TODO: Add this stuff to GUI
        if plot_points:
            # Extract longitudes and latitudes for plotting
            longitudes, latitudes = zip(*points)
            ax.scatter(longitudes, latitudes, transform=ccrs.Geodetic(), s=2, color='red', marker='o', edgecolor='none')


    def get_points(self, data):
        points = []
        for record in data:  # Directly iterate over the list of records
            if 'decimalLongitude' in record and 'decimalLatitude' in record:
                lon = record['decimalLongitude']
                lat = record['decimalLatitude']
                points.append((lon, lat))  # Collecting points as (longitude, latitude) tuples
        return points

        

    def get_clusters(self):
        pass


    def alpha_shape(points, alpha):
        """
        Compute the alpha shape (concave hull) of a set of points.
        @param points: Iterable container of points.
        @param alpha: alpha value to influence the gooeyness of the border. Smaller numbers
                    don't fall inward as much as larger numbers. Too large, and you lose detail.
        @return: Polygon.
        """
        if len(points) < 4:
            # A hull cannot be calculated with less than 4 points
            return geometry.MultiPoint(list(points)).convex_hull
        
        def add_edge(edges, edge_points, coords, i, j):
            """
            Add a line between the i-th and j-th points,
            if not in the list already
            """
            if (i, j) in edges or (j, i) in edges:
                return
            edges.add((i, j))
            edge_points.append(coords[[i, j]])
        
        coords = np.array([point for point in points])
        tri = Delaunay(coords)
        edges = set()
        edge_points = []
        # loop over triangles:
        # ia, ib, ic = indices of corner points of the triangle
        for ia, ib, ic in tri.simplices:
            pa = coords[ia]
            pb = coords[ib]
            pc = coords[ic]
            # Lengths of sides of triangle
            a = np.sqrt((pa[0]-pb[0])**2 + (pa[1]-pb[1])**2)
            b = np.sqrt((pb[0]-pc[0])**2 + (pb[1]-pc[1])**2)
            c = np.sqrt((pc[0]-pa[0])**2 + (pc[1]-pa[1])**2)
            # Semiperimeter of triangle
            s = (a + b + c) / 2.0
            # Area of triangle by Heron's formula
            area = np.sqrt(s*(s-a)*(s-b)*(s-c))
            circum_r = a*b*c/(4.0*area)
            # Here's the radius filter.
            if circum_r < 1.0/alpha:
                add_edge(edges, edge_points, coords, ia, ib)
                add_edge(edges, edge_points, coords, ib, ic)
                add_edge(edges, edge_points, coords, ic, ia)
        
        m = geometry.MultiLineString(edge_points)
        triangles = list(polygonize(m))
        return cascaded_union(triangles), edge_points