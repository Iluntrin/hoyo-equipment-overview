# Equipment Overview

This project parses character and equipment data from https://www.prydwen.gg and transforms this data into a csv file. In this csv file all main and substats that characters need are combined. This means that with only one look into the data/out.csv file you can discern which stats you want to look for.

The parser currently works with data from honkai star rail and zenless zone zero

Feel free to use/change the software and/or the resulting data as you want.

## Usage:
In terminal:
```
source env/bin/activate

python main.py [ARGUMENTS]

Arguments:
 type=<TYPE>			what game would you like to extract
 						options: hsr, zzz (default: hsr)
 renew					reload data from prydwen
 num-equipments=<NUM>	how many equipments per character (default: 1)
 sort-users				sort equipment output by number of users (default by equipment name)
 characters=<FILE>		give a custom character list (e.g. data/characters.custom.json)
 						this can be used to filter out characters you dont want to list
 						NOTE: renew doesnt work if you set this
 						use a copy of the characters.json
 equipments=<FILE>		give a custom equipment list (e.g. data/equipments.custom.json)
 						this can be used to order it specificly or remove/add equipments
 						NOTE: renew doesnt work if you set this
 						use a copy of the equipments.json
 output=<FILE>			where to write the output to


```