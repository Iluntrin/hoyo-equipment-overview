from html.parser import HTMLParser


class CharacterListParser(HTMLParser):
	def __init__(self):
		super().__init__()

		self.parsing_scripts = False

		self.parsing_structure = {
			"card": -1,
			"name": -1
		}

		self.characters = {}
		self.current_char = {}


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
			html_classes = CharacterListParser.getAttribute("class", attrs)

			if(html_classes != None and "avatar-card" in html_classes):
				self.parsing_structure["card"] = 1
				self.current_char = {"filter": False}

			if(self.parsing_structure["card"] > 0 and html_classes != None and "emp-name" in html_classes):
				self.parsing_structure["name"] = 1

		if(tag == "a"):
			if(self.parsing_structure["card"] > 0):
				link = CharacterListParser.getAttribute("href", attrs)
				self.current_char["link"] = link




	def handle_endtag(self, tag):
		for key in self.parsing_structure:
			if(self.parsing_structure[key] > 0):
				self.parsing_structure[key] -= 1
		
		if(tag == "script"):
			self.parsing_scripts = False
		

	def handle_data(self, data):
		if(not self.parsing_scripts):
			if(self.parsing_structure["name"] > 0):
				self.characters[data.strip()] = self.current_char
			


