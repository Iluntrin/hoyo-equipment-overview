# Equipment Overview

This project parses character and equipment data from https://www.prydwen.gg and transforms this data into an xls file. In this xls file all main and substats that characters need are combined. This means that with only one look into the out.xlsx file you can discern which stats you want to look for.

The parser currently works with data from honkai star rail and zenless zone zero.

Feel free to use/change the software and/or the resulting data as you want.

The program directly creates the finished excel sheet you only need to autoformat the column widths by double clicking on the column divider while selecting the whole sheet. Also the program was created using linux so there might be some small differences when doing this with windows (e.g. I think you have to recreate the env by calling ```python -m venv env``` and then readd the requirements from the requirements.txt by using ```pip install -r requirements.txt```)

## Usage:
In terminal:
```
source env/bin/activate

python main.py [ARGUMENTS]

Arguments:
 type=<TYPE>			what game would you like to extract
 						options: hsr, zzz (default: hsr)
 renew					reload data from prydwen
 num-equipments=<NUM>	how many equipments per character (default: 100)
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

Most likely use cases:
renew prydwen data for hsr/zzz
```
python main.py type=hsr renew
python main.py type=zzz renew
```