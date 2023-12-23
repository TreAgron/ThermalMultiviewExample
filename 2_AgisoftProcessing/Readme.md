### Description of the files in this folder:

The single images of individual flights need to be georeferenced, i.e. oriented in the same cartesian geograpahic coordinate reference system as the geojson  in the previous step. To that end, images are processed with the strcuture from motion software Agisoft Metashape. An orthomosaic is created at the end but it is not needed for subsequent analysis, yet it provides an overview of the thermal data for referencing purposes and quality check.

AgisoftProcessing.py:
Python file to process images of individual flights in the Agisoft Metashape stand-alone Python module. It needs to access the process- and functionfiles in the respective folders.

AgisoftProcessingPlan.csv:
The processing plan to define processing parameters and data paths for individual flights