### Description of the files in this folder:

In this step, a geojson file is created based on a csv which represent the experimental design of experiment. The shapes must denn be adjusted to specific location in Qgis or similar. The geojson can also be created otherwise. If using other options to create the geojson, mind that the geometry type must be polygon (and not multipolygon). Each plot must have a unique string as identifier and the identifyer must be named 'plot_label'.

CreateRectanlgesFromCSVLV95.py:
Python file to create a geojson file based on a csv file that represents an experimental design (i.e. the plots of a research field). Mind to adapt the directory_path in line 10 to your folder location.



Example_assign.geojson:
This geojson is an example output of the python script. (Check it in Qgis or other GIS software)
