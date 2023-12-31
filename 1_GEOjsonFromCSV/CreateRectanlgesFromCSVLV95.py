# Run in Geoprocessing environment

# Python 3.8.13
from osgeo import ogr  # gdal version: 3.4.2
import osgeo.osr as osr  # gdal version:3.4.2
import os  # part of python standard library
import pandas as pd  # version: 1.4.4
import numpy as np  # version: 1.23.1

directory_path = r'C:\...\ThermalMultiviewExample\\'

df_design = pd.read_csv(os.path.join(directory_path, 'DesignExample\ExampleAssign.csv'), sep=";")
df_design = df_design.reset_index()  # make sure indexes pair with number of rows

# File name
outGeoJSONfn = os.path.join(directory_path, '1_GEOjsonFromCSV\ExampleAssign.geojson')

# Define coordinate reference system by it's EPSG number (e.g. 2056 for CH1903+ / LV95)
srs = osr.SpatialReference()
srs.ImportFromEPSG(2056)

# Define dimensions of the single rectangles (plots) and spacings between them
width_rectan = 2
hight_rectan = 6
spacing_width = 0.3
spacing_hight = 0.2

# Coordinates of the rough position of the field
lon_offset = 2507555
lat_offset = 1139303

# Define dimensions of the border spacing (offset from rough position of the field)
border_spacing = 0

x_intersept = border_spacing
y_intersept = border_spacing

base_shape = np.array([
    [0, 0],
    [width_rectan, 0],
    [width_rectan, hight_rectan],
    [0, hight_rectan],
    [0, 0]])


# create fields to be included in the geojson file (corresponding to the columns of the design csv file)
# Mind the data types (e.g. String or Integer...)
idField = ogr.FieldDefn('plot_label', ogr.OFTString)
varField = ogr.FieldDefn('Variety', ogr.OFTString)
rowField = ogr.FieldDefn('Row', ogr.OFTInteger)
rangeField = ogr.FieldDefn('Range', ogr.OFTInteger)
treatmentField = ogr.FieldDefn('Treatment', ogr.OFTString)
repField = ogr.FieldDefn('Rep', ogr.OFTString)
experimentField = ogr.FieldDefn('Experiment', ogr.OFTString)
yearField = ogr.FieldDefn('Year', ogr.OFTString)

# Create the output shapefile
GeoJSONDriver = ogr.GetDriverByName("GeoJSON")
if os.path.exists(outGeoJSONfn):
    GeoJSONDriver.DeleteDataSource(outGeoJSONfn)
outDataSource = GeoJSONDriver.CreateDataSource(outGeoJSONfn)
outLayer = outDataSource.CreateLayer(outGeoJSONfn, srs, geom_type=ogr.wkbPoint) # Define coordinate system

# Create the fields of the geojson
outLayer.CreateField(idField)
outLayer.CreateField(varField)
outLayer.CreateField(rowField)
outLayer.CreateField(rangeField)
outLayer.CreateField(treatmentField)
outLayer.CreateField(repField)
outLayer.CreateField(experimentField)
outLayer.CreateField(yearField)

for index, row in df_design.iterrows():
    print(row['plot_label'],
          row['Variety'],
          row['Row'],
          row['Range'],
          row['Treatment'],
          row['Rep'],
          row['Experiment'],
          row['Year'])

    # Create a rectangle for each Row:Range position. If order is not correct in row or range direction in the final
    # geojson, add or remove the "-" sign before "int(row.... " to invert the direction
    x_internal = [x_intersept + ((width_rectan + spacing_width) * (int(row['Row']))) + cord[0] + lon_offset for cord
                  in base_shape]
    y_internal = [y_intersept + ((hight_rectan + spacing_hight) * (-int(row['Range']))) + cord[1] + lat_offset for
                  cord in base_shape]

    # Create ring geometry by defining five points (first = last)
    square = ogr.Geometry(ogr.wkbLinearRing)
    square.AddPoint(float(x_internal[0]), float(y_internal[0]))
    square.AddPoint(float(x_internal[1]), float(y_internal[1]))
    square.AddPoint(float(x_internal[2]), float(y_internal[2]))
    square.AddPoint(float(x_internal[3]), float(y_internal[3]))
    square.AddPoint(float(x_internal[4]), float(y_internal[4]))

    # Create polygon from ring geometry
    polygon = ogr.Geometry(ogr.wkbPolygon)
    polygon.AddGeometry(square)

    # Create the feature and set values
    featureDefn = outLayer.GetLayerDefn()
    outFeature = ogr.Feature(featureDefn)
    outFeature.SetGeometry(polygon)
    outFeature.SetField('plot_label', row['plot_label'])
    outFeature.SetField('Variety', row['Variety'])
    outFeature.SetField('Row', row['Row'])
    outFeature.SetField('Range', row['Range'])
    outFeature.SetField('Treatment', row['Treatment'])
    outFeature.SetField('Rep', str(row['Rep']))
    outFeature.SetField('Experiment', str(row['Experiment']))
    outFeature.SetField('Year', row['Year'])

    outLayer.CreateFeature(outFeature)

    # dereference the feature
    outFeature = None

# Save and close DataSources
outDataSource = None
