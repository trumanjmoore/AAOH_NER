import geopy.point
from geopy.geocoders import Nominatim
import csv
import subprocess
import glob

def geolocate(geo):
    locations_set = set([]) #collection of location names already seen, tries to limit the amount of times the geocoder has to run
    address_set = set([]) #collecetion of lat/lon address already seen, sometimes the same location might go by different names
    lat_long_str = "" #string of all geographical addresses of locations added

    rows = []
    bounding_box = [34, -102, 25, -80]  # bounding box for determining if a location needs user confirmation
    importance_benchmark = .5  # importance level to determine if the location is worth adding

    # reads the locations names that the NER put in the csv file
    with (open(".\\Output\\location_output.csv", 'r') as csvfile):
        csvreader = csv.reader(csvfile)

        for row in csvreader:
            rows.append(row)

        for row in rows:
            for col in row:
                location = "%10s" % col
                if location not in locations_set:
                    locations_set.add(location)
                    try:
                        address = geo.geocode(query=location,
                                              exactly_one=False,
                                              limit=5,
                                              addressdetails=True,
                                              country_codes='US',
                                              featuretype='settlement')  # gets location address information
                    except:
                        print("Couldn't find address for: " + location)

                    if address is not None and address[0].raw['addresstype'] != "state":  # leaves out states
                        if str(address[0].raw['lat']) + '/' + str(address[0].raw['lon']) not in address_set:  # checks if this address has already been seen
                            address_set.add(str(address[0].raw['lat']) + '/' + str(address[0].raw['lon']))  # if not add the address
                            if float(address[0].raw['importance']) >= importance_benchmark:  # checks importance level against benchmark
                                if check_bounds(bounding_box, float(address[0].raw['lat']), float(address[0].raw['lon'])):  # check if the location is in the gulf south
                                    lat_long_str = add_location(str(address[0].raw['lat']), str(address[0].raw['lon']), lat_long_str)  # if so, then add the location automatically
                                    print("\nLocation Found: " + address[0].raw['display_name'])

                                else:  # if location is not in gulf south, look for user confirmation
                                    print("\nFor " + location + ", which location is best?")
                                    print(str(0) + ": " + "Do not include location")
                                    for i in range(len(address)):
                                        print(str(i + 1) + ": " + address[i].raw['display_name'] + ", " +
                                              str(address[i].raw['importance']) + ", " + address[i].raw['lat'] + '/' + address[i].raw['lon'])

                                    while True: #asks for user input
                                        try:
                                            confirmation = int(input("Please choose an option: "))
                                            if confirmation < 0 or confirmation > len(address):
                                                raise ValueError
                                            else:
                                                if confirmation != str(0):
                                                    lat_long_str = add_location(str(address[int(confirmation) - 1].raw['lat']),
                                                                 str(address[int(confirmation) - 1].raw['lat']), lat_long_str)  # adds the location the user chose
                                                break

                                        except ValueError:
                                            print("Please choose a valid option")

    print("\nLocations Added! Please check the output file")
    lat_long_str = lat_long_str[:-1]
    values_dict = {'Latitude/Longitude': lat_long_str}  # location string added to the dict that defines the csv output
    return values_dict


def check_bounds(bounds, lat, lon):
    # checks if the location is within a given bounding box
    if bounds[0] > lat > bounds[2]:
        if lon < 0:
            if bounds[1] < lon < bounds[3]:
                return True
    else:
        return False


def add_location(address_lat, address_lon, latlong_str):
    # adds locations to the lat long string
    latlong_str += address_lat + '/' + address_lon
    latlong_str += ";"
    return latlong_str


def get_item_values(values_dict):
    # reads the interview transcript to fill the item values for csv import
    filelist = glob.glob(".\\Input\\*.txt")
    for file in filelist:
        reading = open(file, 'r')
        while True:
            content = reading.readline()
            if content.strip():
                if content.split()[0] == "AAHP":
                    values_dict['Title'] = content.strip()
                elif content.split()[0] == "Interview":
                    values_dict['interviewer'] = content.strip()
                elif content.split()[0] == "Abstract:":
                    values_dict['Description'] = content.strip()
                elif content.split()[0] == "Keywords:":
                    values_dict['Keywords'] = content.strip()
                elif content.split()[0] == "For":
                    break
    return values_dict


def write_to_file(values_dict):
    # writes the dict values to the csv for csv import to read, and assign item values
    fields = ["Title", "Description", "Keywords", "interviewer", "Latitude/Longitude"]

    with open(".\\Output\\location_output.csv", 'w', newline='') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fields)
        writer.writeheader()
        writer.writerow(values_dict)


if __name__ == '__main__':
    # runs the NER
    subprocess.call(['java', '-jar', 'stanford-ner.jar'])

    #API Key for Nominatim
    geolocator = Nominatim(user_agent="AAHP")

    # get location addresses
    value_dict = geolocate(geolocator)

    # gets item values
    value_dict = get_item_values(value_dict)

    # writes output to the csv file
    write_to_file(value_dict)
