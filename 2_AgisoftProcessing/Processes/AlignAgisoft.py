# Aligning
# Check if project already exists

print(project_path)

if os.path.isfile(project_path):
    question_string = "!!!!!!!!!!!!!!!!!!!!!!!!!!!\nProject\n" + project_path + " exists! \nWant to replace it ?\n!!!!!!!!!!!!!!!!!!!!!!!!!!!\n"
    if FunctionsAgisoft.yes_or_no(question_string):
        pass
    else:
        print("Process stopped!!!")
        print("Change path in 'processing_plan.csv' to save project !")
        sys.exit()

# Save project
doc = Metashape.Document()
doc.save(path=project_path)

chunk = doc.addChunk()

# Import images
image_list = list()
for (dirpath, dirnames, filenames) in os.walk(os.path.join(directory_path, images_path)):
    image_list += [os.path.join(dirpath, file) for file in filenames]

photo_list = list()
for photo in image_list:
    # if photo.rsplit(".", 1)[1].lower() in ["jpg", "jpeg", "tif", "tiff"]:
    if photo.rsplit(".", 1)[1].lower() in ["jpg", "jpeg"]:
        photo_list.append(photo)

chunk.addPhotos(photo_list)

doc.read_only = False
doc.save()

# Check, if camera model is available and if so, load camera model
if list_job_instructions[i].camera_model_path == "NA":
    pass
else:
    my_sensor = chunk.sensors[0]
    my_sensor.type = Metashape.Sensor.Type.Frame
    my_calib = Metashape.Calibration()
    my_calib.load(os.path.join(directory_path, list_job_instructions[i].camera_model_path) , format=Metashape.CalibrationFormatXML)
    my_sensor.user_calib = my_calib
    my_sensor.fixed = True

# Align cameras
chunk.matchPhotos(downscale=0, generic_preselection=True, reference_preselection=False, keypoint_limit=40000,
                  tiepoint_limit=4000, reset_matches=True,
                  reference_preselection_mode=Metashape.ReferencePreselectionSequential)
chunk.alignCameras(adaptive_fitting=False)

doc.save()

# Check, if camera distance filtering is to be applied. If so, apply camera distance filtering.
# (If two cameras are to close, one of them is deleted.)

if list_job_instructions[i].use_distance_filtering == "FALSE":
    pass
elif list_job_instructions[i].use_distance_filtering == "TRUE":
    print("!!!! TRUE")
    cameras_selected = list()

    chunk.crs = Metashape.CoordinateSystem("EPSG::4326")
    chunk.camera_crs = Metashape.CoordinateSystem("EPSG::4326")
    marker_crs = Metashape.CoordinateSystem("EPSG::4326")

    X = float(0.55)  # 0.55
    scale = chunk.transform.scale

    for camera in chunk.cameras:
        if camera.transform:
            cameras_selected.append(camera)

    print("X: ", X)
    for j in range(2, len(cameras_selected), 1):
        distance = (cameras_selected[j].center - cameras_selected[j - 1].center).norm() * scale
        print("Distance between cameras: ", distance)
        if distance < X:
            cameras_selected[j].enabled = False
        j += 1

doc.save()

EPSG_code = "EPSG::" + list_job_instructions[i].EPSG

out_crs = Metashape.CoordinateSystem(EPSG_code)  # user-defined crs
for camera in chunk.cameras:
    if camera.reference.location:
        camera.reference.location = Metashape.CoordinateSystem.transform(camera.reference.location, chunk.crs,
                                                                         out_crs)
for marker in chunk.markers:
    if marker.reference.location:
        marker.reference.location = Metashape.CoordinateSystem.transform(marker.reference.location, chunk.crs,
                                                                         out_crs)

chunk.crs = out_crs
chunk.camera_crs = out_crs
chunk.marker_crs = out_crs

chunk.updateTransform()

doc.save()

# Detect Markers

if list_job_instructions[i].GCP_path == "NA":
    pass
else:
    chunk.detectMarkers(Metashape.TargetType.CrossTarget, tolerance=73, maximum_residual=10)

    for marker in chunk.markers:
        if len(marker.projections) < 7:
            for camera in list(marker.projections.keys()):
                marker.projections[camera] = None

    chunk.importReference(os.path.join(directory_path, list_job_instructions[i].GCP_path), Metashape.ReferenceFormatCSV,
                          Metashape.ReferenceItemsMarkers, columns='noxyz', delimiter=';', ignore_labels=False,
                          skip_rows=2,
                          threshold=3, create_markers=False)
    chunk.importReference(os.path.join(directory_path, list_job_instructions[i].GCP_path), Metashape.ReferenceFormatCSV,
                          Metashape.ReferenceItemsMarkers, columns='noxyz', delimiter=';', ignore_labels=True,
                          skip_rows=2,
                          threshold=3, create_markers=True)
    chunk.updateTransform()


doc.save()
