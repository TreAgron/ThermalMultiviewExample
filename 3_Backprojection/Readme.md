### Description of the files in this folder:

ExportCameraLocationOrientationGeojsons.py:
Python file to project plot shapes from the geojson shape file to all images of individual flights in the Agisoft Metashape stand-alone Python module.

Input needed:
- An Agisoft Metashape project with aligned and georeferenced thermal images
* Digital elevation model (DEM), based on RGB or multispectral or multispectral data, which provide a higher spatial resolution thn thermal images.
* A geojson with the shapes of the plots. Each plot needs a unique string as identifier. The identifiers must be named 'plot-label'

The Agisoft Metashape project , the DEM and the geojson must all be in the same cartesian geographic reference system.

### Troubleshooting:
If geometry type of the geojson is Multipolygon and not polygon, the backprojection won't work. To change geometry type from Multipolygon to Polygon, open the geojson file in Qgis and:
- Vector
* Geometry Tools
* Multiparts to Singleparts
* Save