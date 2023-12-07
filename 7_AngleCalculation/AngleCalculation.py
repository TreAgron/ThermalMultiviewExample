# "C:\ProgramData\Anaconda3\envs\Geoprocessing"
import numpy as np
from osgeo import _gdal
from osgeo import ogr
import geojson
import math
from skimage import io
import numpy as np
import pandas as pd
from matplotlib.path import Path
import os
from timeit import default_timer as timer
import warnings
from datetime import timedelta, datetime
import geopandas as gpd
import matplotlib.pyplot as plt
from shapely.geometry import MultiLineString, LineString
from pyproj import CRS
from shapely.errors import ShapelyDeprecationWarning
from PIL import Image, ExifTags
import csv
import sys
from PIL.ExifTags import TAGS
import subprocess
import json

# Adding a new path here allows python to find the Agisoft_functions file

directory_path = r'O:\Data-Work\22_Plant_Production-CH\224_Digitalisation\Simon_Treier_Files\ThermalMultiviewExample'

sys.path.append(os.path.join(directory_path, '7_AngleCalculation\Functions'))
import SunPosCalc

warnings.filterwarnings("ignore", category=ShapelyDeprecationWarning)
warnings.simplefilter(action='ignore', category=FutureWarning)


df_attribution_path = os.path.join(directory_path, 'DesignExample\ExampleAssign.csv')
geojson_centroids_path = os.path.join(directory_path, 'GeojsonsExample\ExampleCentroids.geojson')
output_path_centroid_lines = os.path.join(directory_path, 'ThermalData')

query_percentile = 50

location = (
    46.39991, +6.23578)  # Location of experiment for determination of solar position in WGS84 coordinates with decimal digits.

mask_geojson_paths = [os.path.join(directory_path, 'ThermalData\Masks_1'),
                      os.path.join(directory_path, 'ThermalData\Masks_2')]


start = timer()

# Cartesian coordinates to a distance and a radiance angle
def cart2RadPol(x, y):
    distance = np.sqrt(x ** 2 + y ** 2)
    RadAngle = np.arctan2(y, x) - math.pi / 2
    return (distance, RadAngle)

# Cartesian coordinates to a distance and a degree angle
def cart2DegPol(x, y):
    distance = np.sqrt(x ** 2 + y ** 2)
    DegAngle = toDeg(np.arctan2(y, x))
    return (distance, DegAngle)

# Degrees to radiance
def toRadians(DegAngle):
    RadAngle = np.prod([np.divide(DegAngle, 360), math.pi, 2])
    return RadAngle

def DegPol2cart(dist, DegAngle):
    x = round(dist * np.cos(toRadians(DegAngle)), 4)
    y = round(dist * np.sin(toRadians(DegAngle)), 4)
    return (x, y)

def toDeg(RadAngle):
    DegAngle = RadAngle * (180 / math.pi)
    if DegAngle < 0:
        DegAngle = DegAngle + 360
    return DegAngle

def normalizeAngle(angle):
    while angle < 0:
        angle += 360
    while angle >= 360:
        angle -= 360
    return angle

def AngleToAzimuthOrientation(
        angle):  # convert from  zero at west to zero at north and from clockwise to counterclockwise
    angle = normalizeAngle(90 - angle)
    return angle

def get_exif(fn):
    ret = {}
    i = Image.open(fn)
    info = i._getexif()
    for tag, value in info.items():
        decoded = TAGS.get(tag, tag)
        ret[decoded] = value
    return ret

df_attribution = pd.read_csv(df_attribution_path, sep=';')
df_centroids = gpd.read_file(geojson_centroids_path)

df_centroids.head()
df_centroids['lon'] = df_centroids.geometry.map(lambda p: p.x)
df_centroids['lat'] = df_centroids.geometry.map(lambda p: p.y)

np.min(pd.unique(df_centroids['Row']))
df_centroids = pd.DataFrame(df_centroids)

crs = CRS("epsg:2056")
polygon_geom_ls = []
row = 1
coords = []
centroid_angles = []
counter = 1

for row in pd.unique(df_centroids['Row']):
    print(row)
    counter += 1
    df_centroids_rowwise = df_centroids[df_centroids['Row'] == row]
    min_centroid = df_centroids_rowwise[df_centroids_rowwise['Range'] == np.min(df_centroids_rowwise['Range'])]
    max_centroid = df_centroids_rowwise[df_centroids_rowwise['Range'] == np.max(df_centroids_rowwise['Range'])]

    coord = ((float(str(list([min_centroid['lon']][0]))[1:-1]), float(str(list([min_centroid['lat']][0]))[1:-1])),
             (float(str(list([max_centroid['lon']][0]))[1:-1]), float(str(list([max_centroid['lat']][0]))[1:-1])))
    coords.append(coord)

    lon_diff, lat_diff = float(str(list([max_centroid['lon']][0]))[1:-1]) - float(
        str(list([min_centroid['lon']][0]))[1:-1]), float(str(list([max_centroid['lat']][0]))[1:-1]) - float(
        str(list([min_centroid['lat']][0]))[1:-1])
    planar_dist, planar_angle = cart2DegPol(lon_diff, lat_diff)
    planar_angle = AngleToAzimuthOrientation(planar_angle)

    if planar_angle >= 180:  # Assure centroid angle is between 0 and 180 from north
        planar_angle = planar_angle - 180
    centroid_angles.append(planar_angle)

mean_centroid_angle = np.mean(centroid_angles)

lines = MultiLineString(coords)
polygon = gpd.GeoDataFrame(index=[0], crs=crs, geometry=[lines])
polygon.to_file(filename=os.path.join(output_path_centroid_lines, 'centroid_lines_polygon.geojson'), driver='GeoJSON')
# polygon.to_file(filename=os.path.join(output_path, 'centroid_lines_polygon.shp'), driver='ESRI Shapefile')


counter = 1
for mask_geojson_path in mask_geojson_paths:
    print(mask_geojson_path, ' was loaded')

    df_angle_sheet = []

    # For each project, list all geojson files
    geojson_files = [f for f in os.listdir(mask_geojson_path) if f.endswith('.geojson')]

    # Make a list where for ech image, all plots are listed that are within these image
    list_plots_in_image = []

    for geojson_file in geojson_files:
        # Import geojson
        with open(os.path.join(mask_geojson_path, geojson_file)) as f:
            gj = geojson.load(f)
        # Import any df and transform to numpy array
        for features in gj['features']:
            square_coords = features['geometry']["coordinates"][0]  # get coordinates for for the single rectangles
            square = ogr.Geometry(ogr.wkbLinearRing)
            square.AddPoint(square_coords[0][0], square_coords[0][1])
            square.AddPoint(square_coords[1][0], square_coords[1][1])
            square.AddPoint(square_coords[2][0], square_coords[2][1])
            square.AddPoint(square_coords[3][0], square_coords[3][1])
            square.AddPoint(square_coords[0][0], square_coords[0][1])

            poly = ogr.Geometry(ogr.wkbPolygon)
            poly.AddGeometry(square)
            square_centroid = poly.Centroid().GetPoint()
            sensor_x = np.round(square_centroid[0], 1)
            sensor_y = np.round(square_centroid[1], 1)

            list_plots_in_image.append((features['properties']['image'], features['properties']['plot_label'],
                                        features['properties']['world_z'],
                                        features['properties']['camera_pos_world_z'],
                                        sensor_x, sensor_y))
            # print(features['properties']['image'])
    end = timer()

    lines_geojson_pos_path = mask_geojson_path.replace("Masks_", "Lines_")
    if os.path.exists(lines_geojson_pos_path):
        pass
    else:
        os.mkdir(lines_geojson_pos_path)

    images_geojson_pos_path = mask_geojson_path.replace("Masks_", "")
    output_path_angles = os.path.join(mask_geojson_path.replace("Masks_", "Angles") + ".csv")
    exposure_pos_path = os.path.join(mask_geojson_path.replace("Masks_", "CamPos") + '.txt')
    df_exposure_pos = pd.read_csv(exposure_pos_path, skiprows=1)
    percentiles_path = os.path.join(mask_geojson_path, 'Percentiles.csv')
    df_percentiles = pd.read_csv(percentiles_path)
    df_percentiles = df_percentiles.query('Percentile == @query_percentile')
    df_percentiles.head()

    # Itteration dummy:
    row = [df_exposure_pos.iloc[64], df_exposure_pos.iloc[64]]

    for row in df_exposure_pos.iterrows():
        print(row[1]['#Label'])
        coords = []
        image_by_exposure_df = row[1]['#Label']
        lon_exposure = row[1]['X_est']
        lat_exposure = row[1]['Y_est']
        image_by_exposure_df_trunk = image_by_exposure_df.replace(".jpg", "")

        if (df_percentiles['Image'].eq(image_by_exposure_df_trunk)).any():
            df_percentiles_by_image = df_percentiles[df_percentiles['Image'].str.match(image_by_exposure_df_trunk)]
        else:
            pass

        image_path = os.path.join(images_geojson_pos_path, image_by_exposure_df)

        # Extract timestamp

        if image_path:

            if os.path.exists(image_path):
                pass
            else:
                continue

            # Make a map with tag names
            get_exif(image_path)['DateTimeOriginal']

            date_obj = datetime.strptime(get_exif(image_path)['DateTimeOriginal'], '%Y:%m:%d %H:%M:%S')

            # Extract central temperature
            meta_json = subprocess.check_output(
                ["exiftool", image_path, '-CentralTemperature', '-j'])  # Change
            central_temperature = json.loads(meta_json.decode())[0]['CentralTemperature']

        when = (date_obj.year, date_obj.month, date_obj.day, date_obj.hour, date_obj.minute, date_obj.second, +2)

        azimuth_sun, elevation_sun = SunPosCalc.sunpos(when, location, True)
        zenith_sun = 90 - elevation_sun

        # Following calculations assume a dummy length of 100 in Sun direction
        rel_x_sun = np.prod([100, np.sin(toRadians(elevation_sun)), np.cos(toRadians(
            360 - azimuth_sun))])  # same absolute value as lat_diff, but different rel coordinate system (0 deg at north, not east)
        rel_y_sun = np.prod([100, np.sin(toRadians(elevation_sun)), np.sin(toRadians(
            360 - azimuth_sun))])  # same absolute value as lat_diff, but different rel coordinate system (0 deg at north, not east)
        rel_z_sun = np.prod([100, np.cos(toRadians(elevation_sun))])

        list_plot_by_exposure = []
        for plot_in_image in list_plots_in_image:
            plot_in_image_image = plot_in_image[0]
            if image_by_exposure_df_trunk == plot_in_image_image:
                list_plot_by_exposure.append([plot_in_image[1], plot_in_image[2], plot_in_image[3], plot_in_image[4],
                                              plot_in_image[5]])  # Change
            else:
                pass

        # Iteration dummy
        # plot_by_exposure = list_plot_by_exposure[27]

        for plot_by_exposure in list_plot_by_exposure:
            df_centroids_rowwise = df_centroids[df_centroids['plot_label'] == plot_by_exposure[0]]
            if len(str(list(df_centroids_rowwise['lon']))[1:-1]) == 0:
                pass
            else:
                coord = ((float(str(list(df_centroids_rowwise['lon']))[1:-1]),
                          float(str(list(df_centroids_rowwise['lat']))[1:-1])),
                         (float(lon_exposure), float(lat_exposure)))
                coords.append(coord)

                variety = df_centroids_rowwise['Variety'].values[0]

                lon_diff, lat_diff = float(str(list(df_centroids_rowwise['lon']))[1:-1]) - float(lon_exposure), float(
                    str(list(df_centroids_rowwise['lat']))[1:-1]) - float(lat_exposure)
                planar_dist, planar_angle = cart2DegPol(lon_diff, lat_diff)
                azimuth_drone = AngleToAzimuthOrientation(planar_angle)

                Temp_by_img_plot = \
                    df_percentiles_by_image[df_percentiles_by_image['Plot'].str.match(plot_by_exposure[0])][
                        'Temperature'].values[0]
                Central_4pixel_temp = \
                    df_percentiles_by_image[df_percentiles_by_image['Plot'].str.match(plot_by_exposure[0])][
                        'Central_4pixel_temp'].values[0]

                planar_diff_angle_row_dir = normalizeAngle(mean_centroid_angle - azimuth_drone)
                z_diff = plot_by_exposure[2] - plot_by_exposure[1]

                tot_dist = np.sqrt(z_diff ** 2 + lon_diff ** 2 + lat_diff ** 2)

                elevation_drone = toDeg(np.arctan(np.divide(z_diff, planar_dist)))

                rel_x_drone = np.prod([tot_dist, np.sin(toRadians(elevation_drone)), np.cos(toRadians(
                    360 - azimuth_drone))])  # same absolute value as lat_diff, but different rel coordinate system (0 deg at north, not east)
                rel_y_drone = np.prod([tot_dist, np.sin(toRadians(elevation_drone)), np.sin(toRadians(
                    360 - azimuth_drone))])  # same absolute value as lat_diff, but different rel coordinate system (0 deg at north, not east)
                rel_z_drone = z_diff

                dot_product = np.prod([rel_x_sun, rel_x_drone]) + np.prod([rel_y_sun, rel_y_drone]) + np.prod(
                    [rel_z_sun, rel_z_drone])
                lenght_sun_vec = np.sqrt(rel_x_sun ** 2 + rel_y_sun ** 2 + rel_z_sun ** 2)
                lenght_drone_vec = np.sqrt(rel_x_drone ** 2 + rel_y_drone ** 2 + rel_z_drone ** 2)
                angleSunPlotDrone = toDeg(
                    np.arccos(np.divide(dot_product, np.prod([lenght_sun_vec, lenght_drone_vec]))))

                longitudinal_dist_from_ex_pos, lateral_dist_from_ex_pos = DegPol2cart(planar_dist,
                                                                                      planar_diff_angle_row_dir)

                lateral_angle_from_ex_pos = toDeg(np.arctan2(np.abs(lateral_dist_from_ex_pos),
                                                             np.abs(z_diff)))
                longitudinal_angle_from_ex_pos = toDeg(np.arctan2(np.abs(longitudinal_dist_from_ex_pos),
                                                                  np.abs(z_diff)))

                azimuth_diff = normalizeAngle(azimuth_sun - azimuth_drone)

                longitudinal_dist_sun_direction, lateral_dist_sun_direction = DegPol2cart(planar_dist,
                                                                                          azimuth_diff)  # Change

                lateral_angle_from_sun_direction = toDeg(np.arctan2(np.abs(lateral_dist_sun_direction),
                                                                    np.abs(z_diff)))
                longitudinal_angle_from_sun_direction = toDeg(np.arctan2(np.abs(longitudinal_dist_sun_direction),
                                                                         np.abs(z_diff)))

                dist_vect = np.array(
                    [lateral_dist_from_ex_pos, longitudinal_dist_from_ex_pos, lateral_dist_sun_direction,
                     longitudinal_dist_sun_direction])
                angl_vect = np.array(
                    [lateral_angle_from_ex_pos, longitudinal_angle_from_ex_pos, lateral_angle_from_sun_direction,
                     longitudinal_angle_from_sun_direction])
                angl_vect = np.where(dist_vect < 0, -angl_vect, angl_vect)

                lateral_angle_from_ex_pos = angl_vect[0]
                longitudinal_angle_from_ex_pos = angl_vect[1]
                lateral_angle_from_sun_direction = angl_vect[2]
                longitudinal_angle_from_sun_direction = angl_vect[3]

                elevation_diff = elevation_sun - elevation_drone

                df_angle_sheet.append([image_by_exposure_df,
                                       variety,
                                       float(lon_exposure),
                                       float(lat_exposure),
                                       plot_by_exposure[2],
                                       plot_by_exposure[0],
                                       float(str(list(df_centroids_rowwise['lon']))[1:-1]),
                                       float(str(list(df_centroids_rowwise['lat']))[1:-1]),
                                       plot_by_exposure[1],
                                       lon_diff,
                                       lat_diff,
                                       z_diff,
                                       planar_dist,
                                       azimuth_drone,
                                       tot_dist,
                                       mean_centroid_angle,
                                       planar_diff_angle_row_dir,
                                       lateral_dist_from_ex_pos,
                                       longitudinal_dist_from_ex_pos,
                                       lateral_angle_from_ex_pos,
                                       longitudinal_angle_from_ex_pos,
                                       azimuth_sun,
                                       elevation_sun,
                                       azimuth_diff,
                                       elevation_diff,
                                       angleSunPlotDrone,
                                       longitudinal_dist_sun_direction,  # Change
                                       lateral_dist_sun_direction,  # Change
                                       longitudinal_angle_from_sun_direction,  # Change
                                       lateral_angle_from_sun_direction,  # Change
                                       Temp_by_img_plot,
                                       central_temperature,  # Change
                                       Central_4pixel_temp,  # Change
                                       date_obj,
                                       plot_by_exposure[3],  # Change
                                       plot_by_exposure[4]])  # Change

        lines = MultiLineString(coords)

        if len(coords) == 0:
            "nope"
        else:
            polygon = gpd.GeoDataFrame(index=[0], crs=crs, geometry=[lines])
            polygon.to_file(filename=os.path.join(lines_geojson_pos_path,
                                                  image_by_exposure_df_trunk + '_centroid_lines_per_exposure.geojson'),
                            driver='GeoJSON')

    # noinspection PyTypeChecker
    df_angle_sheet = pd.DataFrame(df_angle_sheet, columns=['Exposure_image',
                                                           'Variety',
                                                           'Lon_exposure',
                                                           'Lat_exposure',
                                                           'Z_exposure',
                                                           'Plot_label',
                                                           'Lon_plot',
                                                           'Lat_plot',
                                                           'Z_plot',
                                                           'Lon_diff',
                                                           'Lat_diff',
                                                           'Z_diff',
                                                           'Planar_dist',
                                                           'Azimuth_drone',
                                                           'Total_dist',
                                                           'Mean_centroid_angle',
                                                           'Planar_diff_from_mean_centroid_angle',
                                                           'Lateral_dist_from_ex_pos',
                                                           'Longitudinal_dist_from_ex_pos',
                                                           'Lateral_angle_from_ex_pos',
                                                           'Longitudinal_angle_from_ex_pos',
                                                           'Azimuth_sun',
                                                           'Elevation_sun',
                                                           'Azimuth_diff',
                                                           'Elevation_diff',
                                                           'AngleSunPlotDrone',
                                                           'Longitudinal_dist_sun_direction',  # Change
                                                           'Lateral_dist_sun_direction',  # Change
                                                           'Longitudinal_angle_from_sun_direction',  # Change
                                                           'Lateral_angle_from_sun_direction',  # Change
                                                           'Temp_by_img_plot',
                                                           'Central_Temp',  # Change
                                                           'Central_4pixel_temp',  # Change
                                                           'TimeStamp',
                                                           'Sensor_x',  # Change
                                                           'Sensor_y'])  # Change

    df_angle_sheet.to_csv(output_path_angles, encoding='utf-8', index=False)
    print(counter, ' of ', len(mask_geojson_paths), ' missions completed.')
    end = timer()
    print('Time passed: ', timedelta(seconds=end - start))
    counter += 1
