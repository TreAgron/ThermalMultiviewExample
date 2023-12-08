# "C:\ProgramData\Anaconda3\envs\Geoprocessing"
import math
import os
import sys
import csv
import json
import pandas as pd
import numpy as np

import Metashape

directory_path = r'O:\Data-Work\22_Plant_Production-CH\224_Digitalisation\Simon_Treier_Files\ThermalMultiviewExample'

GEOJSON = os.path.join(directory_path, 'GeojsonsExample\Example.geojson')
DEM = os.path.join(directory_path, 'DEM\DEM.tif')

project_list = [(os.path.join(directory_path, 'ProjectExamples'), 'CH_1260_P004_20210701.13.45.1_40m_Therm.psx', os.path.join(directory_path, 'ThermalData'), 'CamPos1.txt', 'Masks_1'),
                (os.path.join(directory_path, 'ProjectExamples'), 'CH_1260_P004_20210701.13.45.2_40m_Therm.psx', os.path.join(directory_path, 'ThermalData'), 'CamPos2.txt', 'Masks_2')]

# This function was taken from https://gitlab.ethz.ch/crop_phenotyping/PhenoFly_data_processing_tools/-/blob/master/ImageProjectionAgisoft/
# Please have a look there for further information.
def generate_image_masks_with_DEM(path_polygons, path_masks_output, zero_gis):
    print("Processing chunk " + chunk.label)
    print(path_polygons)

    points_list = []

    with open(path_polygons) as json_file:
        feature_collection = json.load(json_file)
        features = feature_collection['features']
        print(len(features), 'features in geojson found, extraction points for projection')

        for feature in features:
            properties = feature['properties']
            geometry = feature['geometry']

            label = properties['plot_label']

            for i, corner in enumerate(geometry['coordinates'][0]):
                points_list.append({'world_x': corner[0],
                                    'world_y': corner[1],
                                    'plot_label': label,
                                    'point': i
                                    })
    print(len(points_list), 'points prepared for projection')

    elevation = chunk.elevation
    points = [Metashape.Vector((float(row['world_x']),
                                float(row['world_y']),
                                elevation.altitude(
                                    Metashape.Vector((
                                        float(row['world_x']),
                                        float(row['world_y'])
                                    )))
                                )) for row in points_list]

    plot_labels = [row['plot_label'] for row in points_list]
    point_numbers = [row['point'] for row in points_list]

    rows = []
    for i, point in enumerate(points):
        for camera in chunk.cameras:
            ret = camera.project(chunk.transform.matrix.inv().mulp(chunk.crs.unproject(point)))
            if ret:
                image_x, image_y = ret

                if 0 <= image_y < camera.sensor.height and \
                        0 <= image_x < camera.sensor.width:
                    photo = camera.label
                    sensor = chunk.label
                    world_x, world_y, world_z = point
                    plot_label = plot_labels[i]
                    point_number = point_numbers[i]

                    print("Plot " + plot_label + " found on image " + photo)

                    row = {"image_x": image_x,
                           "image_y": image_y,
                           "image": photo,
                           "sensor": sensor,
                           "world_x": world_x,
                           "world_y": world_y,
                           "world_z": world_z,
                           "plot_label": plot_label,
                           "point_number": point_number,
                           "type": "canopy"}
                    rows.append(row)

    if len(rows) == 0:
        print("No points found! Are the coordinate system of the agisoft project and of the plot geojson the same?")
        return (1)

    keys = rows[0].keys()

    with open(path_masks_output + "/projected_points.csv", 'w', newline='') as output_file:
        dict_writer = csv.DictWriter(output_file, keys)
        dict_writer.writeheader()
        dict_writer.writerows(rows)

    chunk.exportCameras(path_masks_output + "/camera_positions_.csv",
                        format=Metashape.CamerasFormat.CamerasFormatOPK)
    with open(path_masks_output + "/camera_positions_.csv", 'r') as infile:
        with open(path_masks_output + "/camera_positions.csv", 'w') as outfile:
            csvreader = csv.reader(infile, delimiter='\t', quotechar='|')
            next(csvreader, None)
            next(csvreader, None)

            csvwriter = csv.writer(outfile, delimiter=',', quotechar='|', quoting=csv.QUOTE_MINIMAL)
            csvwriter.writerow(
                ["image", "X", "Y", "Z", "Omega", "Phi", "Kappa", "r11", "r12", "r13", "r21", "r22", "r23", "r31",
                 "r32", "r33"])

            csvwriter.writerows(row for row in csvreader)

    # read projected points file
    single_images_coords = pd.read_csv(path_masks_output + "/projected_points.csv", skip_blank_lines=True)

    single_images_coords['image_y'] = -single_images_coords['image_y'] if zero_gis else single_images_coords[
        'image_y']

    # Group by polygons for local coords
    single_images_coords_image = pd.DataFrame(single_images_coords.pivot_table(
        index=['image', 'plot_label', 'type'],
        values=['image_x', 'image_y'],
        columns='point_number').to_records())
    single_images_coords_image = single_images_coords_image.dropna()
    # Group by images for world coords (mean)
    single_images_coords_world = pd.DataFrame(single_images_coords.pivot_table(
        index=['plot_label', 'type'],
        values=['world_x', 'world_y', 'world_z'],
        aggfunc="mean").to_records())
    # Merge all to one df
    single_images_coords_both = pd.merge(single_images_coords_image, single_images_coords_world,
                                         on=["plot_label", "type"])

    # Get camera position file to calculate viewpoints
    camera_coords = pd.read_csv(path_masks_output + "/camera_positions.csv", )

    # Merge camera position with projected plots
    single_images_coords_all = pd.merge(single_images_coords_both, camera_coords, on="image")
    # Calculate viewpoints
    azimuth_proj = np.arctan2(single_images_coords_all.world_y - single_images_coords_all.Y,
                              single_images_coords_all.world_x - single_images_coords_all.X)
    single_images_coords_all['azimuth_angle'] = 2 * np.pi - (azimuth_proj) % (2 * np.pi)
    single_images_coords_all['zenith_angle'] = -(
            np.arctan((single_images_coords_all.world_z - single_images_coords_all.Z) / np.sqrt(
                (single_images_coords_all.world_x - single_images_coords_all.X) * (
                        single_images_coords_all.world_x - single_images_coords_all.X) +
                (single_images_coords_all.world_y - single_images_coords_all.Y) *
                (single_images_coords_all.world_y - single_images_coords_all.Y))) - np.pi / 2)

    single_images_coords_all['camera_pos_world_x'] = single_images_coords_all.X
    single_images_coords_all['camera_pos_world_y'] = single_images_coords_all.Y
    single_images_coords_all['camera_pos_world_z'] = single_images_coords_all.Z

    # Create polygons for geojson files
    polygons = []
    for index, row in single_images_coords_all.iterrows():
        polygons.append(
            [(row["('image_x', 0)"], row["('image_y', 0)"]),
             (row["('image_x', 1)"], row["('image_y', 1)"]),
             (row["('image_x', 2)"], row["('image_y', 2)"]),
             (row["('image_x', 3)"], row["('image_y', 3)"]),
             (row["('image_x', 0)"], row["('image_y', 0)"])]
        )

    # Geopandas df to allow geojson export
    df_single_images_coords = pd.DataFrame(
        single_images_coords_all[
            ['image', 'plot_label', 'type', 'world_x', 'world_y', 'world_z', 'azimuth_angle', 'zenith_angle',
             'camera_pos_world_x', 'camera_pos_world_y', 'camera_pos_world_z']])
    df_single_images_coords['geometry'] = polygons

    # Group by image and export files
    df_single_images_coords['image'] = df_single_images_coords['image'].str.split(".").apply(lambda x: x[0])
    df_grouped = df_single_images_coords.groupby('image')
    for image, df_group in df_grouped:
        feature_collection = {}
        feature_collection['type'] = "FeatureCollection"
        features_list = []
        dicts = df_group.to_dict('records')
        for row in dicts:
            properties = row
            geometry = {"type": "Polygon", "coordinates": [row['geometry']]}
            del properties['geometry']
            feature = {"type": "Feature"}
            feature['properties'] = properties
            feature['geometry'] = geometry
            features_list.append(feature)

        feature_collection['features'] = features_list

        with open(path_masks_output + "/" + image + ".geojson", 'w') as outfile:
            json.dump(feature_collection, outfile, indent=4)

    os.remove(path_masks_output + "/projected_points.csv")
    os.remove(path_masks_output + "/camera_positions_.csv")
    os.remove(path_masks_output + "/camera_positions.csv")


# Aply the above function for each project defined at the beginning.
for project in project_list:
    project_path = os.path.join(project[0], project[1])
    campos_path = os.path.join(project[2], project[3])
    masks_path = os.path.join(project[2], project[4])
    print(masks_path)
    doc = Metashape.Document()
    doc.open(path=project_path)
    doc.read_only = False
    chunk = doc.chunks[0]
    chunk.importRaster(DEM)
    chunk.exportReference(campos_path, format=Metashape.ReferenceFormatCSV, items=Metashape.ReferenceItemsCameras,
                          delimiter=",")

    if os.path.exists(masks_path):
        pass
    else:
        os.mkdir(masks_path)

    generate_image_masks_with_DEM(GEOJSON, masks_path, "y")
