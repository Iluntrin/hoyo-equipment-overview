#!/bin/python

import json
import time
import sys
import datetime

import xlsxwriter

from statextractor import *
from characterlistextractor import CharacterListParser
from webgrab.curl import Curl

debug = False

config = {
	"renew": False,
	"equipments_per_char": 100,
	"sort_num_users": False,
	"equipment_list_file": "",
	"character_list_file": "",
	"type": "hsr",
	"output": ""
}

def load_character_list():
	url = ""
	if(config["type"] == "hsr"):
		url = "https://www.prydwen.gg/star-rail/characters/"
	elif(config["type"] == "zzz"):
		url = "https://www.prydwen.gg/zenless/characters/"

	curl = Curl()

	parser = CharacterListParser()

	if(debug):
		curl.curlCall(url, callBack=parser.feed, abbortIfSaved=True, saveFile=True)
	else:
		curl.curlCall(url, callBack=parser.feed)

	with open(config["character_list_file"], 'w') as f:
		json.dump(parser.characters, f, indent=2)

def load_equipments_per_character():
	data = None
	with open(config["character_list_file"], 'r') as f:
		data = json.load(f)

	curl = Curl()

	equipments = []
	for c in data:
		url = "https://www.prydwen.gg" + data[c]["link"] + "/"
		print(url)
		parser = None
		if(config["type"] == "hsr"):
			parser = HSREquipmentParser(c)
		elif(config["type"] == "zzz"):
			parser = ZZZEquipmentParser(c)

		if(debug):
			curl.curlCall(url, callBack=parser.feed, abbortIfSaved=True, saveFile=True)
		else:
			curl.curlCall(url, callBack=parser.feed)

		equipments.append(parser.get_equipments())

		if(debug):
			break;
			# pass
		# else:
		# timeout to prevent possible ddos prevention
		time.sleep(1)

	with open(config["equipment_list_file"], 'w') as f:
		json.dump(equipments, f, indent=2)

def add_stats_to_equipment(equipment_list, equipment_name, stats, character, priority, main_stats):
	if(equipment_name is None):
		return

	# create empty dict for new equipment names
	if(equipment_name not in equipment_list):
		equipment_list[equipment_name] = {"keys":[], "combined":{}, "stats":{}, "main_stats":{}}

	# combine substats and collect all keys
	for k in stats:
		if k not in equipment_list[equipment_name]["keys"]:
			equipment_list[equipment_name]["keys"].append(k)

		if k in equipment_list[equipment_name]["combined"]:
			equipment_list[equipment_name]["combined"][k] += stats[k]
		else:
			equipment_list[equipment_name]["combined"][k] = stats[k]

	# individual substats
	equipment_list[equipment_name]["stats"][character] = {"stats": stats, "priority": priority}

	# main stats
	for part in main_stats:
		# every part (e.g. body/feet/Sphere/rope)
		if part not in equipment_list[equipment_name]["main_stats"]:
			equipment_list[equipment_name]["main_stats"][part] = {"keys":[], "combined":{}, "stats":{}}

		# combine main stats and collect all keys
		for k in main_stats[part]:
			if k not in equipment_list[equipment_name]["main_stats"][part]["keys"]:
				equipment_list[equipment_name]["main_stats"][part]["keys"].append(k)

			if k in equipment_list[equipment_name]["main_stats"][part]["combined"]:
				equipment_list[equipment_name]["main_stats"][part]["combined"][k] += main_stats[part][k]
			else:
				equipment_list[equipment_name]["main_stats"][part]["combined"][k] = main_stats[part][k]

		# individual main stats
		equipment_list[equipment_name]["main_stats"][part]["stats"][character] = {"stats": main_stats[part], "priority": priority}




def combine():
	data = None
	characters = None
	with open(config["equipment_list_file"], 'r') as f:
		data = json.load(f)
	with open(config["character_list_file"], 'r') as f:
		characters = json.load(f)

	equipment_list = {}

	for c in data:
		if(characters[c["character"]]["filter"] or "substats" not in c["stats"]):
			continue

		for r in c["equipment_set"]:
			if(c["equipment_set"][r]["priority"] < config["equipments_per_char"] - 0.89): #  - 0.89 to allow 0.1 values (i.e. first 2piece set of zzz)
				main_stats = {}
				if(config["type"] == "hsr"):
					if(c["equipment_set"][r]["ornament"]):
						main_stats = {"Sphere":c["stats"]["Planar Sphere"], "Rope":c["stats"]["Link Rope"]}
					else:
						main_stats = {"Body":c["stats"]["Body"], "Feet":c["stats"]["Feet"]}
				if(config["type"] == "zzz"):
					main_stats = {"Disk 4":c["stats"]["Disk 4"], "Disk 5":c["stats"]["Disk 5"],"Disk 6":c["stats"]["Disk 6"]}

				add_stats_to_equipment(equipment_list, r, c["stats"]["substats"], c["character"], c["equipment_set"][r]["priority"], main_stats)

	return equipment_list

def write_stats(sheet, title, data, formats, row, col):
	num_users = len(data["stats"])
	sheet.write_string(row, 0, title, formats["table_header"])
	sheet.write_string(row, 1, "priority", formats["table_header"])
	col = 2

	# KEYS substats
	for k in data["keys"]:
		sheet.write_string(row, col, k, formats["table_header"])

		# if combined value is 0 -> hide the column
		cell_below = xlsxwriter.utility.xl_rowcol_to_cell(row+1,col)
		sheet.conditional_format(row, col, row, col, {'type': 'formula', 'criteria': cell_below+'=0','format': formats["table_header_hide"]})
		col += 1

	row += 1

	# combined substats
	sheet.write_string(row, 0, "combined", formats["table_side_header"])
	sheet.write_string(row, 1, "", formats["table"])
	col = 2

	visibility_col = len(data["keys"])+2

	for k in data["keys"]:
		if(k in data["combined"]):
			# write it out and normalize values to be between 0-1
			# sheet.write(row, col, (data["combined"][k] / 100.0 / num_users), formats["table_percent"])
			cols = xlsxwriter.utility.xl_range(row+1,col,row+num_users, col)
			visibility_cols = xlsxwriter.utility.xl_range(row+1,visibility_col,row+num_users, visibility_col)
			sheet.write_formula(row, col, "=SUM(" + cols + ")/SUM(" + visibility_cols+")", formats["table_percent"], "")
			
			# hide cell if 0
			sheet.conditional_format(row, col, row, col, {'type': 'cell', 'criteria': '=','value': 0,'format': formats["table_hide"]})

			col += 1
		else:
			sheet.write_string(row, col, "", formats["table"])
			col += 1 # no value in column
	row += 1

	for character in data["stats"]:

		# last column for visibility check
		name_cell = xlsxwriter.utility.xl_rowcol_to_cell(row,0)
		prio_cell = xlsxwriter.utility.xl_rowcol_to_cell(row,1)
		visibility_check_cell = xlsxwriter.utility.xl_rowcol_to_cell(row,visibility_col)
		formula = "=IF(OR(LOOKUP("+name_cell+",characters!A:A,characters!B:B)=-1, LOOKUP("+name_cell+",characters!A:A,characters!B:B)+0.1>="+prio_cell+"),1,0)"
		sheet.write_formula(row,visibility_col, formula, formats["invisible"], "")

		# single substats (per character)
		sheet.write_string(row, 0, character, formats["table_side_header"])
		sheet.write(row, 1, data["stats"][character]["priority"], formats["table_number"])
		col = 2 # start with column index 2
		for k in data["keys"]:
			if(k in data["stats"][character]["stats"]):
				# write it out and normalize values to be between 0-1

				name_cell = xlsxwriter.utility.xl_rowcol_to_cell(row,0)
				prio_cell = xlsxwriter.utility.xl_rowcol_to_cell(row,1)

				value = data["stats"][character]["stats"][k] / 100.0

				# look for name in characters sheet
				# if b column in characters sheet is -1 -> show the value
				# if b column in characters sheet is 0-n -> compare the value from characters sheet with prio
				# if prio-0.1 is below/equal to value in characters sheet -> show value else show 0

				formula = "=IF("+visibility_check_cell+"=1,"+str(value)+",0)"
				sheet.write_formula(row,col, formula, formats["table_percent"], "")

				# hide cell if 0
				sheet.conditional_format(row, col, row, col, {'type': 'cell', 'criteria': '=','value': 0,'format': formats["table_hide"]})

				# sheet.write(row, col, (data["stats"][character]["stats"][k] / 100.0), formats["table_percent"])
				col += 1
			else:
				sheet.write_string(row, col, "", formats["table"])
				col += 1


		
		row += 1


def write_xls(equipment_list):
	with open(config["character_list_file"], 'r') as f:
		characters = json.load(f)

	if(config["sort_num_users"]):
		# sort equipment users
		sorted_equipments = {k: v for k,v in sorted(equipment_list.items(), key=lambda x: len(x[1]["stats"]), reverse=True)}
	else:
		# sort equipment name
		sorted_equipments = {k: v for k,v in sorted(equipment_list.items())}

	# sort stat keys
	for r in sorted_equipments:
		sorted_equipments[r]["keys"].sort(key=lambda x: sorted_equipments[r]["combined"][x], reverse=True)

		# sort characters per equipment
		sorted_equipments[r]["stats"] = {k:v for k,v in sorted(sorted_equipments[r]["stats"].items(), key=lambda x: x[1]["priority"])}


	workbook = xlsxwriter.Workbook(config["output"])
	sheet = workbook.add_worksheet("equipment")
	char_sheet = workbook.add_worksheet("characters")

	formats = {
		"header": workbook.add_format({'bold': True,"font_size": 15}),
		"bold": workbook.add_format({'bold': True}),
		"table_header": workbook.add_format({'bold': True, "bg_color": "#666666","font_color": "#FFFFFF", 'valign': "center", "border": 1}),
		"table_header_hide": workbook.add_format({'bold': True, "bg_color": "#666666","font_color": "#666666", 'valign': "center", "border": 1}),
		"table_side_header": workbook.add_format({'bold': True, "bg_color": "#666666","font_color": "#FFFFFF", "border": 1}),
		"table_percent": workbook.add_format({'num_format': '0.00%',"bg_color": "#cccccc", "border": 1}),
		"table": workbook.add_format({"bg_color": "#cccccc", "border": 1}),
		"table_hide": workbook.add_format({"bg_color": "#cccccc", "font_color": "#cccccc", "border": 1}),
		"table_number": workbook.add_format({"num_format": "0.#", "bg_color": "#cccccc", "border": 1}),
		"invisible": workbook.add_format({ "font_color": "#FFFFFF"})
	}

	row = 0

	sheet.write_string(1, 0, "last update:")
	sheet.write_string(1, 1, datetime.datetime.now().strftime('%Y-%m-%d'))
	sheet.write_string(2, 0, "data source:")
	sheet.merge_range(2, 1, 2, 2, "https://www.prydwen.gg/")
	sheet.write_string(3, 0, "generator:")
	sheet.merge_range(3,1,3,6, "https://github.com/Iluntrin/hoyo-equipment-overview")

	if(config["type"] == "hsr"):


		sheet.merge_range(0, 0, 0, 4, "Honkai Star Rail - Relic Overview", formats["header"])

		explanation = '''
The excel sheet contains multiple table groups. Each table group contains the substats and the main stats of a given relic set. The first data row in each table contains the combined values of each character that uses the set. 

The values are in percentages, with the most important stat being 100%. If a subsequent stat was stated on prydwen to be >= (less or equal) of the previous stat, I subtracted 1% of the previous value. If a subsequent stat was stated to be > (less) important I subtracted 10% from the previous value.

The priority columns start with a priority of 0 (meaning this is the recommended set for the character). This value increases by 1 for each subsequent priority.

You can fine tune which characters you want to show (or how many priorities per character you want to show) on the "characters" tab/sheet. By default all characters have the value -1 next to it. -1 means that the character is shown in every set they can use. By setting this value to -2 you can completely hide this character. By setting the value to 0 only the most recommended sets are shown.(1 shows the 2 most recommended sets and so on). As I don't quite know how google docs works with changes on the sheet you most likely want to download a copy of the sheet to your local computer and change your values there.

Disclaimer: I don't claim that all this data is 100% correct (errors (either by me or by prydwen) can always appear or a future character might use preexisting relics with other stats). Please use your own judgment when trashing relics. I take no responsibility if you trashed a good relic because of the data provided here.
'''

		sheet.insert_textbox(5, 0, explanation, {"width": 1000, "height": 350})

		row = 25

	if(config["type"] == "zzz"):
		sheet.merge_range(0, 0, 0, 4, "Zenless Zone Zero - Drive Disk Overview", formats["header"])
		# empty row

		explanation = '''
The excel sheet contains multiple table groups. Each table group contains the substats and the main stats of a given drive disk set. The first data row in each table contains the combined values of each character that uses the set. 

The values are in percentages, with the most important stat being 100%. If a subsequent stat was stated on prydwen to be >= (less or equal) of the previous stat, I subtracted 1% of the previous value. If a subsequent stat was stated to be > (less) important I subtracted 10% from the previous value.

The priority columns start with a priority of 0 (meaning this is the recommended set for the character). This value increases by 1 for each subsequent priority.2 Piece sets start their priority by 0.1 and increase them by increments of 0.1.

You can fine tune which characters you want to show (or how many priorities per character you want to show) on the "characters" tab/sheet. By default all characters have the value -1 next to it. -1 means that the character is shown in every set they can use. By setting this value to -2 you can completely hide this character. By setting the value to 0 only the most recommended sets are shown.(1 shows the 2 most recommended sets and so on). As I don't quite know how google docs works with changes on the sheet you most likely want to download a copy of the sheet to your local computer and change your values there.

Disclaimer: I don't claim that all this data is 100% correct (errors (either by me or by prydwen) can always appear or a future character might use preexisting drive disks with other stats). Please use your own judgment when trashing drive disks. I take no responsibility if you trashed a good drive disk because of the data provided in the excel sheet.
		'''
		sheet.insert_textbox(5, 0, explanation, {"width": 1000, "height": 380})

		row = 27

	# write the stats
	for r in sorted_equipments:
		num_users = len(sorted_equipments[r]["stats"])

		# equipment name
		sheet.write_string(row, 0, r + " (" + str(num_users) + ")", formats["table_header"])
		row += 1

		# substats
		write_stats(sheet, "substats", sorted_equipments[r], formats, row, 0)
		row += num_users + 3 # # 3 = 1 header, 1 combined, 1 empty row

		# main stats
		for part in  sorted_equipments[r]["main_stats"]:
			write_stats(sheet, part + " (main stat)", sorted_equipments[r]["main_stats"][part], formats, row, 0)
			row += num_users + 3 # # 3 = 1 header, 1 combined, 1 empty row
		
		# rows between sets
		row += 5

	sheet.autofit()


	
	row = 0

	char_sheet.write_string(0, 4, "Explanation:", formats["bold"])
	char_sheet.write_string(1, 4, "-1 show all")
	char_sheet.write_string(2, 4, "-2 do not show anything for character")
	char_sheet.write_string(3, 4, "0 show only priority 0 for character (=show only recommended sets)")
	char_sheet.write_string(4, 4, "<n> show only priority 0 to <n> for character")

	for character in characters:
		char_sheet.write_string(row, 0, character)
		# -1 show all | 0 show only with prio 0 or below, ... 
		# -2 do not show character
		char_sheet.write(row, 1, -1) 
		row+=1

	char_sheet.autofit()


	workbook.close()


def main():
	if(config["renew"]):
		load_character_list()
		load_equipments_per_character()

	equipment_list = combine()
	write_xls(equipment_list)


if __name__ == '__main__':
	args = sys.argv[1:]

	if "--help" in args:
		print("Usage:")
		print(" python main.py [ARGUMENTS]")
		print()
		print("Arguments:")
		print(" type=<TYPE>\t\t\twhat game would you like to extract")
		print(" \t\t\t\toptions: hsr, zzz (default: hsr)")
		print(" renew\t\t\t\treload data from prydwen")
		print(" num-equipments=<NUM>\t\thow many equipments per character (default: 100)")
		print(" sort-users\t\t\tsort equipment output by number of users (default by equipment name)")
		print(" characters=<FILE>\t\tgive a custom character list (e.g. data/characters.custom.json)")
		print(" \t\t\t\tthis can be used to filter out characters you dont want to list")
		print(" \t\t\t\tNOTE: renew doesnt work if you set this")
		print(" \t\t\t\tuse a copy of the characters.json")
		print(" equipments=<FILE>\t\t\tgive a custom equipment list (e.g. data/equipments.custom.json)")
		print(" \t\t\t\tthis can be used to order it specificly or remove/add equipments")
		print(" \t\t\t\tNOTE: renew doesnt work if you set this")
		print(" \t\t\t\tuse a copy of the equipments.json")
		print(" output=<FILE>\t\t\twhere to write the output to")
		print()
		exit()

	# overwrite config with args	
	for arg in args:
		if arg == "hsr":
			config["type"] = "hsr"
		elif arg == "zzz":
			config["type"] = "zzz"
		elif arg == "renew":
			config["renew"] = True
		elif arg.startswith("num-equipments"):
			config["equipments_per_char"] = int(arg[arg.find("=")+1:])
		elif arg.startswith("sort-users"):
			config["sort_num_users"] = True
		elif arg.startswith("characters="):
			config["character_list_file"] = arg[arg.find("=")+1:]
		elif arg.startswith("equipments="):
			config["equipment_list_file"] = arg[arg.find("=")+1:]
		elif arg.startswith("output="):
			config["output"] = arg[arg.find("=")+1:]

	config["type"] = "zzz"

	# set the files depending on type (if custom has not been set)
	if(config["equipment_list_file"] == ""):
		config["character_list_file"] = "data/" + config["type"] + "/characters.json"
	if(config["equipment_list_file"] == ""):
		config["equipment_list_file"] = "data/" + config["type"] + "/equipments.json"
	if(config["output"] == ""):
		config["output"] = "data/" + config["type"] + "/out.xlsx"

	if(debug):
		config["renew"] = True

	main()