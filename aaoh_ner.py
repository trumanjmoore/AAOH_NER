import tkinter
from tkinter import Frame
from tkinter import Text
from tkinter import Entry
from tkinter import WORD
from tkinter import INSERT
from tkinter import END
from tkinter import StringVar
from tkinter import Button
from tkinter import Label
from threading import Thread
import glob
from geopy.geocoders import Nominatim
import csv
import subprocess


class Window:
    # create confirmation window
    def __init__(self, key):
        self.window = tkinter.Tk()
        self.window.title('AAOH')
        self.window.lift()
        self.window.attributes('-topmost', True)
        self.window.after_idle(self.window.attributes, '-topmost', False)

        # used for the search function
        self.matches = 0
        self.counter = 1
        self.found_words = []

        screen_width = self.window.winfo_screenwidth()
        screen_height = self.window.winfo_screenheight()
        self.window.geometry(f"{int(screen_width * .75)}x{int(screen_height * .75)}+{0}+{0}")
        self.window.resizable(False, False)

        # left frame holds transcript, right frame has confirmation screen
        main_frame = Frame(self.window)
        main_frame.grid(column=0, row=0, sticky="nswe")

        right_frame = Frame(main_frame)
        right_frame.grid(column=1, row=0, sticky="nswe")

        left_frame = Frame(main_frame)
        left_frame.grid(column=0, row=0, sticky="nswe")

        left_frame_top = Frame(left_frame)
        left_frame_top.grid(column=0, row=0, sticky="nswe")

        left_frame_bot = Frame(left_frame)
        left_frame_bot.grid(column=0, row=1, sticky="nswe")

        # for searching through the transcript
        search_button = Button(left_frame_top, height=1, width=10, text="Search", command=self.find_text)
        search_button.grid(row=0, column=0)

        self.search_field = Entry(left_frame_top)
        self.search_field.grid(row=0, column=1, sticky="nswe")

        next_button = Button(left_frame_top, height=1, width=5, text="Next", command=self.find_next)
        next_button.grid(row=0, column=2)

        prev_button = Button(left_frame_top, height=1, width=5, text="Prev", command=self.find_prev)
        prev_button.grid(row=0, column=3)

        self.matches_label = Label(left_frame_top)
        self.matches_label.grid(row=0, column=4)

        # interview transcript
        self.interview_text = Text(left_frame_bot, wrap=WORD, width=int(screen_width / 20), height=int(screen_height / 22))
        filelist = glob.glob("Input\\*.txt")
        for file in filelist:
            with open(file, 'r', encoding='utf-8') as f:
                self.interview_text.insert(INSERT, f.read())
        self.interview_text.grid(row=0, column=0, sticky="nswe")

        # confirmation request
        output_text = Text(right_frame, width=int(screen_width / 23), height=int(screen_height / 27))
        output_text.grid(row=0, column=0)

        # user confirmation
        input_text = Text(right_frame, width=int(screen_width / 23), height=int(screen_height / 135),
                          background="light blue")
        input_text.grid(row=1, column=0)

        i = 0
        self.button_pressed = StringVar()
        confirm_button = Button(right_frame, height=2, width=20, text="Confirm",
                                command=lambda: self.button_pressed.set(str(++i)))
        confirm_button.grid(row=2, column=0, sticky="nswe")

        self.window.bind('<Return>', self.take_input(i))

        # get location addresses, thread so the user can still interact with the transcript frame
        t1 = Thread(target=geolocate, daemon=True,
                    args=(key, output_text, input_text, confirm_button, self.button_pressed))
        t1.start()

    def run_mainloop(self):
        # run the windows mainloop
        self.window.protocol("WM_DELETE_WINDOW", self.on_closing)
        self.window.mainloop()

    def take_input(self, i):
        self.button_pressed.set(str(++i))

    def on_closing(self):
        # stops the user input field from looking for input
        self.button_pressed.set(str(-1))
        self.window.destroy()

    def find_text(self):
        # when user searches through the transcript
        text = self.search_field.get()
        start = '1.0'
        self.matches = 0
        self.counter = 1
        if text:
            self.clear_tags()
            while 1:
                start = self.interview_text.search(text, start, regexp=True, nocase=True, stopindex=END)
                if not start: break
                last = '%s+%dc' % (start, len(text))
                self.interview_text.tag_add('found', start, last)
                self.found_words.append((start, last))
                self.matches += 1
                start = last
                self.interview_text.tag_config('found', background='light blue')
                self.interview_text.tag_config('next', background='dodger blue')
        if self.matches == 0:
            self.matches_label.config(text="No matches found")
        else:
            self.matches_label.config(text=f"1 of {str(self.matches)}")
            self.interview_text.tag_remove('found', self.found_words[0][0], self.found_words[0][1])
            self.interview_text.tag_add('next', self.found_words[0][0], self.found_words[0][1])
            self.interview_text.see(self.found_words[0][0])

    def find_next(self):
        if self.matches != 0:
            self.add_found_tags()
            if self.counter == len(self.found_words):
                self.counter = 1
            else:
                self.counter += 1
            self.add_next_tags()
            self.matches_label.config(text=f"{self.counter} of {str(self.matches)}")
            self.interview_text.see(self.found_words[self.counter - 1][0])

    def find_prev(self):
        if self.matches != 0:
            self.add_found_tags()
            if self.counter == 1:
                self.counter = len(self.found_words)
            else:
                self.counter -= 1
            self.add_next_tags()
            self.matches_label.config(text=f"{self.counter} of {str(self.matches)}")
            self.interview_text.see(self.found_words[self.counter - 1][0])

    def add_found_tags(self):
        self.interview_text.tag_remove('next', self.found_words[self.counter - 1][0],
                                       self.found_words[self.counter - 1][1])
        self.interview_text.tag_add('found', self.found_words[self.counter - 1][0],
                                    self.found_words[self.counter - 1][1])

    def add_next_tags(self):
        self.interview_text.tag_remove('found', self.found_words[self.counter - 1][0],
                                       self.found_words[self.counter - 1][1])
        self.interview_text.tag_add('next', self.found_words[self.counter - 1][0],
                                    self.found_words[self.counter - 1][1])

    def clear_tags(self):
        for tag in self.found_words:
            self.interview_text.tag_remove("found", tag[0], tag[1])
            self.interview_text.tag_remove("next", tag[0], tag[1])
        self.found_words.clear()


def geolocate(geo, output, input_text, confirm_button, button_pressed):
    locations_set = set([])  # collection of location names already seen, tries to limit the amount of times the geocoder has to run
    address_set = set([])  # collecetion of lat/lon address already seen, sometimes the same location might go by different names
    lat_long_str = ""  # string of all geographical addresses of locations added

    bounding_box = [34, -102, 25, -80]  # bounding box for determining if a location needs user confirmation
    importance_benchmark = .5  # importance level to determine if the location is worth adding

    rows = get_locations()

    gainesville = False

    for row in rows:
        for col in row:
            if ("%10s" % col).strip() not in locations_set:
                location = ("%10s" % col).strip()
                if location == "Gainesville" and not gainesville:
                    gainesville = True
                    continue
                locations_set.add(location)
            else:
                continue

            try:
                address = geo.geocode(query=location, exactly_one=False, limit=5, addressdetails=True,
                                      country_codes='US', featuretype='settlement')  # gets location address information
            except:
                output.insert(END, "Couldn't find address for: " + location + "\n")
                continue

            if address is None:
                continue
            if address[0].raw['addresstype'] == "state":
                continue  # leaves out states
            if str(address[0].raw['lat']) + '/' + str(address[0].raw['lon']) in address_set:
                continue  # checks if this address has already been seen, if not add the address
            address_set.add(str(address[0].raw['lat']) + '/' + str(address[0].raw['lon']))
            if float(address[0].raw['importance']) < importance_benchmark:
                continue  # checks importance level against benchmark

            if check_bounds(bounding_box, float(address[0].raw['lat']),float(address[0].raw['lon'])):  #  if the location is in the gulf south no user confirmation necessary
                lat_long_str = add_location(str(address[0].raw['lat']), str(address[0].raw['lon']), lat_long_str)  # if so, then add the location automatically
                output.insert(END, "\nLocation Found: " + address[0].raw['display_name'] + "\n")
                output.see("end")
                continue

            # if location is not in gulf south, look for user confirmation
            output.insert(END, "\nFor " + location + ", which location is best?" + "\n")
            output.insert(END, str(0) + ": " + "Do not include location" + "\n")
            for i in range(len(address)):
                output.insert(END, str(i + 1) + ": " + address[i].raw['display_name'] + "\n")
            output.insert(END, "Please choose an option: " + "\n")
            output.see("end")

            while True:  #asks for user input
                confirm_button.wait_variable(button_pressed)
                if button_pressed.get() == "-1":
                    exit()
                confirmation = input_text.get("1.0", END)
                input_text.delete('1.0', END)
                if confirmation == "":
                    continue
                try:
                    confirmation = int(confirmation)
                    if confirmation < 0 or confirmation > len(address):
                        raise ValueError
                    if confirmation == 0:
                        output.insert(END, "Location ignored" + "\n")
                    else:
                        output.insert(END, f"Location {confirmation} added" + "\n")
                        lat_long_str = add_location(str(address[confirmation - 1].raw['lat']),
                                                    str(address[confirmation - 1].raw['lon']),
                                                    lat_long_str)  # adds the location the user chose
                    break

                except ValueError:
                    output.insert(END, "Please choose a valid option" + "\n")

                output.see("end")

    output.insert(END, "\nLocations Added! Please check the output file")
    output.see("end")
    lat_long_str = lat_long_str[:-1]
    values_dict = {'Latitude/Longitude': lat_long_str}  # location string added to the dict that defines the csv output
    # gets item description values for omeka
    get_item_values(values_dict)


def get_locations():
    rows = []
    # reads the locations names that the NER put in the csv file
    with (open("Output/location_output.csv", 'r') as csvfile):
        csvreader = csv.reader(csvfile)
        for row in csvreader:
            rows.append(row)
    return rows


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
    title = False
    filelist = glob.glob("Input\\*.txt")
    for file in filelist:
        reading = open(file, 'r', encoding='utf-8')
        while True:
            content = reading.readline()
            if not content.strip():
                continue
            match content.split()[0].strip():
                case "AAHP":
                    if not title:
                        values_dict['Title'] = content.strip("African American History Project" "()" "\n")
                        title = True
                case "MFP":
                    if not title:
                        values_dict['Title'] = content.strip()
                        title = True
                case "Abstract:":
                    abstract = ""
                    while True:
                        print(content.strip())
                        if not content.strip():
                            content = reading.readline()
                            continue
                        if content.split()[0].strip("[") == "Keywords:":
                            keywords = ""
                            for word in content.strip("Keywords:").replace(',', ';').split(";"):
                                keywords += word.strip("[ ]\n")
                                keywords += ";"
                            keywords = keywords.strip(";")
                            values_dict['Table of Contents'] = keywords.strip()
                            break
                        elif content.split()[0].strip("[") == "Keywords":
                            keywords = ""
                            for word in content.strip("Keywords").replace(',', ';').split(";"):
                                keywords += word.strip("[ ]\n")
                                keywords += ";"
                            keywords = keywords.strip(";")
                            values_dict['Table of Contents'] = keywords.strip()
                            break
                        abstract += content.strip("Abstract: \n")
                        content = reading.readline()
                    values_dict['Description'] = abstract
                case "Interviewee:":
                    interviewer = ""
                    date = ""
                    for word in content.split(":"):
                        if word.strip()[-4:] == "Date":
                            interviewer = word.strip("Date")
                        date = word.strip("\n")
                    values_dict['interviewer'] = interviewer
                    values_dict['Date'] = date
                    break
                case "Interviewer:":
                    interviewer = ""
                    date = ""
                    for word in content.split(":"):
                        if word.strip()[-11:] == "Interviewee":
                            interviewer = word.strip("Interviewee")
                        date = word.strip("\n")
                    values_dict['interviewer'] = interviewer
                    values_dict['Date'] = date
                    break
        # writes output to the csv file
        write_to_file(values_dict)


def write_to_file(values_dict):
    # writes the dict values to the csv for csv import to read, and assign item values
    fields = ["Title", "Description", "Table of Contents", "interviewer", "Date", "Latitude/Longitude"]

    with open("Output/location_output.csv", 'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fields)
        writer.writeheader()
        writer.writerow(values_dict)


if __name__ == '__main__':
    # runs the NER
    subprocess.call(['javaw', '-jar', 'stanford_ner//stanford-ner.jar'])

    # Enter into Nominatim
    geolocator = Nominatim(user_agent="AAHP")

    # create the confirmation window
    main_window = Window(geolocator)
    main_window.run_mainloop()
