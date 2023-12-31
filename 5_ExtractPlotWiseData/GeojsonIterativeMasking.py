# "C:\ProgramData\Anaconda3\envs\Geoprocessing"
import geojson
import math
from skimage import io
import numpy as np
import pandas as pd
from matplotlib.path import Path
import os
import matplotlib.pyplot as plt


directory_path = r'C:\...\ThermalMultiviewExample'

geojson_paths = [os.path.join(directory_path, 'ThermalData\Masks_1'),
                 os.path.join(directory_path, 'ThermalData\Masks_2')]

geojson_path = geojson_paths[0]

for geojson_path in geojson_paths:

    thermal_data_path = geojson_path.replace("Masks_", "")
    thermal_data_path = os.path.join(thermal_data_path, 'Grayscale')
    geojson_files = [f for f in os.listdir(geojson_path) if f.endswith('.geojson')]

    list_percentiles = []
    geojson_file = geojson_files[100]
    for geojson_file in geojson_files:

        # Import geojson
        with open(os.path.join(geojson_path, geojson_file)) as f:
            gj = geojson.load(f)
        # Access single entries
        len(gj['features'])

        # Import any df and transform to numpy array
        thermal_data = io.imread(os.path.join(thermal_data_path, geojson_file.replace(".geojson", ".tiff")))
        thermal_data = np.asarray(thermal_data)

        Central_4pixel_temp = int(np.round(np.mean(thermal_data[255:257, 200:202])))

        features = gj['features'][0]

        for features in gj['features']:

            # Create an empty df for the mask
            np.shape(thermal_data)
            nx, ny = np.shape(thermal_data)[1], np.shape(thermal_data)[0]
            # Create vertex coordinates for each grid cell...
            # (<0,0> is at the top left of the grid in this system)
            x, y = np.meshgrid(np.arange(nx), np.arange(ny))
            x, y = x.flatten(), y.flatten()
            points = np.vstack((x, y)).T

            vec_features = np.abs(features['geometry']['coordinates'][0])

            poly_verts = [((vec_features[0][0]), (vec_features[0][1])),
                          ((vec_features[1][0]), (vec_features[1][1])),
                          ((vec_features[2][0]), (vec_features[2][1])),
                          ((vec_features[3][0]), (vec_features[3][1])),
                          ((vec_features[4][0]), (vec_features[4][1]))]

            path = Path(poly_verts)
            grid = path.contains_points(points)
            grid = grid.reshape((ny, nx))

            grid_int = grid.astype(int)

            x_vec = (vec_features[0][0],
                     vec_features[1][0],
                     vec_features[2][0],
                     vec_features[3][0],
                     vec_features[4][0])

            y_vec = (vec_features[0][1],
                     vec_features[1][1],
                     vec_features[2][1],
                     vec_features[3][1],
                     vec_features[4][1])

            thermal_data_masked = thermal_data * grid_int
            thermal_data_masked = thermal_data_masked.astype(float)
            cropped_array = thermal_data_masked[int(math.floor(np.min(y_vec))):int(math.ceil(np.max(y_vec))),
                            int(math.floor(np.min(x_vec))):int(math.ceil(np.max(x_vec)))]
            cropped_array[cropped_array == 0] = 'nan'

            for i in range(0, 101):
                list_percentiles.append([features['properties']['image'], features['properties']['plot_label'], str(i),
                                         str(np.nanpercentile(cropped_array, i)), geojson_path[-3],
                                         Central_4pixel_temp])
            np.nanmean(cropped_array)
            print(len(list_percentiles), " Percentiles calculated")

    df_percentiles = pd.DataFrame(list_percentiles,
                                  columns=['Image', 'Plot', 'Percentile', 'Temperature', 'Flight_Subgroup',
                                           'Central_4pixel_temp'])
    print(len(df_percentiles), " Percentiles calculated in df")
    df_percentiles.to_csv(os.path.join(geojson_path, 'Percentiles.csv'), encoding='utf-8', index=False)
