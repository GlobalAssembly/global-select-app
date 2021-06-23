# Global selection code....the second attempt - using admin centroids
#
# April 2020 by Brett Hennig and ....
#

import csv, random, math

# Settings/input

# must download data and put it here of course...
global_pop_admin_centroids_file_root = "/home/developer/projects/global-select-app/docs/"
global_pop_output_file_root = "/home/developer/projects/global-select-app/docs/"
global_pop_admin_centroids_files = [
		"gpw_v4_admin_unit_center_points_population_estimates_rev11_usa_midwest.csv",
		"gpw_v4_admin_unit_center_points_population_estimates_rev11_usa_northeast.csv",
		"gpw_v4_admin_unit_center_points_population_estimates_rev11_usa_south.csv",
		"gpw_v4_admin_unit_center_points_population_estimates_rev11_usa_west.csv",
		"gpw_v4_admin_unit_center_points_population_estimates_rev11_global.csv"
		]
un_region_country_count_file = global_pop_output_file_root + "country-code-UN-Region-max.csv"

# TESTing area (oceania):
#global_pop_admin_centroids_file_root = "/Users/bsh/brett/sortition/foundation/projects-events/Stratification-Services/Global CA/data-points/GPWv4/gpw-v4-admin-unit-center-points-population-estimates-rev11_oceania_csv/"
#global_pop_admin_centroids_files = ["gpw_v4_admin_unit_center_points_population_estimates_rev11_oceania.csv"]
#total_pop = 42131508
# Testing non-US only
#total_pop = 7424623670
total_pop = 7758177449
num_points = 100
debug_print = False


# output file:
google_out_file_name = global_pop_output_file_root + "global-assembly-points.csv"

# Read in the database from
#
# https://sedac.ciesin.columbia.edu/data/set/gpw-v4-admin-unit-center-points-population-estimates-rev11
#
# or could use pop density
# or could use: https://ghsl.jrc.ec.europa.eu/ghs_pop2019.php (but this is based on GPWv4)

# this just counts the total pop - did this once then put in line above

'''
total_pop = 0
iso_country_dict = {} #set()
for file_name in global_pop_admin_centroids_files:
	print("Reading in: " + file_name)
	file_handle = open(global_pop_admin_centroids_file_root + file_name, 'r')
	file_reader = csv.DictReader(file_handle)
	for row in file_reader:
		pop_row = int(row[ "UN_2020_E" ])
		pop_iso = row["ISOALPHA"]
		total_pop += pop_row
		if pop_iso in iso_country_dict:
			iso_country_dict[pop_iso] += pop_row
		else:
			iso_country_dict[pop_iso] = pop_row
	file_handle.close()
out_file_google = open(google_out_file_name, "w")
for k, val in iso_country_dict.items():
	out_file_google.write( k + ',' + str(val) + '\n' )
out_file_google.close()
print("Total (file) pop = {}".format(total_pop))
'''


# from https://en.wikipedia.org/wiki/United_Nations_Regional_Groups
class un_region():
	def __init__(self, region_name ):
		self.region_name = region_name
		self.region_pop_percent = 0.0 # actually num_points fraction / 100
		self.region_count = 0
		self.countries = {}
		
	def add_country_to_region(self, country_code, parent_country_code, country_pc):
		if country_code in self.countries:
			print("ERROR: Two rows with same country code: {}".format(country_code))
		if parent_country_code != country_code:
			# need to add percent to parent...
			self.countries[ parent_country_code ][ "country_pc" ] += country_pc
		self.countries[ country_code ] = { "parent_country_code" : parent_country_code, "country_pc" : country_pc, "country_people" : [] }
		self.region_pop_percent += country_pc
	
	def add_person_to_region(self, person):
		self.region_count += 1
		# check if this "country" has a parent, if so make the country be the parent
		parent_country = self.countries[ person["country_iso"] ]["parent_country_code"]
		if person["country_iso"] != parent_country:
			if debug_print:
				print("Found parent country of {} and set to {}.".format(person["country_iso"], parent_country))
			person["country_iso"] = parent_country
		self.countries[ person["country_iso"] ][ "country_people" ].append( person )
		
	def write_country_summary(self, out_file_google):
		for country_key, country_vals in self.countries.items():
			country_count = len(country_vals[ "country_people" ])
			country_max = math.ceil(country_vals["country_pc"])
			if country_count != 0:
				out_file_google.write( country_key + "," + str(country_max) + "," + str(country_count) + "\n" )
		max_region_count = math.ceil(self.region_pop_percent)
		return self.region_name + "," + str(max_region_count) + "," + str(self.region_count) + "\n"
		
	def write_people(self):
		people_array = []
		for country_vals in self.countries.values():
			for person in country_vals["country_people"]:
				people_array.append( ",".join(str(x) for x in person.values()) + "\n" )
		return people_array
		
	def delete_above_max(self):
		# first check country maxs
		num_deleted = 0
		for country_key, country_vals in self.countries.items():
			country_count = len(country_vals[ "country_people" ])
			country_max = math.ceil(country_vals["country_pc"])
			if country_count > country_max:
				#print(country_count)
				num_to_delete = country_count - country_max
				if debug_print:
					print("Country {} above max, delete {}".format(country_key, num_to_delete))
				# delete num_to_delete
				# chose who to delete
				to_delete = set(random.sample(range(country_count), num_to_delete))
				# delete them
				country_vals[ "country_people" ] = [x for i,x in enumerate(country_vals[ "country_people" ]) if not i in to_delete]
				num_deleted += num_to_delete
				self.region_count -= num_to_delete
		max_region_count = math.ceil(self.region_pop_percent)
		if self.region_count > max_region_count:
			num_to_delete = self.region_count - max_region_count
			if debug_print:
				print("Region {} above max, delete {}".format(self.region_name, num_to_delete))
			# delete num_to_delete
			to_delete = set(random.sample(range(self.region_count), num_to_delete))
			for country_key, country_vals in self.countries.items():
				orig_len = len(country_vals[ "country_people" ])
				country_vals[ "country_people" ] = [x for i,x in enumerate(country_vals[ "country_people" ]) if not i in to_delete]
				# if the numbers to delete were 2, 7, 11 and the first country had 3 people then we delete person 2,
				# then shift the numbers down 3 to: -1, 4, 8 and look in the next country etc
				to_delete = [x - orig_len for x in to_delete]
			num_deleted += num_to_delete
			self.region_count -= num_to_delete
		return num_deleted
	
	def replacement( self, person ):
		max_region_count = math.ceil(self.region_pop_percent)
		if self.region_count < max_region_count:
			country_code = self.countries[ person["country_iso"] ][ "parent_country_code" ]
			if country_code != person["country_iso"]: # there is a parent country
				person["country_iso"] = country_code
			country = self.countries[ country_code ]
			country_max = math.ceil(country[ "country_pc" ])
			if len(country[ "country_people" ]) < country_max:
				country[ "country_people" ].append(person)
				self.region_count += 1
				return 1
			else:
				#print("failed to replace in {} as {} of {}".format(person["country_iso"], len(country[ "country_people" ]), country[ "country_max" ]))
				return 0
		else:
			#print("failed to replace in {} as {} of {}".format(self.region_name, self.region_count, self.max_region_count))
			return 0

	def get_person(self, x):
		total_country_count = 0
		for country_key, country_vals in self.countries.items():
			country_count = len(country_vals[ "country_people" ])
			if x >= total_country_count and x < total_country_count + country_count:
				return country_vals[ "country_people" ][x - total_country_count]
			total_country_count += country_count
		print("Error - got to country list end {}".format(x))
		
		
class ca_people():
	name_fields = ["NAME1", "NAME2", "NAME3", "NAME4", "NAME5", "NAME6"]
	total_pop = 0

	def __init__(self, total_pop, num_points, print_info):
		ca_people.total_pop = total_pop
		self.num_points = num_points
		self.print_info = print_info
		self.regions = {
			"Africa Group" : un_region("Africa Group" ),
			"Asia and the Pacific Group" : un_region("Asia and the Pacific Group" ),
			"Eastern European Group" : un_region("Eastern European Group" ),
			"Latin American and Caribbean Group" : un_region("Latin American and Caribbean Group" ),
			"Western European and Others Group" : un_region("Western European and Others Group" )  }
		if print_info:
			print("Total population in database = {}".format(ca_people.total_pop))
		# read in region and country count
		un_region_file_handle = open(un_region_country_count_file, 'r')
		un_region_file_reader = csv.DictReader(un_region_file_handle)
		self.country_region = {}
		for row in un_region_file_reader:
			#country_max = math.ceil(float(row["country_pop_percent"]))
			country_percent = float(row["country_pop_percent"])
			#if country_max == 0: #check if rounding errors have crept in
			#	country_max = 1
			self.regions[ row["un_region"] ].add_country_to_region( row["country_code"], row["parent_country_code"], num_points*country_percent/100.0 )
			self.country_region[row["country_code"]] = row["un_region"]

		# Select num_points points - population/density weighted?
		self.selected_nums = []
		# grab same number of backups as well - could be the same!
		for i in range(self.num_points):
			self.selected_nums.append(random.randint(1, ca_people.total_pop))

		if print_info:
			print("Randomly selected {} numbers from total population.".format(len(self.selected_nums)))
		self.selected_nums.sort()		
		self.count_selected_people = 0


	def grab_people_in_admin_area(self, pop_count, row):
		pop_row = int(row[ "UN_2020_E" ])
		while self.count_selected_people < self.num_points and self.selected_nums[self.count_selected_people] > pop_count and self.selected_nums[self.count_selected_people] <= pop_count + pop_row:
			#found a person we want!
			#print(selected_list_count, people_nums[selected_list_count], total_pop, total_pop + pop_row)
			place_name = ''
			for nm in ca_people.name_fields:
				if row[ nm ] != "NA":
					if place_name != '':
						place_name += ' -- '
					place_name += row[nm].strip()
			place_country = row["COUNTRYNM"].strip()
			place_country_iso = row["ISOALPHA"]
			if self.print_info:
				print("                                           ", end="\r")
				print("Found point {} in {}".format(self.count_selected_people + 1, place_country))
			# throw a random offset into location based on its size, approximate as circle!
			orig_radius = math.sqrt(float(row["TOTAL_A_KM"])/math.pi)
			rand_radius_km = random.random()*orig_radius
			# see: http://www.edwilliams.org/avform147.htm#LL
			# for what is going on here - but basically just displacing the point
			# a little bit, depending on the size of the admin area
			# rand_radius_radians (distance units in formula are weird, 1 Nautical mile = 1852 m)
			rrr = (math.pi/(180*60))*1000*rand_radius_km/1852.0
			tc = random.random()*2*math.pi
			lat1 = math.radians(float(row["CENTROID_Y"]))
			lon1 = math.radians(float(row["CENTROID_X"]))
			lat2 = math.asin(math.sin(lat1)*math.cos(rrr)+math.cos(lat1)*math.sin(rrr)*math.cos(tc))
			lon2 = (lon1-math.asin(math.sin(tc)*math.sin(rrr)/math.cos(lat2))+math.pi)%(2*math.pi) - math.pi
			rand_lat_deg = math.degrees(lat2)
			rand_lon_deg = math.degrees(lon2)
			# add to counts for country and region
			if place_country_iso in self.country_region.keys():
				person_region = self.country_region[place_country_iso]
			else:
				if debug_print:
					print("Error {} not in country-region map. ADDED TO 'Asia and the Pacific Group'".format(place_country_iso))
				person_region = "Asia and the Pacific Group"
				self.regions[ person_region ].add_country_to_region( place_country_iso, place_country_iso, 1 )
				self.country_region[place_country_iso] = person_region
			person = { "latitude" : rand_lat_deg,
					"longitude" : rand_lon_deg,
					"name" : place_name,
					"country" : place_country,
					"country_iso" : place_country_iso,
					"un_region" : person_region }
			self.regions[ person_region ].add_person_to_region( person )
			self.count_selected_people += 1

	'''	
	def selected_people_min_dist(self):
		# this initialises list with a big number...
		selected_people_min_dist = [1e15]*ca_people.num_points
		for p1_num in range(len(self.selected_people)-1):
			lat1 = math.radians(self.selected_people[p1_num]["latitude"])
			lon1 = math.radians(self.selected_people[p1_num]["longitude"])
			for p2_num in range(p1_num + 1 , len(self.selected_people)):
				lat2 = math.radians(self.selected_people[p2_num]["latitude"])
				lon2 = math.radians(self.selected_people[p2_num]["longitude"])
				distance = math.acos(math.sin(lat1)*math.sin(lat2)+math.cos(lat1)*math.cos(lat2)*math.cos(lon1-lon2))
				# to km
				distance = 1852*distance*180*60/(1000*math.pi)
				#print(p1_num, p2_num, distance)
				if distance < selected_people_min_dist[p1_num]:
					selected_people_min_dist[p1_num] = distance
				if distance < selected_people_min_dist[p2_num]:
					selected_people_min_dist[p2_num] = distance
		self.average_dist = sum(selected_people_min_dist)/ca_people.num_points
		print("Average minimum distance between points = {}".format(self.average_dist))
	'''
		
	def selected_people_print(self):
		# output them for google map input
		# let's randomise the order here!   
		out_file_google = open(google_out_file_name, "w")
		file_output = "latitude, longitude, name, country, country_iso, un_region\n"
		people_array = []
		for region in self.regions.values():
			people_array += region.write_people()
		random.shuffle(people_array)
		file_output += "".join(people_array)
		  #Write to file
		people_array_str = ''.join([str(elem+'___') for elem in people_array])
		file = open("results.txt", "w")
		file.write(people_array_str)
		file.close()

		out_file_google.write( file_output )
		#out_file_google.write("Average minimum distance between points = {}\n".format(self.average_dist))
		# print country and region counts as well...
		out_file_google.write("country_iso, country_max, country_count\n")
		region_summary = ''
		for region in self.regions.values():
			region_summary += region.write_country_summary( out_file_google )
		out_file_google.write( "region_name, region_max, region_count\n" + region_summary )
		out_file_google.close()
	
	def get_person(self, x):
		total_region_count = 0
		for region in self.regions.values():
			if x >= total_region_count and x < total_region_count + region.region_count:
				return region.get_person( x - total_region_count )
			total_region_count += region.region_count
		if debug_print:
			print("Error - got to region list end {}".format(x))
	
	def replace_above_max(self, gca_backups):
		num_deleted = 0
		# for each region delete random people above max
		for region in self.regions.values():
			num_deleted += region.delete_above_max()
		print("Of the initial {} people, {} were from countries or regions above their maximum.".format(self.num_points, num_deleted))
		self.count_selected_people -= num_deleted
		# then replace these deleted from the pool
		#replacements = random.sample(range(ca_people.num_points - num_deleted), num_deleted)
		replacements = list(range(gca_backups.num_points))
		random.shuffle(replacements)
		success_replace = 0
		for x in replacements:
			person = gca_backups.get_person(x)
			is_okay = self.regions[ person["un_region"] ].replacement( person )
			success_replace += is_okay
			if is_okay:
				print("Replaced point {} with a point in {}".format(success_replace, person["country"] ))
			if success_replace == num_deleted:
				break;
		if debug_print:
			print("Successfully replaced {} people".format(success_replace))
			

gca_people = ca_people(total_pop, num_points, True)
if debug_print:
	print("And backup people...")
gca_backups = ca_people(total_pop, 2*num_points, False)

pop_count = 0
print_interval = 10000
print_count = print_interval
print("Going through the database... (USA section)")
for file_name in global_pop_admin_centroids_files:
	if file_name == "gpw_v4_admin_unit_center_points_population_estimates_rev11_global.csv":
		print("Going through the database... (rest of the world)")
		print_interval = 1000000
	else:
		print_interval = 10000
	if debug_print:
		print("Reading in: " + file_name)
	file_handle = open(global_pop_admin_centroids_file_root + file_name, 'r')
	file_reader = csv.DictReader(file_handle)
	for row in file_reader:	
		pop_row = int(row[ "UN_2020_E" ])
		# there might be more than one person we want in here!! the next number could even be the same number...
		gca_people.grab_people_in_admin_area(pop_count, row)
		gca_backups.grab_people_in_admin_area(pop_count, row)
		pop_count += pop_row
		if pop_count > print_count:
			print("Population count: {}".format(pop_count), end="\r")
			print_count += print_interval
	file_handle.close()
print("Population count: {}".format(pop_count), end="\r")
print("\nCheck total population (post selection) = {}".format(total_pop))

# calculate the distance to the closet other point for every point, and sum these minimum distances
#gca_people.selected_people_min_dist()

gca_people.replace_above_max(gca_backups)

gca_people.selected_people_print()

