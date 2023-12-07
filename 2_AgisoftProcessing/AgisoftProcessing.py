# Run in PyAgisoft environemnt

# Python 3.8.13
import Metashape # version: 1.7.3
import os # part of python standard library
import csv # part of python standard library
import sys # part of python standard library
import statistics # part of python standard library
import numpy as np # version: 1.22.3
import json # part of python standard library
from timeit import default_timer as timer # part of python standard library
from datetime import timedelta, datetime # part of python standard library

# Define main directory path
directory_path = r'O:\Data-Work\22_Plant_Production-CH\224_Digitalisation\Simon_Treier_Files\ThermalMultiviewExample'

# Adding a new path here allows python to find the Agisoft_functions file
sys.path.append(os.path.join(directory_path, '2_AgisoftProcessing\Functions'))
import FunctionsAgisoft

# Read in the processing plan which contains all information about processing the campaigns in Agisoft
df_processing_plan = list()
with open(os.path.join(directory_path, '2_AgisoftProcessing\AgisoftProcessingPlan.csv'), 'r') as file:
    reader = csv.DictReader(file, delimiter=';')
    for row in reader:
        df_processing_plan.append(row)

# Create a list of objects of the class "job_instruction". One object for one campaign.
# A name for each campaign is automatically generated

list_job_instructions = list()
for i in range(0, len(df_processing_plan)):
    job = FunctionsAgisoft.job_instruction(df_processing_plan[i]['main_path'],
                                           df_processing_plan[i]['images_path'],
                                           df_processing_plan[i]['camera_model_path'],
                                           df_processing_plan[i]['GCP_path'],
                                           df_processing_plan[i]['use_distance_filtering'],
                                           df_processing_plan[i]['second_alignement_after_distance_filtering'],
                                           df_processing_plan[i]['country'],
                                           df_processing_plan[i]['postal_code_field'],
                                           df_processing_plan[i]['parcel'],
                                           df_processing_plan[i]['date'],
                                           df_processing_plan[i]['flight_height'],
                                           df_processing_plan[i]['colour_space_option'],
                                           df_processing_plan[i]['operation'],
                                           df_processing_plan[i]['EPSG'],
                                           df_processing_plan[i]['ortho_path'],
                                           df_processing_plan[i]['ortho_pixel_size'],
                                           df_processing_plan[i]['activated'])

    list_job_instructions.append(job)

    if list_job_instructions[i].images_path == "NA":
        project_path = os.path.join(directory_path, list_job_instructions[i].main_path)
    else:
        project_path = os.path.join(directory_path,
                                    list_job_instructions[i].main_path,
                                    list_job_instructions[i].name + '.psx')
        images_path = os.path.join(directory_path, list_job_instructions[i].images_path)

    start = timer()

    if list_job_instructions[i].activated == "TRUE":

        if list_job_instructions[i].operation == "align":
            print("align")
            with open(
                    os.path.join(directory_path, "2_AgisoftProcessing\Processes\AlignAgisoft.py"),
                    'r') as f:
                exec(f.read())

        elif list_job_instructions[i].operation == "model":
            with open(
                    os.path.join(directory_path, "2_AgisoftProcessing\Processes\DenseCloudDEMAgisoft.py"),
                    'r') as f:
                exec(f.read())

        elif list_job_instructions[i].operation == "tiff_ortho":
            with open(
                    os.path.join(directory_path, "2_AgisoftProcessing\Processes\OrthoTiffAgisoft.py"),
                    'r') as f:
                exec(f.read())

    end = timer()
    print('Time passed: ', timedelta(seconds=end - start))

    if list_job_instructions[i].activated == "FALSE":
        pass
