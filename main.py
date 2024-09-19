#!/bin/python

import json
import time
import sys

from statextractor import *
from characterlistextractor import CharacterListParser
from webgrab.curl import Curl

debug = False

def load_character_list():
	url = "https://www.prydwen.gg/star-rail/characters/"
	curl = Curl()

	cparser = CharacterListParser()

	if(debug):
		curl.curlCall(url, callBack=cparser.feed, abbortIfSaved=True, saveFile=True)
	else:
		curl.curlCall(url, callBack=cparser.feed)

	with open('data/characters.json', 'w') as f:
		json.dump(cparser.characters, f)

def load_relics_per_character():
	data = None
	with open('data/characters.json', 'r') as f:
		data = json.load(f)

	curl = Curl()

	relics = []
	for c in data:
		url = "https://www.prydwen.gg" + data[c]["link"] + "/"
		print(url)
		rparser = HSRRelicParser(c)

		if(debug):
			curl.curlCall(url, callBack=rparser.feed, abbortIfSaved=True, saveFile=True)
		else:
			curl.curlCall(url, callBack=rparser.feed)

		relics.append(rparser.get_relics())

		if(debug):
			break;
			# pass
		# else:
		# timeout to prevent possible ddos prevention
		time.sleep(1)

	with open('data/relics.json', 'w') as f:
		json.dump(relics, f)

def add_stats_to_relic(relic_list, relic_name, stats, character, priority, main_stats):
	if(relic_name is None):
		return

	# create empty dict for new relic names
	if(relic_name not in relic_list):
		relic_list[relic_name] = {"keys":[], "combined":{}, "stats":{}, "main_stats":{}}

	# combine substats and collect all keys
	for k in stats:
		if k not in relic_list[relic_name]["keys"]:
			relic_list[relic_name]["keys"].append(k)

		if k in relic_list[relic_name]["combined"]:
			relic_list[relic_name]["combined"][k] += stats[k]
		else:
			relic_list[relic_name]["combined"][k] = stats[k]

	# individual substats
	relic_list[relic_name]["stats"][character] = {"stats": stats, "priority": priority}

	# main stats
	for part in main_stats:
		# every part (e.g. body/feet/Sphere/rope)
		if part not in relic_list[relic_name]["main_stats"]:
			relic_list[relic_name]["main_stats"][part] = {"keys":[], "combined":{}, "stats":{}}

		# combine main stats and collect all keys
		for k in main_stats[part]:
			if k not in relic_list[relic_name]["main_stats"][part]["keys"]:
				relic_list[relic_name]["main_stats"][part]["keys"].append(k)

			if k in relic_list[relic_name]["main_stats"][part]["combined"]:
				relic_list[relic_name]["main_stats"][part]["combined"][k] += main_stats[part][k]
			else:
				relic_list[relic_name]["main_stats"][part]["combined"][k] = main_stats[part][k]

		# individual main stats
		relic_list[relic_name]["main_stats"][part]["stats"][character] = main_stats[part]




def combine(max_relics, character_list_file, relic_list_file):
	data = None
	characters = None
	with open(relic_list_file, 'r') as f:
		data = json.load(f)
	with open(character_list_file, 'r') as f:
		characters = json.load(f)

	relic_list = {}
	ornament_list = {}

	for c in data:
		if(characters[c["character"]]["filter"] or "substats" not in c["stats"]):
			continue

		for r in c["relic_set"]:
			if(c["relic_set"][r] < max_relics):
				add_stats_to_relic(relic_list, r, c["stats"]["substats"], c["character"], c["relic_set"][r], {"Body":c["stats"]["Body"], "Feet":c["stats"]["Feet"]})


		for r in c["ornament_set"]:
			if(c["ornament_set"][r] < max_relics):
				add_stats_to_relic(ornament_list, r, c["stats"]["substats"], c["character"], c["ornament_set"][r], {"Sphere":c["stats"]["Planar Sphere"], "Rope":c["stats"]["Link Rope"]})
			
	return (relic_list, ornament_list)


def visualize(r_list, sort_num_users):
	relic_list = r_list[0]
	ornament_list = r_list[1]

	if(sort_num_users):
		# sort relic users
		relic_list = {k: v for k,v in sorted(relic_list.items(), key=lambda x: len(x[1]["stats"]), reverse=True)}
		ornament_list = {k: v for k,v in sorted(ornament_list.items(), key=lambda x: len(x[1]["stats"]), reverse=True)}
	else:
		# sort relic name
		relic_list = {k: v for k,v in sorted(relic_list.items())}
		ornament_list = {k: v for k,v in sorted(ornament_list.items())}

	# combine both
	sorted_relics = {**relic_list, **ornament_list}


	# sort stat keys
	for r in sorted_relics:
		sorted_relics[r]["keys"].sort(key=lambda x: sorted_relics[r]["combined"][x], reverse=True)

		# sort characters per relic
		sorted_relics[r]["stats"] = {k:v for k,v in sorted(sorted_relics[r]["stats"].items(), key=lambda x: x[1]["priority"])}


	csv_out = ""
	for r in sorted_relics:
		num_users = len(sorted_relics[r]["stats"])

		csv_out += r + " (" + str(num_users) + ")\tpriority"

		# KEYS substats
		for k in sorted_relics[r]["keys"]:
			csv_out += "\t" + k

		# KEYS main stats
		for part in sorted_relics[r]["main_stats"]:
			csv_out += "\t\t" + part + " (main stat)"
			for k in sorted_relics[r]["main_stats"][part]["keys"]:
				csv_out += "\t" + k

		csv_out += "\n"

		# combined substats
		csv_out += "combined:\t"
		for k in sorted_relics[r]["keys"]:
			if(k in sorted_relics[r]["combined"]):
				# write it out and normalize values to be between 0-1
				csv_out += "\t" + "%.3f" % (sorted_relics[r]["combined"][k] / 1000.0 / num_users)
			else:
				csv_out += "\t"

		# combined main stats
		for part in sorted_relics[r]["main_stats"]:
			csv_out += "\t\t"
			for k in sorted_relics[r]["main_stats"][part]["keys"]:
				if(k in sorted_relics[r]["main_stats"][part]["combined"]):
					# write it out and normalize values to be between 0-1
					csv_out += "\t" + "%.3f" % (sorted_relics[r]["main_stats"][part]["combined"][k] / 1000.0 / num_users)
				else:
					csv_out += "\t"

		csv_out += "\n"

		
		for character in sorted_relics[r]["stats"]:

			# single substats (per character)
			csv_out += character + "\t" + str(sorted_relics[r]["stats"][character]["priority"])
			for k in sorted_relics[r]["keys"]:
				if(k in sorted_relics[r]["stats"][character]["stats"]):
					# write it out and normalize values to be between 0-1
					csv_out += "\t" + "%.3f" % (sorted_relics[r]["stats"][character]["stats"][k] / 1000.0)
				else:
					csv_out += "\t"

			# single main stats (per character)
			for part in sorted_relics[r]["main_stats"]:
				csv_out += "\t\t"
				for k in sorted_relics[r]["main_stats"][part]["keys"]:
					if(k in sorted_relics[r]["main_stats"][part]["stats"][character]):
						# write it out and normalize values to be between 0-1
						csv_out += "\t" + "%.3f" % (sorted_relics[r]["main_stats"][part]["stats"][character][k] / 1000.0)
					else:
						csv_out += "\t"

			csv_out += "\n"
		

		csv_out += "\n"


	with open('data/out.csv','w') as file:
		file.write(csv_out)

def main(renew, relics_per_char, sort_num_users, character_list_file, relic_list_file):
	if(renew):
		load_character_list()
		load_relics_per_character()

	relic_list = combine(relics_per_char, character_list_file, relic_list_file)
	visualize(relic_list, sort_num_users)



if __name__ == '__main__':
	args = sys.argv[1:]

	if "--help" in args:
		print("Usage:")
		print(" python main.py [ARGUMENTS]")
		print()
		print("Arguments:")
		print(" renew\t\t\t\treload data from prydwen")
		print(" num-relics=<NUM>\t\thow many relics per character (default: 1)")
		print(" sort-users\t\t\tsort relic output by number of users (default by relic name)")
		print(" characters=<FILE>\t\tgive a custom character list (e.g. data/characters.custom.json)")
		print(" \t\t\t\tthis can be used to filter out characters you dont want to list")
		print(" \t\t\t\tNOTE: renew doesnt work if you set this")
		print(" relics=<FILE>\t\t\tgive a custom relic list (e.g. data/relics.custom.json)")
		print(" \t\t\t\tthis can be used to order it specificly or remove/add relics")
		print(" \t\t\t\tNOTE: renew doesnt work if you set this")
		print()
		exit()

	# default values
	renew = False
	relics_per_char = 1
	sort_num_users = False
	character_list_file = "data/characters.json"
	relic_list_file = "data/relics.json"

	for arg in args:

		if arg == "renew":
			renew = True
		elif arg.startswith("num-relics"):
			relics_per_char = int(arg[arg.find("=")+1:])
		elif arg.startswith("sort-users"):
			sort_num_users = True
		elif arg.startswith("characters="):
			character_list_file = arg[arg.find("=")+1:]
		elif arg.startswith("relics="):
			relic_list_file = arg[arg.find("=")+1:]

	if(debug):
		renew = True

	main(renew, relics_per_char, sort_num_users, character_list_file, relic_list_file)