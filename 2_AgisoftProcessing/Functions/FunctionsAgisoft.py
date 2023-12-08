#
def yes_or_no(question):
    answer = input(question + "(y/n): ").lower().strip()
    print("")
    while not (answer == "y" or answer == "yes" or \
               answer == "n" or answer == "no"):
        print("Input yes or no")
        answer = input(question + "(y/n):").lower().strip()
        print("")
    if answer[0] == "y":
        return True
    else:
        return False


# Create class that contains all informations on the mission based on AgisoftProcessingPlan.csv
class job_instruction():
    def __init__(self, main_path, images_path, camera_model_path, GCP_path,
                 use_distance_filtering, second_alignement_after_distance_filtering,
                 country, postal_code_field, parcel, date, flight_height, colour_space_option,
                 operation, EPSG, ortho_pixel_size, ortho_path, activated):
        self.name = country + '_' + postal_code_field + '_' + parcel + '_' + date + '_' + flight_height + 'm_' + colour_space_option
        self.main_path = main_path
        self.images_path = images_path
        self.camera_model_path = camera_model_path
        self.GCP_path = GCP_path
        self.use_distance_filtering = use_distance_filtering
        self.second_alignement_after_distance_filtering = second_alignement_after_distance_filtering
        self.country = country
        self.postal_code_field = postal_code_field
        self.parcel = parcel
        self.date = date
        self.flight_height = flight_height
        self.colour_space_option = colour_space_option
        self.operation = operation
        self.EPSG = EPSG
        self.ortho_path = ortho_path
        self.ortho_pixel_size = ortho_pixel_size
        self.activated = activated
