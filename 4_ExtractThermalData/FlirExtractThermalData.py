# "C:\ProgramData\Anaconda3\envs\Geoprocessing"

from matplotlib import cm
import numpy as np
import os
import tifffile as tiff
from skimage.util import img_as_uint
import sys
import timeit
import importlib

directory_path = r'O:\Data-Work\22_Plant_Production-CH\224_Digitalisation\Simon_Treier_Files\ThermalMultiviewExample'

# Adding a new path here allows python to find the Agisoft_functions file
sys.path.append(os.path.join(directory_path, '4_ExtractThermalData\Functions'))
import FlirFunctionsImport

importlib.reload(FlirFunctionsImport)

flir = FlirFunctionsImport.FlirImageExtractor()

paths_to_radiometric_data = [os.path.join(directory_path, 'ThermalData\\1'),
                             os.path.join(directory_path, 'ThermalData\\2')]

# dummy path
path_to_radiometric_data = paths_to_radiometric_data[0]

flir = FlirFunctionsImport.FlirImageExtractor()
counter = 0

start = timeit.default_timer()

for path_to_radiometric_data in paths_to_radiometric_data:

    path_out = os.path.join(path_to_radiometric_data, 'Grayscale')
    print(path_out)

    if os.path.exists(path_out):
        print("Folder exist")
    else:
        print("Folder does not exist")
        os.mkdir(path_out)

    images_radiometric = [single_images for single_images in os.listdir(path_to_radiometric_data) if
                          single_images.endswith('.jpg')]
    counter = 0
    image_in = images_radiometric[75]
    for image_in in images_radiometric:
        path_radiometric_file = os.path.join(path_to_radiometric_data, image_in)

        flir.process_image(path_radiometric_file)

        thermal_np, thermal_raw, meta = flir.thermal_image_np

        thermal_np_mil = thermal_np * 1000
        thermal_np_mil = np.where(thermal_np_mil < 0, (2 ** 16) - 1, thermal_np_mil)
        thermal_np_mil = np.where(thermal_np_mil >= (2 ** 16) - 1, (2 ** 16) - 1, thermal_np_mil)
        thermal_np_mil = np.where(np.isnan(thermal_np_mil), (2 ** 16) - 1, thermal_np_mil)

        counter = counter + 1

        print(counter, " of ", len(images_radiometric), " images")
        progress = round(np.divide(counter, len(images_radiometric)), 4)
        print("Progress:", progress * 100, " %")

        gs_image_file = image_in.replace('DJI_', 'DJI_')
        path_out_file = os.path.join(path_out, gs_image_file)

        path_out_file_tiff = path_out_file.replace('.jpg', '.tiff')

        thermal_np_mil = np.rint(thermal_np_mil) / (2 ** 16)
        thermal_np_mil = img_as_uint(thermal_np_mil)

        execution_time = timeit.default_timer() - start

        print("Time elapsed: " + str(np.round(execution_time, 1)) + " s")  # It returns time in seconds

        print("****")

        tiff.imsave(path_out_file_tiff, thermal_np_mil)