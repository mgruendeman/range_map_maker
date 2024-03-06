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

# Function to find the convex hull using the gift wrapping algorithm
def convex_hull(points):
    """Computes the convex hull of a set of 2D points."""
    hull = []
    start = points[np.argmin(points[:, 0])]  # start with the leftmost point
    hull.append(start)
    current = start
    while True:
        next_point = points[0]
        for point in points[1:]:
            if np.cross(point-current, next_point-current) > 0 or np.all(next_point == current):
                next_point = point
        if np.all(next_point == start):
            break
        hull.append(next_point)
        current = next_point
    return np.array(hull)

# def plot_cluster_hull(points, clusters, ax):
#     unique_clusters = np.unique(clusters)
#     for cluster in unique_clusters:
#         if cluster == -1:  # -1 means noise in DBSCAN
#             continue  # Optionally, skip plotting noise points
#         cluster_points = points[clusters == cluster]
#         hull_points = convex_hull(cluster_points).vertices
#         ax.scatter(cluster_points[:, 0], cluster_points[:, 1], s=5, transform=ccrs.Geodetic())
#         ax.plot(cluster_points[hull_points, 0], cluster_points[hull_points, 1], 'r-', transform=ccrs.Geodetic())
# def plot_cluster_hull(points, clusters, ax):
#     unique_clusters = np.unique(clusters)
#     for cluster in unique_clusters:
#         if cluster == -1:  # -1 means noise in DBSCAN
#             continue  # Optionally, skip plotting noise points
#         cluster_points = points[clusters == cluster]
#         hull = convex_hull(cluster_points)  # This now directly returns the hull points
#         hull = smooth_hull(hull)
#         if len(hull) < 3:  # Check if the hull has at least 3 points to form a polygon
#             continue  # Skip clusters with less than 3 points (cannot form a convex hull)
#         ax.scatter(cluster_points[:, 0], cluster_points[:, 1], s=5, transform=ccrs.Geodetic())
#         # Close the hull polygon by appending the first point at the end
#         hull_polygon = np.append(hull, [hull[0]], axis=0)
#         ax.plot(hull_polygon[:, 0], hull_polygon[:, 1], 'r-', transform=ccrs.Geodetic())
#         ax.fill(hull_points[:, 0], hull_points[:, 1], 'r', alpha=0.5, transform=ccrs.Geodetic())

def plot_cluster_hull(points, clusters, ax):
    unique_clusters = np.unique(clusters)
    for cluster in unique_clusters:
        if cluster == -1:  # -1 means noise in DBSCAN
            continue  # Optionally, skip plotting noise points
        cluster_points = points[clusters == cluster]
        hull_points = convex_hull(cluster_points)  # This returns the hull points
        if len(hull_points) < 3:  # Check if the hull has at least 3 points to form a polygon
            continue  # Skip clusters with less than 3 points (cannot form a convex hull)
        
        hull_polygon = Polygon(hull_points)  # Create a Shapely Polygon from the hull points
        smoothed_hull_polygon = smooth_hull(hull_polygon)  # Smooth the polygon
        
        # Extract smoothed points for plotting
        x, y = smoothed_hull_polygon.exterior.xy
        
        ax.scatter(cluster_points[:, 0], cluster_points[:, 1], s=5, transform=ccrs.Geodetic())
        ax.plot(x, y, 'r-', transform=ccrs.Geodetic())  # Plot smoothed hull
        # ax.fill(x, y, 'r', alpha=0.5, transform=ccrs.Geodetic())  # Optionally, fill the smoothed hull



        
# def smooth_hull(hull_polygon, smooth_factor=3, num_points=100):
#     # Extract the x and y coordinates of the hull_polygon
#     x, y = hull_polygon.exterior.xy
    
#     # Close the loop for the spline interpolation
#     x, y = np.append(x, x[0]), np.append(y, y[0])
    
#     # Fit spline to hull's boundary points
#     tck, u = splprep([x, y], s=smooth_factor)
    
#     # Generate new interpolated points for the smoothed curve
#     u_new = np.linspace(u.min(), u.max(), num_points)
#     x_new, y_new = splev(u_new, tck, der=0)
    
#     # Create a new smoothed polygon
#     smoothed_hull = Polygon(zip(x_new, y_new))
    
#     return smoothed_hull
# def smooth_hull(hull_polygon, smooth_factor=.02, num_points=1000):
#     # Extract the x and y coordinates of the hull_polygon
#     x, y = hull_polygon.exterior.xy
    
#     # Remove duplicate points
#     unique_points = np.unique(np.column_stack([x, y]), axis=0)
#     x, y = unique_points[:, 0], unique_points[:, 1]
    
#     # Ensure there are enough points for spline fitting
#     if len(x) < 4:
#         print("Not enough unique points for spline fitting.")
#         return hull_polygon  # Return the original polygon if not enough points
    
#     # Close the loop for the spline interpolation, if not already closed
#     if x[0] != x[-1] or y[0] != y[-1]:
#         x = np.append(x, x[0])
#         y = np.append(y, y[0])
    
#     try:
#         # Fit spline to hull's boundary points
#         tck, u = splprep([x, y], s=smooth_factor)
        
#         # Generate new interpolated points for the smoothed curve
#         u_new = np.linspace(u.min(), u.max(), num_points)
#         x_new, y_new = splev(u_new, tck, der=0)
        
#         # Create a new smoothed polygon
#         smoothed_hull = Polygon(zip(x_new, y_new))
#         return smoothed_hull
#     except ValueError as e:
#         print(f"Error in spline fitting: {e}")
#         return hull_polygon  # Return the original polygon in case of error
        
def smooth_hull(hull_points, s=0.0, k=3, num_points=1000):
    """
    Smooth the boundary of a hull using spline interpolation.

    :param hull_points: Coordinates of the hull's boundary points (x, y).
    :param s: Smoothing factor.
    :param k: Degree of the spline. Cubic splines are common (k=3).
    :param num_points: Number of points to generate along the smoothed curve.
    :return: x_new, y_new - smoothed coordinates along the hull boundary.
    """
    x, y = hull_points[:, 0], hull_points[:, 1]

    # Close the loop by appending the first point at the end
    x = np.append(x, x[0])
    y = np.append(y, y[0])

    # Fit spline to hull's boundary points and evaluate it
    tck, u = splprep([x, y], s=s, k=k)
    u_new = np.linspace(0, 1, num_points)
    x_new, y_new = splev(u_new, tck)

    return x_new, y_new

def smooth_path(vertices, smooth_factor=0.01, num_points=200):
    """Smooth the path defined by vertices using spline interpolation."""
    tck, u = splprep(vertices.T, s=smooth_factor, per=True)  # per=True for periodic (closed) spline
    u_new = np.linspace(u.min(), u.max(), num_points)
    x_new, y_new = splev(u_new, tck, der=0)
    return x_new, y_new

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


df = pd.read_csv('/home/tank-server/Downloads/0016730-240229165702484.csv',delimiter='\t',on_bad_lines='skip')


df.columns = df.columns.str.strip()

df = df.dropna(subset=['decimalLongitude', 'decimalLatitude'])

points = df[['decimalLongitude','decimalLatitude']].values


hull = ConvexHull(points)

dbscan = DBSCAN(eps=1, min_samples=10)
clusters = dbscan.fit_predict(points)

hull_points = convex_hull(points)

# water_bodies_gdf = gpd.read_file('water_bodies_data.shp')

alpha = 0.1  # Adjust this based on your dataset and desired concavity

concave_hull, _ = alpha_shape(points, alpha=alpha)
# plot_hull = smooth_path(concave_hull)

x, y = concave_hull.exterior.coords.xy
hull_points = np.column_stack((x, y))

x_smooth, y_smooth = smooth_hull(hull_points, num_points=1000)

plt.plot(x_smooth, y_smooth, 'r-', linewidth=2)

fig, ax = plt.subplots()
ax.plot(*concave_hull.exterior.xy)
plt.show()


fig, ax = plt.subplots(figsize=(10, 5), subplot_kw={'projection': ccrs.PlateCarree()})

# Add coastlines to the map
ax.coastlines()

ax.add_feature(cfeature.BORDERS)
ax.add_feature(cfeature.LAKES, edgecolor='black')
ax.add_feature(cfeature.OCEAN, edgecolor='black')#,zorder=100,)

# for simplex in hull.simplices:
#     ax.plot(points[simplex, 0], points[simplex, 1], 'k-', transform=ccrs.Geodetic())

unique_clusters = np.unique(clusters)
for cluster in unique_clusters:
    if cluster == -1:  # Optionally skip noise if -1 is considered noise
        continue
    cluster_points = points[clusters == cluster]
    if cluster_points.shape[0] < 3:  # Need at least 3 points to form a hull
        continue

    hull = ConvexHull(cluster_points)
    hull_vertices = cluster_points[hull.vertices]

    # Optionally, smooth the hull's outline
    x_smooth, y_smooth = smooth_path(hull_vertices)

    # Plot cluster points
    ax.scatter(cluster_points[:, 0], cluster_points[:, 1], s=5, transform=ccrs.Geodetic())
    # Plot smoothed hull
    ax.plot(x_smooth, y_smooth, 'r-', transform=ccrs.Geodetic())



# Plot the convex hull on the map
# Note: hull_points[:, 0] are your longitudes and hull_points[:, 1] are your latitudes
# ax.scatter(points[:, 0], points[:, 1], color='blue', marker='o', s=5, transform=ccrs.Geodetic(), label='Data Points')
# ax.plot(hull_points[:, 0], hull_points[:, 1], 'r-', transform=ccrs.Geodetic())  # Plot lines
# ax.fill(hull_points[:, 0], hull_points[:, 1], 'r', alpha=0.5, transform=ccrs.Geodetic())  # Fill the area

min_longitude = -49
max_longitude = -165
min_latitude = 10
max_latitude = 80


# Optionally, set the extent to zoom into your area of interest
ax.set_extent([min_longitude, max_longitude, min_latitude, max_latitude], crs=ccrs.PlateCarree())

# plot_cluster_hull(points, clusters, ax)

plt.show()