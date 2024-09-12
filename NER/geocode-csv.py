import geopy.point
from geopy.geocoders import Nominatim
import csv
import subprocess
import glob

def geolocate(geo):
    locations_set = set([])
    address_set = set([])
    lat_long_str = ""

    rows = []
    bounding_box = [34, -102, 25, -80]

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
                                              featuretype='settlement')
                    except:
                        print("Couldn't find address for: " + location)

                    if address is not None and address[0].raw['addresstype'] != "state":
                        if str(address[0].raw['lat']) + '/' + str(address[0].raw['lon']) not in address_set:
                            address_set.add(str(address[0].raw['lat']) + '/' + str(address[0].raw['lon']))
                            if check_bounds(bounding_box, float(address[0].raw['lat']), float(address[0].raw['lon'])):
                                lat_long_str += str(address[0].raw['lat']) + '/' + str(address[0].raw['lon'])
                                lat_long_str += ";"
                                print("\nLocation Found: " + address[0].raw['display_name'])
                            else:
                                print("\nFor " + location + ", which location is best?")
                                print(str(0) + ": " + "Do not include location")
                                for i in range(len(address)):
                                    print(address[i].raw)
                                    print(str(i + 1) + ": " + address[i].raw['importance'] + ", " + address[i].raw['display_name'] + ", " + address[i].raw['lat'] + '/' + address[i].raw['lon'])
                                confirmation = input("Please choose an option: ")
                                if confirmation != str(0):
                                    lat_long_str += str(address[int(confirmation) - 1].raw['lat']) + '/' + str(address[int(confirmation) - 1].raw['lon'])
                                    lat_long_str += ";"

    print("\nLocations Added! Please check the output file")
    lat_long_str = lat_long_str[:-1]
    values_dict = {'Latitude/Longitude': lat_long_str}
    return values_dict


def check_bounds(bounds, lat, lon):
    if bounds[0] > lat > bounds[2]:
        if lon < 0:
            if bounds[1] < lon < bounds[3]:
                return True
    else:
        return False


def get_item_values(values_dict):
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
    fields = ["Title", "Description", "Keywords", "interviewer", "Latitude/Longitude"]

    with open(".\\Output\\location_output.csv", 'w', newline='') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fields)
        writer.writeheader()
        writer.writerow(values_dict)


if __name__ == '__main__':
    subprocess.call(['java', '-jar', 'stanford-ner.jar'])

    geolocator = Nominatim(user_agent="AAHP")

    value_dict = geolocate(geolocator)

    value_dict = get_item_values(value_dict)

    write_to_file(value_dict)
