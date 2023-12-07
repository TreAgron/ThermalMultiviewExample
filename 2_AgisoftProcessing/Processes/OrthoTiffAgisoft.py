# Aligning
# Check if project already exists



doc = Metashape.Document()
doc.open(path = project_path)
doc.read_only = False
chunk = doc.chunk

project_path_tif = project_path.replace(".psx", "_tif.psx")

if os.path.isfile(project_path_tif):
    question_string = "!!!!!!!!!!!!!!!!!!!!!!!!!!!\nProject\n" + project_path_tif + " exists! \nWant to replace it ?\n!!!!!!!!!!!!!!!!!!!!!!!!!!!\n"
    if Agisoft_functions.yes_or_no(question_string):
        pass
    else:
        print("Process stopped!!!")
        print("Change path in 'processing_plan.csv' to save project !")
        sys.exit()

ortho_folder = main_path + "/ortho"
flight_subgroup     = images_path.rsplit("/", 1)[1]
campos_path_old     = main_path + "/CamPos" + flight_subgroup + ".txt"
campos_path_new     = main_path + "/CamPos" + flight_subgroup + "_tiff.txt"
marker_path         = main_path + "/Marker" + flight_subgroup + ".xml"
ortho_path_disabled = ortho_folder + "/Ortho_" + flight_subgroup + "_disabled.tif"
ortho_path_average  = ortho_folder + "/Ortho_" + flight_subgroup + "_average.tif"
ortho_path_mosaic   = ortho_folder + "/Ortho_" + flight_subgroup + "_mosaic.tif"

chunk.exportMarkers(marker_path, doc.chunk.crs)

if os.path.exists(ortho_folder):
    pass
else:
    os.mkdir(ortho_folder)

# Save project

doc.read_only = False

photo_list = list()
meta_list = list()
for j in range(len(chunk.cameras)):
    if chunk.cameras[j].center is not None:
        old_path = chunk.cameras[j].photo.path
        new_path = old_path.replace("/DJI_0", "/Grayscale/DJI_0")
        new_path = new_path.replace(".jpg", ".tiff")
        photo_list.append(new_path)
        meta_list.append(chunk.cameras[j].photo.meta)
        camera = chunk.cameras[j]
    else:
        pass





print("***")
print(campos_path_old)
print(campos_path_new)
print(marker_path)
print(ortho_path_disabled)
print(ortho_path_average)
print(ortho_path_mosaic)




doc = Metashape.Document()
doc.save(path=project_path_tif)

chunk = doc.addChunk()

chunk.addPhotos(photo_list, load_reference = True)

for j in range (len(chunk.cameras)):
    chunk.cameras[j].photo.meta = meta_list[j]

chunk.crs = Metashape.CoordinateSystem("EPSG::2056")
chunk.camera_crs = chunk.crs



with open(campos_path_old, 'r') as file:
    data = file.read()
    data = data.replace('.jpg', '.tiff')
with open(campos_path_new, 'w') as file:
    file.write(data)


doc.read_only = False

chunk.importReference(campos_path_new, format=Metashape.ReferenceFormatCSV, items=Metashape.ReferenceItemsCameras, delimiter=",", skip_rows=2, columns="nooooooooooooooxyzabc")

my_sensor = chunk.sensors[0]
my_sensor.type = Metashape.Sensor.Type.Frame
my_calib = Metashape.Calibration()
my_calib.load(list_job_instructions[i].camera_model_path, format=Metashape.CalibrationFormatXML)
my_sensor.user_calib = my_calib
my_sensor.fixed = True

doc.save()




chunk.importMarkers(marker_path)
chunk.importReference(list_job_instructions[i].GCP_path, Metashape.ReferenceFormatCSV, Metashape.ReferenceItemsMarkers, columns='nxyz', delimiter=';', ignore_labels=False, threshold=3, create_markers=False)
chunk.importReference(list_job_instructions[i].GCP_path, Metashape.ReferenceFormatCSV, Metashape.ReferenceItemsMarkers, columns='nxyz', delimiter=';', ignore_labels=True, threshold=3, create_markers=True)


chunk.matchPhotos(downscale=0, generic_preselection=False, reference_preselection=True, keypoint_limit=40000, tiepoint_limit=4000, reset_matches=True, reference_preselection_mode=Metashape.ReferencePreselectionEstimated)
chunk.alignCameras(adaptive_fitting=False)

doc.read_only = False
doc.save()


def progress_print(p):
    print('Current task progress: {:.2f}%'.format(p))





chunk.buildDepthMaps(downscale=1, filter_mode=Metashape.AggressiveFiltering, progress=progress_print)
chunk.buildDenseCloud()

doc.save()

chunk.buildModel(surface_type=Metashape.Arbitrary, interpolation=Metashape.EnabledInterpolation, progress=progress_print)

doc.save()

chunk.buildDem(source_data=Metashape.DenseCloudData, interpolation=Metashape.EnabledInterpolation, progress=progress_print)

doc.save()



compression = Metashape.ImageCompression()
compression.tiff_big = True
compression.tiff_tiled = True
compression.tiff_compression = Metashape.ImageCompression.TiffCompressionNone
compression.tiff_overviews = True


doc.save()

proj = Metashape.OrthoProjection()
proj.crs = chunk.crs

chunk.buildOrthomosaic(surface_data=Metashape.DataSource.ElevationData,blending_mode=Metashape.BlendingMode.DisabledBlending, progress=progress_print, projection = proj)
chunk.exportRaster(path = ortho_path_disabled,
                   raster_transform = Metashape.RasterTransformNone,
                   save_alpha = False, # Saving alpha channel messes up the ortho for unknown reasons
                   image_format = Metashape.ImageFormatTIFF,
                   image_compression = compression,
                   resolution_x = list_job_instructions[i].ortho_pixel_size,
                   resolution_y = list_job_instructions[i].ortho_pixel_size,
                   source_data = Metashape.OrthomosaicData,
                   projection = proj)

chunk.buildOrthomosaic(surface_data=Metashape.DataSource.ElevationData,blending_mode=Metashape.BlendingMode.MosaicBlending, progress=progress_print, projection = proj)
chunk.exportRaster(path = ortho_path_mosaic,
                   raster_transform = Metashape.RasterTransformNone,
                   save_alpha = False, # Saving alpha channel messes up the ortho for unknown reasons
                   image_format = Metashape.ImageFormatTIFF,
                   image_compression = compression,
                   resolution_x = list_job_instructions[i].ortho_pixel_size,
                   resolution_y = list_job_instructions[i].ortho_pixel_size,
                   source_data = Metashape.OrthomosaicData,
                   projection = proj)

chunk.buildOrthomosaic(surface_data=Metashape.DataSource.ElevationData,blending_mode=Metashape.BlendingMode.AverageBlending, progress=progress_print, projection = proj)
chunk.exportRaster(path = ortho_path_average,
                   raster_transform = Metashape.RasterTransformNone,
                   save_alpha = False, # Saving alpha channel messes up the ortho for unknown reasons
                   image_format = Metashape.ImageFormatTIFF,
                   image_compression = compression,
                   resolution_x = list_job_instructions[i].ortho_pixel_size,
                   resolution_y = list_job_instructions[i].ortho_pixel_size,
                   source_data = Metashape.OrthomosaicData,
                   projection = proj)

doc.save()


print("##################################################################################################################################")
print(project_path_tif," finished." )
print("##################################################################################################################################")