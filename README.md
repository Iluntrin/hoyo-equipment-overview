# Equipment Overview

This project parses character and equipment data from https://www.prydwen.gg and transforms this data into a csv file. In this csv file all main and substats that characters need are combined. This means that with only one look into the data/out.csv file you can discern which stats you want to look for.

Feel free to use/change the software and/or the resulting data as you want.

## Usage:
```
python main.py [ARGUMENTS]

Arguments:
 renew					reload data from prydwen
 num-relics=<NUM>		how many relics per character (default: 1)
 sort-users				sort relic output by number of users (default by relic name)
 characters=<FILE>		give a custom character list (e.g. data/characters.custom.json)
 						this can be used to filter out characters you dont want to list
 						NOTE: renew doesnt work if you set this
 relics=<FILE>			give a custom relic list (e.g. data/relics.custom.json)
 						this can be used to order it specificly or remove/add relics
 						NOTE: renew doesnt work if you set this

```