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
import math






class PlottingService:
    def __init__(self):

        pass

    def plot_data(
            self, 
            plot_points, 
            plot_outline, 
            data_fp, 
            ax=None, 
            eps = 1,
            sf = .5,
            point_size = 1,
            point_color = "#0B6A00",
            fill_range = True,
            range_outline_size = 1
        ):

        with open(data_fp, 'r') as file:
            data = json.load(file)
        points = self.get_points(data)


        if not ax:  # In case ax is None or not passed
            fig, ax = plt.subplots(figsize=(15, 15), dpi =500, subplot_kw={'projection': ccrs.PlateCarree()})
        else:
            # Use the existing ax to clear and plot, no need to create a new fig, ax
            ax.clear()

        # fig, ax = plt.subplots(figsize=(10, 10), subplot_kw={'projection': ccrs.PlateCarree()})
        ax.add_feature(cfeature.COASTLINE, linewidth=0.25,zorder =100)
        ax.add_feature(cfeature.BORDERS, linewidth=0.25,zorder =100)
        ax.add_feature(cfeature.STATES, edgecolor = 'gray', linewidth=0.125,zorder =99)
        ax.add_feature(cfeature.LAKES, edgecolor='black',linewidth=0.25, zorder =100)
        ax.add_feature(cfeature.OCEAN, edgecolor='black',linewidth=0.25, zorder = 100)


        # TODO: Add this stuff to GUI
        if plot_points:
            # Extract longitudes and latitudes for plotting
            longitudes, latitudes = zip(*points)
            ax.scatter(
                longitudes, 
                latitudes, 
                transform=ccrs.Geodetic(), 
                s=point_size, 
                color=point_color, 
                marker='o', 
                edgecolor='none', 
                zorder = 10
            )

        ## TODO put this in its own function and save calcs for future plotting rather than recalc every time
        if plot_outline:
            clusters = self.get_clusters(points, eps)
            unique_clusters = np.unique(clusters)

            hulls = []

            for cluster in unique_clusters:
                if cluster == -1:
                    continue  # Skip noise points, labeled as -1

                points_np = np.array(points)

                cluster_points = points_np[clusters == cluster]

                hulls.append(self.build_hull(cluster_points,0.1))

            
            for hull in hulls:
                # x, y = hull.exterior.coords.xy
                # hull_points = np.column_stack((x, y))
                hull_points = np.array(hull.exterior.coords)
                x_smooth, y_smooth = self.smooth_hull(hull_points, s = sf, num_points=1000)

                if fill_range == True:
                    ax.fill(x_smooth, y_smooth, 'r-', linewidth=0, zorder = 5)
                else: 
                    ax.plot(x_smooth, y_smooth, 'r-', linewidth=range_outline_size, zorder = 5)




    def get_points(self, data):
        points = []
        for record in data:  # Directly iterate over the list of records
            if 'decimalLongitude' in record and 'decimalLatitude' in record:
                lon = record['decimalLongitude']
                lat = record['decimalLatitude']

                # Skip the record if longitude or latitude is NaN or infinite
                if math.isnan(lon) or math.isnan(lat) or math.isinf(lon) or math.isinf(lat):
                    continue

                points.append((lon, lat))  # Collecting points as (longitude, latitude) tuples
        return points

        

    def get_clusters(self, points, eps):
        dbscan = DBSCAN(eps=eps, min_samples=100)
        clusters = dbscan.fit_predict(points)
        
        return clusters
    
    def build_hull(self, points, alpha):
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
        return cascaded_union(triangles) #, edge_points # Might need edge points for determining inside or outside of hull

    def smooth_hull(self, hull_points, s=0.01, k=3, num_points=1000):
        """
        Smooth the boundary of a hull using spline interpolation.

        :param hull_points: Coordinates of the hull's boundary points (x, y).
        :param s: Smoothing factor.
        :param k: Degree of the spline. Cubic splines are common (k=3).
        :param num_points: Number of points to generate along the smoothed curve.
        :return: x_new, y_new - smoothed coordinates along the hull boundary.
        """

        hull_points = np.array(hull_points)

        if hull_points.shape[0] < k + 1:
            # print(f"Not enough unique points for spline fitting. Required: {k+1}, provided: {hull_points.shape[0]}")
            # Handle the case of insufficient points, e.g., by returning the original points
            return hull_points[:, 0], hull_points[:, 1]


        x, y = hull_points.T  # Transpose to separate x and y

        try:
            # Fit spline to hull's boundary points and evaluate it
            tck, u = splprep([x, y], s=s, k=k)
            u_new = np.linspace(0, 1, num_points)
            x_new, y_new = splev(u_new, tck)
            return x_new, y_new
        except Exception as e:
            print(f"Error during spline fitting: {e}")
            # Handle error, e.g., by returning the original points or a subset
            return x, y

    
    
    
    def get_hull(self):
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