# Generate dense cloud and DEM


# Load the project
doc = Metashape.Document()
doc.open(path = project_path)
doc.read_only = False
chunk = doc.chunk
doc.save()


def progress_print(p):
    print('Current task progress: {:.2f}%'.format(p))

chunk.buildDepthMaps(downscale=1, filter_mode=Metashape.AggressiveFiltering, progress=progress_print)
chunk.buildDenseCloud()
doc.save()
chunk.buildModel(surface_type=Metashape.Arbitrary, interpolation=Metashape.EnabledInterpolation, progress=progress_print)
doc.save()

#
chunk.buildDem(source_data=Metashape.DenseCloudData, interpolation=Metashape.EnabledInterpolation, progress=progress_print)
doc.save()

chunk.buildOrthomosaic(surface_data=Metashape.DataSource.ElevationData,blending_mode=Metashape.BlendingMode.DisabledBlending, progress=progress_print)

doc.save()

compression = Metashape.ImageCompression()
compression.tiff_big = True
compression.tiff_tiled = True
compression.tiff_compression = Metashape.ImageCompression.TiffCompressionNone
compression.tiff_overviews = True


if list_job_instructions[i].ortho_path == "NA":
    pass
else:
    chunk.exportRaster(path = list_job_instructions[i].ortho_path,
                       raster_transform = Metashape.RasterTransformNone,
                       save_alpha = False, # Saving alpha channel messes up the ortho for unknown reasons
                       image_format = Metashape.ImageFormatTIFF,
                       image_compression = compression,
                       resolution_x = list_job_instructions[i].ortho_pixel_size,
                       resolution_y = list_job_instructions[i].ortho_pixel_size,
                       source_data = Metashape.OrthomosaicData)

doc.save()

