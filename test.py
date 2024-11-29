from statextractor import *

stats = EquipmentStats("Caesar")

d = "[CRIT RATE = CRIT DMG > ATK% > PEN = ATK] OR [Anomaly Profiency > ATK% > PEN > ATK]"

p = stats.split_substats(d)

print(p)
