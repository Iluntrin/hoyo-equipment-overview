from html.parser import HTMLParser

# keys are stats that appear
# values are stats that we want to show
# e.g. "EFF RES%" will be translated to "Effect RES"
# (this has to be done since prydwen uses inconsistent naming)
sanitized_stats = {
	"CRIT RATE": "CRIT Rate",
	"CRIT RATE%": "CRIT Rate",
	"CRIT Rate%": "CRIT Rate",
	"CRIT Rate": "CRIT Rate",
	"CRIT DMG": "CRIT DMG",
	"CRIT DMG%": "CRIT DMG",
	"SPD": "SPD",
	"Speed": "SPD",
	"ATK%": "ATK%",
	"ATK": "ATK",
	"FLAT ATK": "ATK",
	"HP%": "HP%",
	"HP": "HP",
	"DEF%": "DEF%",
	"DEF": "DEF",
	"Effect RES": "Effect RES%",
	"EFF RES%": "Effect RES%",
	"Effect RES%": "Effect RES%",
	"Effect RES until 30%": "Effect RES%", # I hate that i have to use this...
	"Break Effect%" : "Break Effect%",
	"Break Effect" : "Break Effect%",
	"BREAK EFFECT%" : "Break Effect%",
	"Break Effect %" : "Break Effect%",
	"Energy Regen Rate" : "Energy Regen",
	"Energy Regen" : "Energy Regen",
	"Energy Regen%" : "Energy Regen",
	"Outgoing Healing" : "Outgoing Healing",
	"Outgoing Healing%" : "Outgoing Healing",
	"EHR" : "EHR",
	"EHR%" : "EHR",
	"Effect HIT Rate" : "EHR",
	"Effect Hit Rate" : "EHR",
	"Physical DMG" : "Physical DMG",
	"Fire DMG" : "Fire DMG",
	"Ice DMG" : "Ice DMG",
	"Lightning DMG" : "Lightning DMG",
	"Wind DMG" : "Wind DMG",
	"Quantum DMG" : "Quantum DMG",
	"Imaginary DMG" : "Imaginary DMG",


	# zzz (some are also above)
	"Physical DMG%" : "Physical DMG%",
	"Fire DMG%" : "Fire DMG%",
	"Ice DMG%" : "Ice DMG%",
	"Electric DMG%": "Electric DMG%",
	"Ether DMG%": "Ether DMG%",
	"Impact": "Impact",
	"Pen": "PEN",
	"PEN": "PEN",
	"PEN Ratio%": "PEN Ratio%",
	"Anomaly Mastery": "Anomaly Mastery",
	"Anomaly Proficiency": "Anomaly Proficiency",

}

class EquipmentStats(object):
	def __init__(self, character):
		self.character = character

		self.equipment_set = {}

		self.stats = {}
		self.current_stat_key = ""
		self.current_order = 1000

	def set_equipment(self, name, data):
		name = name.strip()
		if(name == "" or name.startswith("(") or name == "4" or name == "-PC)"): # filter out errors
			return

		if(name not in self.equipment_set): # make sure that equipment doesnt already exist
			self.equipment_set[name] = data
		

	def set_stat_key(self,stat_key):
		# we only want the first stats (from build and teams and not from calculations)
		if(stat_key in self.stats):
			self.current_stat_key = ""
		# Average (sub)stats come from calculations and are not needed
		elif(stat_key in ["Average stats", "Average sub stats"]):
			self.current_stat_key = ""
		else:
			self.current_order = 1000
			self.current_stat_key = stat_key
			self.stats[self.current_stat_key] = {}

	def set_stat(self,stat):
		if(self.current_stat_key == "substats"):
			if(stat == "Substats:" or stat.strip() == ""):
				return

			self.stats[self.current_stat_key] = self.split_substats(stat)

		elif(self.current_stat_key != ""):
			if(stat == "Anything"): # boothill...
				return
			self.stats[self.current_stat_key][self.sanitize_stat(stat)] = self.current_order

	def set_order(self, order):
		if(order == ">="):
			self.current_order -= 1
		elif(order == ">"):
			self.current_order = self.current_order-10
		elif(order == "="):
			pass
		else:
			print("unhandled order: " + order) # shouldnt happen

	def sanitize_stat(self,stat):
		pos = stat.find("(") # remove additional details in brackets
		if(pos != -1):
			stat = stat[0:pos].strip()
		else:
			stat = stat.strip()

		if(stat in sanitized_stats):
			return sanitized_stats[stat]

		print("stat not found: " + stat)
		#shouldnt happen
		return stat

	def split_substats(self,attr):


		parts = {}
		split_positions = self.split_by_order(attr)
		start_pos = 0

		for pos in split_positions:
			parts[self.sanitize_stat(attr[start_pos:pos])] = self.current_order

			# set order of the next element depending on the encountered order sign
			self.set_order(attr[pos:pos+2].strip())

			start_pos = pos + 2

		parts[self.sanitize_stat(attr[start_pos:])] = self.current_order

		return parts

	def split_by_order(self, text):
		# returns the positions where order_chars have been found in a sorted order
		# sorted order: means that if > appears first and then =  -> we would return first the postion of > and then the position of =
		order_chars = [" =", ">=", "> "]
		positions = []

		for o in order_chars:
			pos = 0
			while pos != -1:
				pos = text.find(o, pos)

				if(pos == -1):
					break

				positions.append(pos)

				pos += o.__len__()

		positions.sort()

		return positions


	def get_equipments(self):
		return {
			"character": self.character,
			"equipment_set": self.equipment_set,
			"stats": self.stats
		}

class HSREquipmentParser(HTMLParser):
	def __init__(self, character):
		super().__init__()

		self.parsing_scripts = False

		self.parsing_structure = {
			"stats_header": -1,
			"main_stat": -1,
			"order": -1,
			"substats": -1,
			"set": -1,
			"set_specific": -1,
			"set_ornaments": -1
		}

		self.set_priority = -1
		self.set_2piece = False

		self.tab = -1

		self.stats = EquipmentStats(character)

	def getAttribute(key, attrs):
		for a in attrs:
			if(a[0] == key):
				return a[1]

		return None

	def handle_starttag(self, tag, attrs):

		for key in self.parsing_structure:
			if(self.parsing_structure[key] > 0):
				self.parsing_structure[key] += 1

		if(tag == "script"):
			self.parsing_scripts = True

		if(tag == "div" or tag == "span"):
			html_classes = HSREquipmentParser.getAttribute("class", attrs)

			if(html_classes != None and "tab-inside" in html_classes):
				self.tab += 1

			if(self.tab == 2):
				if(html_classes != None and "stats-header" in html_classes):
					self.parsing_structure["stats_header"] = 1

				if(html_classes != None and "hsr-stat" in html_classes):
					self.parsing_structure["main_stat"] = 1

				if(html_classes != None and "order" in html_classes):
					self.parsing_structure["order"] = 1

				if(html_classes != None and "sub-stats" in html_classes):
					self.parsing_structure["substats"] = 1
					self.stats.set_stat_key("substats")

				if(html_classes != None and "build-relics" in html_classes):
					self.parsing_structure["set"] = 1
					self.set_ornament = False
					self.set_priority = -1 # reset priority

				if(self.parsing_structure["set"] > 0 and html_classes != None and "single-cone" in html_classes):
					self.set_priority += 1

		if(self.tab == 2): # we only want to look at build and teams tab
			if(tag == "button"):
				if(self.parsing_structure["set"] > 0):
					self.parsing_structure["set_specific"] = 1

			if(tag == "h6"):
				if(self.parsing_structure["set"] > 0):
					self.parsing_structure["set_ornaments"] = 1
					self.set_priority = -1 # reset priority


	def handle_endtag(self, tag):
		for key in self.parsing_structure:
			if(self.parsing_structure[key] > 0):
				self.parsing_structure[key] -= 1
		
		if(tag == "script"):
			self.parsing_scripts = False
		
	def handle_data(self, data):
		if(not self.parsing_scripts):
			if(self.parsing_structure["stats_header"] > 0):
				self.stats.set_stat_key(data)
			if(self.parsing_structure["main_stat"] > 0):
				self.stats.set_stat(data)
			if(self.parsing_structure["order"] > 0):
				self.stats.set_order(data)
			if(self.parsing_structure["substats"] > 0):
				self.stats.set_stat(data)
			if(self.parsing_structure["set_specific"] > 0):
				self.stats.set_equipment(data, {"priority": self.set_priority, "ornament": self.set_ornament})
			if(self.parsing_structure["set_ornaments"] > 0 and data == "Best Planetary Sets" or data == "Planetary Sets"):
				self.set_ornament = True


	def get_equipments(self):
		return self.stats.get_equipments()


class ZZZEquipmentParser(HTMLParser):
	def __init__(self, character):
		super().__init__()

		self.parsing_scripts = False

		self.parsing_structure = {
			"main_header": -1,
			"drive_disk": -1,
			"main_stat": -1,
			"order": -1,
			"substats": -1,
			"set_specific": -1,
			"content_header": -1,
			"equipment_info": -1,
			"equipment_info_specific": -1
		}

		self.set_priority = -1
		self.set_2piece = False

		self.parsing_equipment_set = False

		self.correct_tab = False

		self.stats = EquipmentStats(character)

	def getAttribute(key, attrs):
		for a in attrs:
			if(a[0] == key):
				return a[1]

		return None

	def handle_starttag(self, tag, attrs):

		for key in self.parsing_structure:
			if(self.parsing_structure[key] > 0):
				self.parsing_structure[key] += 1

		if(tag == "script"):
			self.parsing_scripts = True

		if(tag == "div" or tag == "span"):
			html_classes = ZZZEquipmentParser.getAttribute("class", attrs)

			if(html_classes != None and "mobile-header" in html_classes):
				self.parsing_structure["main_header"] = 1

			if(self.correct_tab):
				if(html_classes != None and "content-header" in html_classes):
					self.parsing_structure["content_header"] = 1

				if(html_classes != None and "stats-inside" in html_classes):
					self.parsing_structure["drive_disk"] = 1
					# print("a")

				if(html_classes != None and "zzz-stat" in html_classes):
					self.parsing_structure["main_stat"] = 1

				if(html_classes != None and "order" in html_classes):
					self.parsing_structure["order"] = 1

				if(html_classes != None and "sub-stats" in html_classes):
					self.parsing_structure["substats"] = 1
					self.stats.set_stat_key("substats")

				if(self.parsing_equipment_set and html_classes != None and "zzz-weapon-name" in html_classes):
					self.set_priority = int(self.set_priority) + 1 # make sure that it is a whole integer
					self.set_2piece = False
					self.parsing_structure["set_specific"] = 1

				if(self.parsing_equipment_set and html_classes != None and "information" in html_classes):
					self.parsing_structure["equipment_info"] = 1

		if(self.parsing_equipment_set and self.parsing_structure["equipment_info"] > 0 and tag == "ul"):
			# only allow values within ul tag (otherwise <strong> tags in notes section are also falsely parsed)
			self.parsing_structure["equipment_info_specific"] = 1 


		if(self.parsing_equipment_set and self.parsing_structure["equipment_info_specific"] > 0 and tag == "strong"):
			self.set_priority += 0.1 # 2 piece set -> increase in small increment
			self.set_2piece = True
			self.parsing_structure["set_specific"] = 1


	def handle_endtag(self, tag):
		for key in self.parsing_structure:
			if(self.parsing_structure[key] > 0):
				self.parsing_structure[key] -= 1
		
		if(tag == "script"):
			self.parsing_scripts = False
		
	def handle_data(self, data):
		if(self.parsing_structure["main_header"] > 0):
			if("Build and teams" in data):
				self.correct_tab = True
			else:
				self.correct_tab = False

		if(not self.parsing_scripts):
			if(self.parsing_structure["content_header"] > 0):
				if("Best Disk Drives Sets" in data):
					self.parsing_equipment_set = True # we are now parsing drive disks
					self.set_2piece = False
					self.set_priority = -1
				else:
					self.parsing_equipment_set = False

			if(self.parsing_equipment_set):
				if(self.parsing_structure["set_specific"] > 0):
					self.stats.set_equipment(data, {"priority": self.set_priority, "2piece": self.set_2piece})

			if(self.parsing_structure["drive_disk"] > 0):
				self.stats.set_stat_key(data)
			if(self.parsing_structure["main_stat"] > 0):
				self.stats.set_stat(data)
			if(self.parsing_structure["order"] > 0):
				self.stats.set_order(data)
			if(self.parsing_structure["substats"] > 0):
				self.stats.set_stat(data)

	def get_equipments(self):
		return self.stats.get_equipments()


