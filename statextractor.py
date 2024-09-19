from html.parser import HTMLParser

# keys are stats that appear
# values are stats that we want to show
# e.g. "EFF RES%" will be translated to "Effect RES"
# (this has to be done since prydwen uses inconsistent naming)
sanitized_stats = {
	"CRIT RATE": "CRIT Rate",
	"CRIT RATE%": "CRIT Rate",
	"CRIT Rate": "CRIT Rate",
	"CRIT DMG": "CRIT DMG",
	"CRIT DMG%": "CRIT DMG",
	"SPD": "SPD",
	"Speed": "SPD",
	"ATK%": "ATK%",
	"ATK": "ATK",
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
	"Imaginary DMG" : "Imaginary DMG"
}

class RelicStats(object):
	def __init__(self, character):
		self.character = character
		self.relic_set = {}
		self.ornament_set = {}
		self.set_ornaments = False

		self.attributes = {}
		self.currentStat = ""
		self.current_order = 1000

	def set_set(self, attr, priority):
		attr = attr.strip()
		if(attr == "" or attr.startswith("(")):
			return

		if(self.set_ornaments):
			if(attr not in self.ornament_set): # make sure that relic doesnt already exist
				self.ornament_set[attr] = priority
		else:
			if(attr not in self.relic_set): # make sure that relic doesnt already exist
				self.relic_set[attr] = priority


	def set_stat(self,stat):
		# we only want the first stats (from build and teams and not from calculations)
		if(stat in self.attributes):
			self.currentStat = ""
		# Average (sub)stats come from calculations and are not needed
		elif(stat in ["Average stats", "Average sub stats"]):
			self.currentStat = ""
		else:
			self.current_order = 1000
			self.currentStat = stat
			self.attributes[self.currentStat] = {}

	def set_attr(self,attr):
		if(self.currentStat == "substats"):
			if(attr == "Substats:"):
				return

			self.attributes[self.currentStat] = self.split_substats(attr)

		elif(self.currentStat != ""):
			if(attr == "Anything"): # boothill...
				return
			self.attributes[self.currentStat][self.sanitize_stat(attr)] = self.current_order

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


	def get_relics(self):
		return {
			"character": self.character,
			"relic_set": self.relic_set,
			"ornament_set": self.ornament_set,
			"stats": self.attributes
		}


class HSRRelicParser(HTMLParser):
	def __init__(self, character):
		super().__init__()

		self.parsing_scripts = False

		self.parsing_structure = {
			"stats_header": -1,
			"stat": -1,
			"order": -1,
			"substats": -1,
			"set": -1,
			"set_specific": -1,
			"set_ornaments": -1
		}

		self.set_priority = -1

		self.tab = -1

		self.stats = RelicStats(character)

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
			html_classes = HSRRelicParser.getAttribute("class", attrs)

			if(html_classes != None and "tab-inside" in html_classes):
				self.tab += 1

			if(self.tab == 2):
				if(html_classes != None and "stats-header" in html_classes):
					self.parsing_structure["stats_header"] = 1

				if(html_classes != None and "hsr-stat" in html_classes):
					self.parsing_structure["stat"] = 1

				if(html_classes != None and "order" in html_classes):
					self.parsing_structure["order"] = 1

				if(html_classes != None and "sub-stats" in html_classes):
					self.parsing_structure["substats"] = 1
					self.stats.set_stat("substats")

				if(html_classes != None and "build-relics" in html_classes):
					self.parsing_structure["set"] = 1
					self.stats.set_ornaments = False
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
				self.stats.set_stat(data)
			if(self.parsing_structure["stat"] > 0):
				self.stats.set_attr(data)
			if(self.parsing_structure["order"] > 0):
				self.stats.set_order(data)
			if(self.parsing_structure["substats"] > 0):
				self.stats.set_attr(data)
			if(self.parsing_structure["set_specific"] > 0):
				self.stats.set_set(data, self.set_priority)
			if(self.parsing_structure["set_ornaments"] > 0 and data == "Best Planetary Sets" or data == "Planetary Sets"):
				self.stats.set_ornaments = True


	def get_relics(self):
		return self.stats.get_relics()






	

	
