### Description of the files in this folder:

AngleCalculation.py:
Based on the geojson file, the centroids and the masks create during backprojection (step 3), for each plot on each image, specif viewing geometries are calculated and trigger timing derived based on meta data of the image. Mind to adapt the directory_path in line 29. In line 42, the query percentile can be defined (default is the 50<sup>th</sup> percentile, i.e. the median)