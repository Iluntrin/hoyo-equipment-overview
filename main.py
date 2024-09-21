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
	"equipments_per_char": 1,
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
		equipment_list[equipment_name]["main_stats"][part]["stats"][character] = main_stats[part]




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

def write_substats(sheet, name, data, formats, row, col):
	pass
def write_mainstats(sheet, name, data, formats, row, col):
	pass

def write_xls(equipment_list):
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
	sheet = workbook.add_worksheet()

	formats = {
		"header": workbook.add_format({'bold': True,"font_size": 15}),
		"bold": workbook.add_format({'bold': True}),
		"table_header": workbook.add_format({'bold': True, "bg_color": "#666666","font_color": "#FFFFFF", 'valign': "center", "border": 1}),
		"table_side_header": workbook.add_format({'bold': True, "bg_color": "#666666","font_color": "#FFFFFF", "border": 1}),
		"table_percent": workbook.add_format({'num_format': '0.00%',"bg_color": "#cccccc", "border": 1}),
		"table": workbook.add_format({"bg_color": "#cccccc", "border": 1})
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
		# empty row
		sheet.merge_range(5, 0, 5, 12, "Info:", formats["bold"])
		sheet.merge_range(6, 0, 6, 12, "This file lists all possible substats and stats for each individual relic set.")
		sheet.merge_range(7, 0, 7, 12, "The file provides a combined row and rows for each individual character.")
		sheet.merge_range(8, 0, 8, 12, "The values demonstrate how important each individual stat is for the given set (the higher the more important).")
		sheet.merge_range(9, 0, 9, 12, "The priority column shows how important this set is for each individual character (starting from 0).")
		sheet.merge_range(10, 0, 10, 12, "The stats shown in the first columns are the desired substats.")
		sheet.merge_range(11, 0, 11, 12, "The main stats are shown in later columns and start with the piece (e.g. Body (main stat))")
		sheet.merge_range(12, 0, 12, 12, "The number next to the set name shows how many characters are using this set.")
		# empty row
		row = 14

	if(config["type"] == "zzz"):
		sheet.merge_range(0, 0, 0, 4, "Zenless Zone Zero - Drive Disk Overview", formats["header"])
		# empty row
		sheet.merge_range(5, 0, 5, 12, "Info:", formats["bold"])
		sheet.merge_range(6, 0, 6, 12, "This file lists all possible substats and stats for each individual drive disk set.")
		sheet.merge_range(7, 0, 7, 12, "The file provides a combined row and rows for each individual character.")
		sheet.merge_range(8, 0, 8, 12, "The values demonstrate how important each individual stat is for the given set (the higher the more important).")
		sheet.merge_range(9, 0, 9, 12, "The priority column shows how important this set is for each individual character (starting from 0).")
		sheet.merge_range(10, 0, 10, 12, "2 Piece sets start their priority by 0.1 and increase them by increments of 0.1.")
		sheet.merge_range(11, 0, 11, 12, "The stats shown in the first columns are the desired substats.")
		sheet.merge_range(12, 0, 12, 12, "The main stats are shown in later columns and start with the piece (e.g. Drive Disk 4 (main stat))")
		sheet.merge_range(13, 0, 13, 12, "The number next to the set name shows how many characters are using this set.")
		# empty row
		row = 15


	for r in sorted_equipments:
		num_users = len(sorted_equipments[r]["stats"])

		sheet.write_string(row, 0, r + " (" + str(num_users) + ")", formats["table_header"])
		sheet.write_string(row, 1, "priority", formats["table_header"])
		col = 2

		# KEYS substats
		for k in sorted_equipments[r]["keys"]:
			sheet.write_string(row, col, k, formats["table_header"])
			col += 1

		# KEYS main stats
		for part in sorted_equipments[r]["main_stats"]:
			col += 1 # one additional cell

			sheet.write_string(row, col, part + " (main stat)", formats["table_header"])
			col += 1

			for k in sorted_equipments[r]["main_stats"][part]["keys"]:
				sheet.write_string(row, col, k, formats["table_header"])
				col += 1

		row += 1

		# combined substats
		sheet.write_string(row, 0, "combined", formats["table_side_header"])
		sheet.write_string(row, 1, "", formats["table"])

		col = 2 # one column skipped for priority of characters
		for k in sorted_equipments[r]["keys"]:
			if(k in sorted_equipments[r]["combined"]):
				# write it out and normalize values to be between 0-1
				sheet.write(row, col, (sorted_equipments[r]["combined"][k] / 1000.0 / num_users), formats["table_percent"])
				col += 1
			else:
				sheet.write_string(row, col, "", formats["table"])
				col += 1 # no value in column

		# combined main stats
		for part in sorted_equipments[r]["main_stats"]:
			col += 1 # one additional cell
			sheet.write_string(row, col, "combined", formats["table_side_header"]) # repeat combined
			col += 1

			for k in sorted_equipments[r]["main_stats"][part]["keys"]:
				if(k in sorted_equipments[r]["main_stats"][part]["combined"]):
					# write it out and normalize values to be between 0-1
					sheet.write(row, col, (sorted_equipments[r]["main_stats"][part]["combined"][k] / 1000.0 / num_users), formats["table_percent"])
					col += 1
				else:
					sheet.write_string(row, col, "", formats["table"])
					col += 1 # no value in column

		row += 1
		
		for character in sorted_equipments[r]["stats"]:
			# single substats (per character)
			sheet.write_string(row, 0, character, formats["table_side_header"])
			sheet.write_string(row, 1, "%.1g" % sorted_equipments[r]["stats"][character]["priority"], formats["table"])
			col = 2 # start with column index 2
			for k in sorted_equipments[r]["keys"]:
				if(k in sorted_equipments[r]["stats"][character]["stats"]):
					# write it out and normalize values to be between 0-1
					sheet.write(row, col, (sorted_equipments[r]["stats"][character]["stats"][k] / 1000.0), formats["table_percent"])
					col += 1
				else:
					sheet.write_string(row, col, "", formats["table"])
					col += 1

			# single main stats (per character)
			for part in sorted_equipments[r]["main_stats"]:
				col += 1 # one additional cell
				sheet.write_string(row, col, character, formats["table_side_header"]) # repeat character name
				col += 1

				for k in sorted_equipments[r]["main_stats"][part]["keys"]:
					if(k in sorted_equipments[r]["main_stats"][part]["stats"][character]):
						# write it out and normalize values to be between 0-1
						sheet.write(row, col, (sorted_equipments[r]["main_stats"][part]["stats"][character][k] / 1000.0), formats["table_percent"])
						col += 1
					else:
						sheet.write_string(row, col, "", formats["table"])
						col += 1
						
			row += 1
		
		# rows between sets
		row += 5

	sheet.autofit()
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
		print(" num-equipments=<NUM>\t\thow many equipments per character (default: 1)")
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